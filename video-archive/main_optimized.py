#!/usr/bin/env python3
"""
视频批量转码工具 - 优化版本

主要优化：
1. 使用dataclasses和类型提示提高代码可读性
2. 提取常量和配置
3. 分离职责，使代码更模块化
4. 改进错误处理和日志记录
5. 使用上下文管理器确保资源清理
6. 简化逻辑流程
"""

import os
import shutil
import subprocess
import argparse
import json
import re
import tempfile
import logging
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any
import time

# 常量配置
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.mkv', '.avi', '.ts', '.flv', '.webm'}
DEFAULT_TEST_DURATION = 60
PROGRESS_UPDATE_THRESHOLD = 0.01  # 1%
PROGRESS_TIME_THRESHOLD = 1.0     # 1秒
MIN_SPACE_SAVING_RATIO = 0.1      # 10%

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    """视频信息数据类"""
    width: int
    height: int
    frame_rate: float
    duration: float
    codec_name: str

    @property
    def is_landscape(self) -> bool:
        """是否为横向视频"""
        return self.width > self.height
    
    @property
    def is_target_codec(self) -> bool:
        """是否已经是目标编码格式 (AV1 或 H265)"""
        return self.codec_name.lower() in ['av01', 'hevc', 'h265', 'x265', 'libx265', 'libsvtav1']


@dataclass
class TranscodeConfig:
    """转码配置数据类"""
    codec: str
    max_resolution: Optional[int] = None
    max_framerate: Optional[float] = None
    crf: int = 28
    preset: int = 10
    extra_args: Optional[List[str]] = None
    skip_test: bool = False
    input_dir: str = ""
    output_dir: str = ""

    def get_codec_params(self) -> List[str]:
        """获取编码器参数"""
        if self.codec == 'h265':
            return [
                '-c:v', 'libx265',
                '-x265-params', f'log-level=error:crf={self.crf}',
            ]
        elif self.codec == 'av1':
            return [
                '-c:v', 'libsvtav1',
                '-svtav1-params', f'preset={self.preset}',
                '-crf', str(self.crf),
            ]
        else:
            return ['-c:v', 'copy']


class VideoInfoExtractor:
    """视频信息提取器"""
    
    @staticmethod
    def extract(input_file: str) -> VideoInfo:
        """提取视频元数据"""
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,r_frame_rate,duration,codec_name',
            '-of', 'json',
            input_file
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            if not data.get('streams'):
                raise ValueError(f"无法获取视频流信息: {input_file}")
            
            info = data['streams'][0]
            frame_rate = VideoInfoExtractor._parse_frame_rate(info['r_frame_rate'])
            
            return VideoInfo(
                width=int(info['width']),
                height=int(info['height']),
                frame_rate=round(frame_rate, 2),
                duration=float(info['duration']),
                codec_name=info.get('codec_name', 'unknown')
            )
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"获取视频信息失败: {input_file}, 错误: {e}")
    
    @staticmethod
    def _parse_frame_rate(frame_rate_str: str) -> float:
        """安全地解析帧率"""
        if '/' in frame_rate_str:
            numerator, denominator = frame_rate_str.split('/')
            return float(numerator) / float(denominator) if float(denominator) != 0 else 0
        return float(frame_rate_str)


class FFmpegProgressParser:
    """FFmpeg进度解析器"""
    
    TIME_PATTERN = re.compile(r'time=(\d{2}:\d{2}:\d{2}\.\d{2})')
    
    @classmethod
    def parse_progress(cls, line: str, total_duration: float) -> Optional[float]:
        """解析FFmpeg输出中的进度信息"""
        match = cls.TIME_PATTERN.search(line)
        if not match:
            return None
        
        current_time = match.group(1)
        seconds = cls._time_str_to_seconds(current_time)
        
        if total_duration > 0:
            progress = seconds / total_duration
            return min(progress, 1.0)  # 防止超过100%
        return None
    
    @staticmethod
    def _time_str_to_seconds(time_str: str) -> float:
        """将时间字符串转换为秒数"""
        time_part, ms_part = time_str.split('.')
        t = time.strptime(time_part, "%H:%M:%S")
        seconds = t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec
        seconds += float(f"0.{ms_part}")
        return seconds


