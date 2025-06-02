import os
import shutil
import subprocess
import argparse
import json
import re
import tempfile
from datetime import timedelta
import time

def get_video_info(input_file: str):
    """获取视频元数据"""
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
        
        # 解析帧率 - 安全地解析分数格式 (例如 "30/1")
        frame_rate_str = info['r_frame_rate']
        if '/' in frame_rate_str:
            numerator, denominator = frame_rate_str.split('/')
            frame_rate = float(numerator) / float(denominator) if float(denominator) != 0 else 0
        else:
            frame_rate = float(frame_rate_str)
        
        return {
            'width': int(info['width']),
            'height': int(info['height']),
            'frame_rate': round(frame_rate, 2),
            'duration': float(info['duration']),
            'codec_name': info.get('codec_name', 'unknown')
        }
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, ValueError) as e:
        raise ValueError(f"获取视频信息失败: {input_file}, 错误: {e}")


def is_target_codec(codec_name: str) -> bool:
    """检查是否已经是目标编码格式 (AV1 或 H265)"""
    return codec_name.lower() in ['av01', 'hevc', 'h265', 'x265', 'libx265', 'libsvtav1']

def parse_ffmpeg_progress(line, total_duration):
    """解析FFmpeg输出中的进度信息"""
    # 匹配时间格式 00:00:00.00
    time_match = re.search(r'time=(\d{2}:\d{2}:\d{2}\.\d{2})', line)
    if time_match:
        current_time = time_match.group(1)
        # 转换为秒数
        t = time.strptime(current_time.split('.')[0], "%H:%M:%S")
        seconds = t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec
        seconds += float(f"0.{current_time.split('.')[1]}")
        
        if total_duration > 0:
            progress = seconds / total_duration
            return min(progress, 1.0)  # 防止超过100%
    return None

def format_duration(seconds):
    """格式化时间显示"""
    return str(timedelta(seconds=seconds))

def transcode_video(input_path, output_path, config, test_mode=False, progress_callback=None):
    """执行转码操作（带进度回调）"""
    video_info = get_video_info(input_path)
    total_duration = min(video_info['duration'], 60) if test_mode else video_info['duration']
    
    # 检查是否为原地转换（输入和输出路径相同）
    is_in_place = os.path.abspath(input_path) == os.path.abspath(output_path)
    actual_output = output_path
    
    if is_in_place:
        # 原地转换：创建临时文件
        temp_dir = os.path.dirname(output_path)
        temp_fd, temp_path = tempfile.mkstemp(suffix='.tmp.mp4', dir=temp_dir)
        os.close(temp_fd)  # 关闭文件描述符，只使用路径
        actual_output = temp_path
    
    # 构建基本命令
    cmd = ['ffmpeg', '-i', input_path, '-y']
    
    # 视频处理参数
    video_filters = []
    
    if config.max_resolution:
        # 检查视频方向（横向或纵向）
        if video_info['width'] > video_info['height']:
            # 横向视频：限制高度
            if video_info['height'] > config.max_resolution:
                video_filters.append(f'scale=-2:{config.max_resolution}')
        else:
            # 纵向视频：限制宽度
            if video_info['width'] > config.max_resolution:
                video_filters.append(f'scale={config.max_resolution}:-2')
    
    if config.max_framerate and video_info['frame_rate'] > config.max_framerate:
        video_filters.append(f'fps={config.max_framerate}')
    
    if video_filters:
        cmd += ['-vf', ','.join(video_filters)]
    
    if config.codec == 'h265':
        codec_params = [
            '-c:v', 'libx265',
            '-x265-params', f'log-level=error:crf={config.crf}',
        ]
    elif config.codec == 'av1':
        codec_params = [
            '-c:v', 'libsvtav1',
            '-svtav1-params', f'preset={config.preset}',
            '-crf', str(config.crf),
        ]
    else:
        codec_params = ['-c:v', 'copy']
    
    cmd += codec_params
    cmd += ['-c:a', 'copy']
    
    if test_mode:
        cmd += ['-t', '60']
    
    if config.extra_args:
        cmd += config.extra_args
    
    cmd.append(actual_output)
    
    # 启动FFmpeg进程
    process = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding='utf-8',
        errors='replace'
    )
    
    if not process.stderr:
        print(f"\n无法启动FFmpeg进程: {input_path}")
        if is_in_place and os.path.exists(actual_output):
            os.remove(actual_output)
        return False
    
    # 实时解析进度
    last_progress = 0
    last_time = time.time()
    while True:
        if process.poll() is not None:
            break
            
        line = process.stderr.readline()
        if not line:
            continue
            
        # 解析进度
        progress = parse_ffmpeg_progress(line, total_duration)
        if progress and progress_callback:
            current_time = time.time()
            # 避免频繁回调，至少间隔1%或1秒
            if (progress - last_progress) > 0.01 or (current_time - last_time) > 1:
                progress_callback(progress)
                last_progress = progress
                last_time = current_time
    
    if process.returncode != 0:
        print(f"\n转码失败: {input_path}")
        if is_in_place and os.path.exists(actual_output):
            os.remove(actual_output)
        return False
    
    # 如果是原地转换，需要替换原文件
    if is_in_place:
        try:
            # 备份原文件（可选，增加安全性）
            backup_path = f"{input_path}.backup"
            shutil.move(input_path, backup_path)
            
            # 移动临时文件到目标位置
            shutil.move(actual_output, output_path)
            
            # 删除备份文件
            os.remove(backup_path)
            
        except Exception as e:
            print(f"\n原地转换失败: {e}")
            # 恢复备份文件
            if os.path.exists(backup_path):
                shutil.move(backup_path, input_path)
            if os.path.exists(actual_output):
                os.remove(actual_output)
            return False
    
    return True

