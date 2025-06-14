#!/usr/bin/env python3
"""
脚本：提取单文件目录中的文件
功能：遍历指定目录及其子目录，如果某个目录只包含一个文件，则将该文件移动到其父目录中
作者：自动生成
"""

import os
import sys
import shutil
from pathlib import Path


def find_single_file_directories(root_path):
    """
    查找只包含单个文件的目录
    
    Args:
        root_path: 根目录路径
        
    Returns:
        list: 包含 (目录路径, 文件路径) 元组的列表
    """
    single_file_dirs = []
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # 跳过根目录本身
        if dirpath == root_path:
            continue
            
        # 检查当前目录是否只包含一个文件且没有子目录
        if len(filenames) == 1 and len(dirnames) == 0:
            file_path = os.path.join(dirpath, filenames[0])
            single_file_dirs.append((dirpath, file_path))
    
    return single_file_dirs


def move_files(operations):
    """
    执行文件移动操作
    
    Args:
        operations: 包含 (源目录, 文件路径) 元组的列表
    """
    moved_count = 0
    
    for dir_path, file_path in operations:
        try:
            # 获取文件名
            filename = os.path.basename(file_path)
            
            # 目标路径是源目录的父目录
            parent_dir = os.path.dirname(dir_path)
            target_path = os.path.join(parent_dir, filename)
            
            # 检查目标文件是否已存在
            if os.path.exists(target_path):
                print(f"警告：目标文件已存在，跳过: {target_path}")
                continue
            
            # 移动文件
            shutil.move(file_path, target_path)
            print(f"✓ 移动: {file_path} -> {target_path}")
            
            # 删除空目录
            try:
                os.rmdir(dir_path)
                print(f"✓ 删除空目录: {dir_path}")
            except OSError as e:
                print(f"警告：无法删除目录 {dir_path}: {e}")
            
            moved_count += 1
            
        except Exception as e:
            print(f"错误：移动文件 {file_path} 时出错: {e}")
    
    return moved_count


def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) != 2:
        print("用法: python extract-single-files.py <目录路径>")
        print("示例: python extract-single-files.py /path/to/directory")
        sys.exit(1)
    
    root_directory = sys.argv[1]
    
    # 检查目录是否存在
    if not os.path.exists(root_directory):
        print(f"错误：目录不存在: {root_directory}")
        sys.exit(1)
    
    if not os.path.isdir(root_directory):
        print(f"错误：路径不是目录: {root_directory}")
        sys.exit(1)
    
    print(f"正在扫描目录: {root_directory}")
    print("查找只包含单个文件的子目录...")
    
    # 查找只包含单个文件的目录
    single_file_dirs = find_single_file_directories(root_directory)
    
    if not single_file_dirs:
        print("未找到只包含单个文件的子目录。")
        return
    
    print(f"\n找到 {len(single_file_dirs)} 个只包含单个文件的目录:")
    print("-" * 60)
    
    for i, (dir_path, file_path) in enumerate(single_file_dirs, 1):
        filename = os.path.basename(file_path)
        parent_dir = os.path.dirname(dir_path)
        target_path = os.path.join(parent_dir, filename)
        
        print(f"{i:2d}. 目录: {dir_path}")
        print(f"    文件: {filename}")
        print(f"    将移动到: {target_path}")
        
        # 检查目标文件是否已存在
        if os.path.exists(target_path):
            print(f"    ⚠️  警告：目标位置已存在同名文件！")
        print()
    
    # 用户确认
    print("-" * 60)
    try:
        confirm = input("确认执行上述操作吗？(y/N): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("操作已取消。")
            return
    except KeyboardInterrupt:
        print("\n操作已取消。")
        return
    
    print("\n开始执行文件移动操作...")
    print("-" * 60)
    
    # 执行移动操作
    moved_count = move_files(single_file_dirs)
    
    print("-" * 60)
    print(f"操作完成！成功移动了 {moved_count} 个文件。")


if __name__ == "__main__":
    main()
