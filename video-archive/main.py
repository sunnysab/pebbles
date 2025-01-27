import os
import shutil
import subprocess
import argparse
import json
import re
from datetime import timedelta
import time

def get_video_info(input_file: str):
    """获取视频元数据"""
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,r_frame_rate,duration',
        '-of', 'json',
        input_file
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)['streams'][0]
    
    # 解析帧率
    frame_rate = eval(info['r_frame_rate'])
    return {
        'width': int(info['width']),
        'height': int(info['height']),
        'frame_rate': round(frame_rate, 2),
        'duration': float(info['duration'])
    }

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
    
    # 构建基本命令
    cmd = ['ffmpeg', '-i', input_path, '-y']
    
    # 视频处理参数
    video_filters = []
    
    if config.max_resolution:
        if video_info['height'] > config.max_resolution:
            video_filters.append(f'scale=-2:{config.max_resolution}')
    
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
    
    cmd.append(output_path)
    
    # 启动FFmpeg进程
    process = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding='utf-8',
        errors='replace'
    )
    
    # 实时解析进度
    last_progress = 0
    while True:
        if process.poll() is not None:
            break
            
        line = process.stderr.readline()
        if not line:
            continue
            
        # 解析进度
        progress = parse_ffmpeg_progress(line, total_duration)
        if progress and progress_callback:
            # 避免频繁回调，至少间隔1%或1秒
            if (progress - last_progress) > 0.01 or (time.time() - last_progress) > 1:
                progress_callback(progress)
                last_progress = progress
    
    if process.returncode != 0:
        print(f"\n转码失败: {input_path}")
        return False
    return True

class ProgressDisplay:
    """进度显示管理器"""
    def __init__(self, total_files):
        self.total_files = total_files
        self.current_file = 1
        self.start_time = time.time()
    
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
    video_files = []
    for root, _, files in os.walk(config.input_dir):
        for file in files:
            if file.split('.')[-1].lower() in ['mp4', 'mov', 'mkv', 'avi']:
                video_files.append(os.path.join(root, file))
    
    progress = ProgressDisplay(len(video_files))
    
    for input_path in video_files:
        rel_path = os.path.relpath(input_path, config.input_dir)
        output_path = os.path.join(config.output_dir, rel_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        progress.begin_file(input_path)
        
        # 测试转码
        test_output = f'{output_path}-{config.codec}.mp4'
        test_success = transcode_video(
            input_path, test_output, config, 
            test_mode=True,
            progress_callback=lambda p: progress.update(p)
        )
        
        if not test_success:
            progress.end_file()
            continue
        
        # 计算压缩率
        orig_size = os.path.getsize(input_path) * (1/60)
        test_size = os.path.getsize(test_output)
        os.remove(test_output)
        
        if (orig_size - test_size) / orig_size < 0.1:
            print(f"\n跳过：空间节省不足10%")
            
            shutil.move(input_path, output_path)
            progress.end_file()
            continue
        
        # 完整转码
        full_success = transcode_video(
            input_path, output_path, config,
            progress_callback=lambda p: progress.update(p)
        )
        
        progress.end_file()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="视频批量转码工具")
    parser.add_argument('input_dir', help="输入目录")
    parser.add_argument('output_dir', help="输出目录")
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

    args = parser.parse_args()
    
    # 验证FFmpeg可用性
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        print("错误：请先安装FFmpeg并添加到系统路径")
        exit(1)

    process_files(args)
    print("\n全部转码完成！")