class ProgressDisplay:
    """进度显示管理器"""
    def __init__(self, total_files):
        self.total_files = total_files
        self.current_file = 1
        self.start_time = time.time()
        self.filename = ""
        self.file_start = 0.0
    
    def begin_file(self, filename):
        """开始处理新文件"""
        self.filename = os.path.basename(filename)
        self.file_start = time.time()
        print(f"\n正在处理 ({self.current_file}/{self.total_files}): {self.filename}")
    
    def update(self, progress):
        """更新当前文件进度"""
        elapsed = time.time() - self.file_start
        percent = progress * 100
        eta = elapsed / progress - elapsed if progress > 0 else 0
        
        # 进度条可视化
        bar_length = 30
        filled = int(round(bar_length * progress))
        bar = '█' * filled + '-' * (bar_length - filled)
        
        print(
            f"\r[{bar}] {percent:.1f}% | 用时: {format_duration(elapsed)} | "
            f"剩余: {format_duration(eta)}", 
            end='', 
            flush=True
        )
    
    def end_file(self):
        """完成当前文件处理"""
        self.current_file += 1
        total_elapsed = time.time() - self.start_time
        print(f"\n完成! 总用时: {format_duration(total_elapsed)}\n")

def process_files(config):
    """处理目录中的所有视频文件"""
    video_extensions = {'.mp4', '.mov', '.mkv', '.avi', '.ts', '.flv'}
    video_files = []
    
    for root, _, files in os.walk(config.input_dir):
        for file in files:
            # 安全地获取文件扩展名
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in video_extensions:
                video_files.append(os.path.join(root, file))
    
    progress = ProgressDisplay(len(video_files))
    
    for input_path in video_files:
        # 获取相对路径并修改扩展名为 mp4
        rel_path = os.path.relpath(input_path, config.input_dir)
        rel_path = os.path.splitext(rel_path)[0] + '.mp4'
        output_path = os.path.join(config.output_dir, rel_path)

        # 检查视频编码格式，如果已经是目标格式则跳过
        try:
            video_info = get_video_info(input_path)
            if is_target_codec(video_info['codec_name']):
                print(f"\n跳过：视频已是 AV1/H265 格式 ({video_info['codec_name']})")
                continue
        except Exception as e:
            print(f"\n无法获取视频信息，跳过: {input_path}, 错误: {e}")
            continue
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        progress.begin_file(input_path)

        if not config.skip_test:
            # 测试转码
            test_output = f'{output_path}-{config.codec}.mp4'
            try:
                # 获取视频信息用于后续计算
                video_info = get_video_info(input_path)
                
                test_success = transcode_video(
                    input_path, test_output, config, 
                    test_mode=True,
                    progress_callback=lambda p: progress.update(p)
                )
            except Exception as e:
                print(f"\n转码失败: {input_path}")
                print(f"错误: {e}")
                progress.end_file()
                shutil.move(input_path, output_path)
                continue
            
            if not test_success:
                progress.end_file()
                continue
            
            # 计算压缩率
            orig_size = os.path.getsize(input_path)
            test_size = os.path.getsize(test_output)
            
            # 按测试时长估算完整文件转码后的大小
            test_duration = min(video_info['duration'], 60)
            estimated_full_size = test_size * (video_info['duration'] / test_duration)
            
            # 计算节省的空间比例
            space_saved_ratio = (orig_size - estimated_full_size) / orig_size
            os.remove(test_output)
            
            if space_saved_ratio < 0.1:
                print(f"\n跳过：空间节省不足10% (估算节省 {space_saved_ratio:.1%})")
                
                shutil.move(input_path, output_path)
                progress.end_file()
                continue
        
        # 完整转码
        try:
            full_success = transcode_video(
                input_path, output_path, config,
                progress_callback=lambda p: progress.update(p)
            )
            
            if not full_success:
                print(f"\n完整转码失败: {input_path}")
                # 如果转码失败，删除可能的不完整输出文件
                if os.path.exists(output_path):
                    os.remove(output_path)
        except Exception as e:
            print(f"\n完整转码出错: {input_path}")
            print(f"错误: {e}")
            # 清理不完整的输出文件
            if os.path.exists(output_path):
                os.remove(output_path)
        
        progress.end_file()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="视频批量转码工具")
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

    args = parser.parse_args()
    
    # 如果未提供输出目录，使用输入目录（原地转换）
    if args.output_dir is None:
        args.output_dir = args.input_dir
        print("未指定输出目录，将进行原地转换")
    
    # 验证FFmpeg可用性
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        print("错误：请先安装FFmpeg并添加到系统路径")
        exit(1)

    process_files(args)
    print("\n全部转码完成！")