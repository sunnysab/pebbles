#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名清理脚本
功能：
1. 删除文件名开头和结尾的空格
2. 删除文件名开头的emoji
3. 将文件名中的emoji转换为空格
4. 规范化多个连续空格为单个空格
5. 删除文件尾部的特定字符串（如 (z-lib.org)）
6. 支持自定义清理规则的扩展

用法：python3 sanitize-filename.py <目录路径>
"""

import os
import sys
import re
import unicodedata
from pathlib import Path
from typing import List, Tuple


class FilenameSanitizer:
    """文件名清理器类，提供可扩展的文件名清理功能"""
    
    def __init__(self):
        # 定义需要删除的文件尾部字符串列表，支持扩展
        self.tail_patterns_to_remove = [
            r'\(z-lib\.org\)',           # (z-lib.org)
            r'\[z-lib\.org\]',           # [z-lib.org]
            r'\(zlibrary\.org\)',        # (zlibrary.org)
            r'\[zlibrary\.org\]',        # [zlibrary.org]
            r'\(pdfdrive\.com\)',        # (pdfdrive.com)
            r'\[pdfdrive\.com\]',        # [pdfdrive.com]
            r'\(Z-Library\)',            # (Z-Library)
        ]
        
        # 编译正则表达式，提高性能
        self.tail_regex = re.compile(
            '|'.join(self.tail_patterns_to_remove) + r'$',
            re.IGNORECASE
        )
        
        # 用于匹配多个连续空格的正则表达式
        self.multiple_spaces_regex = re.compile(r'\s+')
    
    def is_emoji(self, char: str) -> bool:
        """
        判断字符是否为emoji
        使用Unicode分类来识别emoji字符
        """
        # 检查是否为emoji相关的Unicode分类
        category = unicodedata.category(char)
        
        # Symbol, other (So) - 包含大多数emoji
        if category == 'So':
            return True
            
        # 检查是否在emoji Unicode范围内
        code_point = ord(char)
        
        # 常见的emoji Unicode范围
        emoji_ranges = [
            (0x1F600, 0x1F64F),  # 表情符号
            (0x1F300, 0x1F5FF),  # 杂项符号和象形文字
            (0x1F680, 0x1F6FF),  # 交通和地图符号
            (0x1F1E0, 0x1F1FF),  # 区域指示符号
            (0x2600, 0x26FF),    # 杂项符号
            (0x2700, 0x27BF),    # 装饰符号
            (0xFE00, 0xFE0F),    # 变体选择器
            (0x1F900, 0x1F9FF),  # 补充符号和象形文字
            (0x1F018, 0x1F270),  # 各种符号
        ]
        
        return any(start <= code_point <= end for start, end in emoji_ranges)
    
    def remove_leading_emojis(self, filename: str) -> str:
        """
        删除文件名开头的emoji字符
        """
        result = ''
        emoji_section_ended = False
        
        for char in filename:
            if not emoji_section_ended and self.is_emoji(char):
                # 跳过开头的emoji
                continue
            else:
                # 遇到第一个非emoji字符，标记emoji部分结束
                emoji_section_ended = True
                result += char
        
        return result
    
    def replace_emojis_with_space(self, filename: str) -> str:
        """
        将文件名中的emoji替换为空格
        """
        result = ''
        for char in filename:
            if self.is_emoji(char):
                result += ' '
            else:
                result += char
        return result
    
    def normalize_spaces(self, filename: str) -> str:
        """
        将多个连续空格规范化为单个空格，并去除首尾空格
        """
        # 替换多个连续空格为单个空格
        normalized = self.multiple_spaces_regex.sub(' ', filename)
        # 去除首尾空格
        return normalized.strip()
    
    def remove_tail_patterns(self, filename: str) -> str:
        """
        删除文件尾部的特定字符串模式
        """
        return self.tail_regex.sub('', filename).strip()
    
    def sanitize_filename(self, filename: str) -> str:
        """
        完整的文件名清理流程
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # 分离文件名和扩展名
        name, ext = os.path.splitext(filename)
        
        # 步骤0: 去除原始文件名的首尾空格
        name = name.strip()
        
        # 步骤1: 删除开头的emoji
        name = self.remove_leading_emojis(name)
        
        # 步骤2: 将emoji转换为空格
        name = self.replace_emojis_with_space(name)
        
        # 步骤3: 规范化空格
        name = self.normalize_spaces(name)
        
        # 步骤4: 删除尾部特定字符串
        name = self.remove_tail_patterns(name)
        
        # 步骤5: 最终空格清理
        name = self.normalize_spaces(name)
        
        # 如果处理后文件名为空，使用默认名称
        if not name:
            name = 'unnamed_file'
        
        return name + ext
    
    def add_tail_pattern(self, pattern: str):
        """
        添加新的尾部删除模式（扩展功能）
        
        Args:
            pattern: 正则表达式模式
        """
        self.tail_patterns_to_remove.append(pattern)
        # 重新编译正则表达式
        self.tail_regex = re.compile(
            '|'.join(self.tail_patterns_to_remove) + r'$',
            re.IGNORECASE
        )