class ProgressDisplay:
    """进度显示管理器"""
    
    def __init__(self, total_files: int):
        self.total_files = total_files
        self.current_file = 1
        self.start_time = time.time()
        self.filename = ""
        self.file_start = 0.0
    
    def begin_file(self, filename: str) -> None:
        """开始处理新文件"""
        self.filename = Path(filename).name
        self.file_start = time.time()
        logger.info(f"正在处理 ({self.current_file}/{self.total_files}): {self.filename}")
    
    def update_progress(self, progress: float) -> None:
        """更新当前文件进度"""
        elapsed = time.time() - self.file_start
        percent = progress * 100
        eta = (elapsed / progress - elapsed) if progress > 0 else 0
        
        # 进度条可视化
        bar = self._create_progress_bar(progress)
        
        print(
            f"\r{bar} {percent:.1f}% | 用时: {self._format_duration(elapsed)} | "
            f"剩余: {self._format_duration(eta)}", 
            end='', 
            flush=True
        )
    
    def end_file(self) -> None:
        """完成当前文件处理"""
        self.current_file += 1
        total_elapsed = time.time() - self.start_time
        logger.info(f"完成! 总用时: {self._format_duration(total_elapsed)}")
    
    @staticmethod
    def _create_progress_bar(progress: float, length: int = 30) -> str:
        """创建进度条"""
        filled = int(round(length * progress))
        return f"[{'█' * filled}{'-' * (length - filled)}]"
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化时间显示"""
        return str(timedelta(seconds=int(seconds)))


class VideoTranscoder:
    """视频转码器"""
    
    def __init__(self, config: TranscodeConfig):
        self.config = config
    
    def transcode(self, input_path: str, output_path: str, 
                  test_mode: bool = False, 
                  progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """执行转码操作"""
        try:
            video_info = VideoInfoExtractor.extract(input_path)
            total_duration = (min(video_info.duration, DEFAULT_TEST_DURATION) 
                            if test_mode else video_info.duration)
            
            with TempFileManager(input_path, output_path) as temp_manager:
                actual_output = temp_manager.get_output_path()
                
                cmd = self._build_ffmpeg_command(input_path, actual_output, video_info, test_mode)
                
                success = self._execute_ffmpeg(cmd, total_duration, progress_callback)
                
                if success and temp_manager.is_in_place:
                    temp_manager.finalize()
                
                return success
                
        except Exception as e:
            logger.error(f"转码失败: {input_path}, 错误: {e}")
            return False
    
    def _build_ffmpeg_command(self, input_path: str, output_path: str, 
                             video_info: VideoInfo, test_mode: bool) -> List[str]:
        """构建FFmpeg命令"""
        cmd = ['ffmpeg', '-i', input_path, '-y']
        
        # 视频过滤器
        video_filters = self._build_video_filters(video_info)
        if video_filters:
            cmd.extend(['-vf', ','.join(video_filters)])
        
        # 编码参数
        cmd.extend(self.config.get_codec_params())
        cmd.extend(['-c:a', 'copy'])
        
        # 测试模式限制时长
        if test_mode:
            cmd.extend(['-t', str(DEFAULT_TEST_DURATION)])
        
        # 额外参数
        if self.config.extra_args:
            cmd.extend(self.config.extra_args)
        
        cmd.append(output_path)
        return cmd
    
    def _build_video_filters(self, video_info: VideoInfo) -> List[str]:
        """构建视频过滤器"""
        filters = []
        
        # 分辨率限制
        if self.config.max_resolution:
            if video_info.is_landscape:
                if video_info.height > self.config.max_resolution:
                    filters.append(f'scale=-2:{self.config.max_resolution}')
            else:
                if video_info.width > self.config.max_resolution:
                    filters.append(f'scale={self.config.max_resolution}:-2')
        
        # 帧率限制
        if (self.config.max_framerate and 
            video_info.frame_rate > self.config.max_framerate):
            filters.append(f'fps={self.config.max_framerate}')
        
        return filters
    
    def _execute_ffmpeg(self, cmd: List[str], total_duration: float,
                       progress_callback: Optional[Callable[[float], None]]) -> bool:
        """执行FFmpeg命令"""
        process = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if not process.stderr:
            logger.error("无法启动FFmpeg进程")
            return False
        
        self._monitor_progress(process, total_duration, progress_callback)
        return process.returncode == 0
    
    def _monitor_progress(self, process: subprocess.Popen, total_duration: float,
                         progress_callback: Optional[Callable[[float], None]]) -> None:
        """监控转码进度"""
        last_progress = 0
        last_time = time.time()
        
        if not process.stderr:
            return
            
        while process.poll() is None:
            line = process.stderr.readline()
            if not line:
                continue
            
            progress = FFmpegProgressParser.parse_progress(line, total_duration)
            if progress and progress_callback:
                current_time = time.time()
                if (progress - last_progress > PROGRESS_UPDATE_THRESHOLD or 
                    current_time - last_time > PROGRESS_TIME_THRESHOLD):
                    progress_callback(progress)
                    last_progress = progress
                    last_time = current_time


class TempFileManager:
    """临时文件管理器"""
    
    def __init__(self, input_path: str, output_path: str):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.is_in_place = self.input_path.resolve() == self.output_path.resolve()
        self.temp_path: Optional[Path] = None
        self.backup_path: Optional[Path] = None
    
    def __enter__(self):
        if self.is_in_place:
            temp_fd, temp_path_str = tempfile.mkstemp(
                suffix='.tmp.mp4', 
                dir=self.output_path.parent
            )
            os.close(temp_fd)
            self.temp_path = Path(temp_path_str)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_path and self.temp_path.exists():
            self.temp_path.unlink()
        if self.backup_path and self.backup_path.exists():
            self.backup_path.unlink()
    
    def get_output_path(self) -> str:
        """获取实际输出路径"""
        return str(self.temp_path if self.is_in_place else self.output_path)
    
    def finalize(self) -> None:
        """完成原地转换"""
        if not self.is_in_place or not self.temp_path:
            return
        
        self.backup_path = self.input_path.with_suffix('.backup')
        
        try:
            # 备份原文件
            shutil.move(str(self.input_path), str(self.backup_path))
            # 移动临时文件到目标位置
            shutil.move(str(self.temp_path), str(self.output_path))
            # 删除备份
            self.backup_path.unlink()
            self.backup_path = None
        except Exception as e:
            # 恢复备份文件
            if self.backup_path and self.backup_path.exists():
                shutil.move(str(self.backup_path), str(self.input_path))
            raise e


class CompressionAnalyzer:
    """压缩分析器"""
    
    @staticmethod
    def calculate_space_saving_ratio(original_size: int, test_size: int, 
                                   test_duration: float, total_duration: float) -> float:
        """计算空间节省比例"""
        estimated_full_size = test_size * (total_duration / test_duration)
        return (original_size - estimated_full_size) / original_size
    
    @staticmethod
    def is_worth_transcoding(space_saving_ratio: float) -> bool:
        """判断是否值得转码"""
        return space_saving_ratio >= MIN_SPACE_SAVING_RATIO


class VideoProcessor:
    """视频处理器 - 主要业务逻辑"""
    
    def __init__(self, config: TranscodeConfig):
        self.config = config
        self.transcoder = VideoTranscoder(config)
    
    def process_files(self) -> None:
        """处理目录中的所有视频文件"""
        video_files = self._find_video_files()
        
        if not video_files:
            logger.info("未找到视频文件")
            return
        
        progress_display = ProgressDisplay(len(video_files))
        
        for input_path in video_files:
            output_path = self._get_output_path(input_path)
            
            # 检查视频编码格式，如果已经是目标格式则跳过
            try:
                video_info = VideoInfoExtractor.extract(str(input_path))
                if video_info.is_target_codec:
                    logger.info(f"跳过：视频已是 AV1/H265 格式 ({video_info.codec_name}) - {input_path}")
                    continue
            except Exception as e:
                logger.error(f"无法获取视频信息，跳过: {input_path}, 错误: {e}")
                continue
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            progress_display.begin_file(str(input_path))
            
            try:
                if self._process_single_file(input_path, output_path, progress_display):
                    logger.info(f"成功处理: {input_path}")
                else:
                    logger.warning(f"处理失败: {input_path}")
            except Exception as e:
                logger.error(f"处理出错: {input_path}, 错误: {e}")
                self._cleanup_failed_output(output_path)
            
            progress_display.end_file()
    
    def _find_video_files(self) -> List[Path]:
        """查找视频文件"""
        video_files = []
        input_dir = Path(self.config.input_dir)
        
        for file_path in input_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in VIDEO_EXTENSIONS:
                video_files.append(file_path)
        
        return sorted(video_files)
    
    def _get_output_path(self, input_path: Path) -> Path:
        """获取输出文件路径"""
        rel_path = input_path.relative_to(self.config.input_dir)
        output_path = Path(self.config.output_dir) / rel_path.with_suffix('.mp4')
        return output_path
    
    def _process_single_file(self, input_path: Path, output_path: Path,
                           progress_display: ProgressDisplay) -> bool:
        """处理单个文件"""
        # 测试转码
        if not self.config.skip_test:
            if not self._test_transcode(input_path, output_path, progress_display):
                return False
        
        # 完整转码
        return self.transcoder.transcode(
            str(input_path), str(output_path),
            progress_callback=progress_display.update_progress
        )
    
    def _test_transcode(self, input_path: Path, output_path: Path,
                       progress_display: ProgressDisplay) -> bool:
        """测试转码"""
        test_output = output_path.with_suffix(f'.{self.config.codec}.test.mp4')
        
        try:
            video_info = VideoInfoExtractor.extract(str(input_path))
            
            success = self.transcoder.transcode(
                str(input_path), str(test_output),
                test_mode=True,
                progress_callback=progress_display.update_progress
            )
            
            if not success:
                return False
            
            # 分析压缩效果
            if not self._analyze_compression(input_path, test_output, video_info):
                # 如果压缩效果不佳，直接移动原文件
                shutil.move(str(input_path), str(output_path))
                return True  # 视为成功，因为文件已处理
            
            return True
            
        finally:
            if test_output.exists():
                test_output.unlink()
    
    def _analyze_compression(self, input_path: Path, test_output: Path, 
                           video_info: VideoInfo) -> bool:
        """分析压缩效果"""
        original_size = input_path.stat().st_size
        test_size = test_output.stat().st_size
        test_duration = min(video_info.duration, DEFAULT_TEST_DURATION)
        
        space_saving_ratio = CompressionAnalyzer.calculate_space_saving_ratio(
            original_size, test_size, test_duration, video_info.duration
        )
        
        if CompressionAnalyzer.is_worth_transcoding(space_saving_ratio):
            logger.info(f"预估空间节省: {space_saving_ratio:.1%}")
            return True
        else:
            logger.info(f"跳过：空间节省不足10% (估算节省 {space_saving_ratio:.1%})")
            return False
    
    @staticmethod
    def _cleanup_failed_output(output_path: Path) -> None:
        """清理失败的输出文件"""
        if output_path.exists():
            output_path.unlink()


def check_dependencies() -> None:
    """检查依赖项"""
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['ffprobe', '-version'], check=True,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        logger.error("错误：请先安装FFmpeg并添加到系统路径")
        exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="视频批量转码工具 - 优化版")
    parser.add_argument('input_dir', help="输入目录")
    parser.add_argument('output_dir', nargs='?', default=None,
                       help="输出目录（可选，默认为输入目录，即原地转换）")
    parser.add_argument('--codec', choices=['h265', 'av1'], required=True,
                       help="目标编码格式")
    parser.add_argument('--max_resolution', type=int,
                       help="最大垂直分辨率（例如 1080）")
    parser.add_argument('--max_framerate', type=float, default=24,
                       help="最大帧率")
    parser.add_argument('--crf', type=int, default=28,
                       help="视频质量（CRF值，默认28）")
    parser.add_argument('--preset', type=int, default=10,
                       help="编码速度预设（1-13，值越大速度越快质量越低）")
    parser.add_argument('--extra_args', nargs=argparse.REMAINDER,
                       help="额外的FFmpeg参数")
    parser.add_argument('--skip_test', action='store_true',
                       help="跳过测试转码步骤")
    parser.add_argument('--verbose', '-v', action='store_true',
                       help="详细输出模式")

    args = parser.parse_args()
    
    # 如果未提供输出目录，使用输入目录（原地转换）
    if args.output_dir is None:
        args.output_dir = args.input_dir
        logger.info("未指定输出目录，将进行原地转换")
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 验证依赖
    check_dependencies()
    
    # 创建配置
    config = TranscodeConfig(
        codec=args.codec,
        max_resolution=args.max_resolution,
        max_framerate=args.max_framerate,
        crf=args.crf,
        preset=args.preset,
        extra_args=args.extra_args,
        skip_test=args.skip_test,
        input_dir=args.input_dir,
        output_dir=args.output_dir
    )
    
    # 处理文件
    processor = VideoProcessor(config)
    processor.process_files()
    
    logger.info("全部转码完成！")


if __name__ == "__main__":
    main()