def collect_all_items(directory_path: str, recursive: bool = True) -> List[Tuple[Path, str, bool]]:
    """
    收集目录中所有需要处理的项目（文件和目录）
    
    Args:
        directory_path: 目录路径
        recursive: 是否递归处理子目录
        
    Returns:
        项目列表 [(路径对象, 相对路径, 是否为目录), ...]
        按深度排序，确保先处理深层项目
    """
    directory = Path(directory_path)
    all_items = []
    
    def scan_directory(current_dir: Path, base_path: Path):
        """递归扫描目录"""
        try:
            items = list(current_dir.iterdir())
            # 按名称排序，确保处理顺序一致
            items.sort(key=lambda x: x.name)
            
            for item in items:
                relative_path = item.relative_to(base_path)
                all_items.append((item, str(relative_path), item.is_dir()))
                
                # 如果是目录且开启递归，继续扫描
                if item.is_dir() and recursive:
                    scan_directory(item, base_path)
                    
        except PermissionError:
            print(f'警告: 无权限访问目录 "{current_dir}"')
        except OSError as e:
            print(f'警告: 访问目录 "{current_dir}" 时出错: {e}')
    
    scan_directory(directory, directory)
    
    # 按深度倒序排列，确保先处理深层文件和目录
    # 这样重命名时不会影响后续的路径访问
    all_items.sort(key=lambda x: (len(x[1].split('/')), x[1]), reverse=True)
    
    return all_items


def process_directory(directory_path: str, dry_run: bool = False, recursive: bool = True) -> List[Tuple[str, str, str]]:
    """
    处理指定目录中的所有文件和子目录
    
    Args:
        directory_path: 目录路径
        dry_run: 是否为测试模式（不实际重命名文件）
        recursive: 是否递归处理子目录
        
    Returns:
        重命名操作的列表 [(原路径, 新路径, 类型), ...]
    """
    directory = Path(directory_path)
    
    if not directory.exists():
        print(f'错误: 目录 "{directory_path}" 不存在')
        return []
    
    if not directory.is_dir():
        print(f'错误: "{directory_path}" 不是一个目录')
        return []
    
    sanitizer = FilenameSanitizer()
    rename_operations = []
    
    # 收集所有需要处理的项目
    all_items = collect_all_items(directory_path, recursive)
    
    print(f'扫描完成，共找到 {len(all_items)} 个项目')
    
    # 处理每个项目
    for item_path, relative_path, is_directory in all_items:
        original_name = item_path.name
        new_name = sanitizer.sanitize_filename(original_name)
        
        # 如果名称发生了变化
        if original_name != new_name:
            new_path = item_path.parent / new_name
            
            # 检查目标路径是否已存在
            if new_path.exists():
                item_type = '目录' if is_directory else '文件'
                print(f'警告: 目标{item_type} "{new_name}" 已存在，跳过重命名')
                continue
            
            item_type = '目录' if is_directory else '文件'
            rename_operations.append((str(item_path), str(new_path), item_type))
            
            if not dry_run:
                try:
                    item_path.rename(new_path)
                    print(f'✓ 重命名{item_type}: "{original_name}" -> "{new_name}"')
                except OSError as e:
                    print(f'错误: 无法重命名{item_type} "{original_name}": {e}')
            else:
                print(f'[测试模式] 将重命名{item_type}: "{original_name}" -> "{new_name}"')
    
    return rename_operations


def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) != 2:
        print('用法: python3 sanitize-filename.py <目录路径>')
        print('示例: python3 sanitize-filename.py /home/user/downloads')
        sys.exit(1)
    
    directory_path = sys.argv[1]
    
    print(f'开始处理目录: {directory_path}')
    print('=' * 50)
    
    # 首先运行测试模式，显示将要进行的操作
    print('预览模式 - 将要进行的操作:')
    print('-' * 30)
    operations = process_directory(directory_path, dry_run=True)
    
    if not operations:
        print('没有需要重命名的文件。')
        return
    
    print(f'\n找到 {len(operations)} 个需要重命名的文件。')
    
    # 询问用户确认
    while True:
        confirm = input('\n是否继续执行重命名操作？(y/n): ').lower().strip()
        if confirm in ['y', 'yes', '是']:
            break
        elif confirm in ['n', 'no', '否']:
            print('操作已取消。')
            return
        else:
            print('请输入 y 或 n')
    
    # 执行实际重命名
    print('\n执行重命名操作:')
    print('-' * 30)
    process_directory(directory_path, dry_run=False)
    print('\n处理完成！')


if __name__ == '__main__':
    main()