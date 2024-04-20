#! /usr/bin/env python3

import sys
from file_iter import list_files
from tag import FileMetadata


BLOCK_WORDS = ['车载', '酷我', '酷狗', 'wx', '排行榜', '无损', '正版', 'www.', '.com', 'qq', '出品', '精品', '3D环绕', '优音', '音樂論壇', '音乐论坛', '收藏']

if __name__ == '__main__':
    INPUT_PATH = sys.argv[1] if len(sys.argv) > 1 else '.'

    for (t, file) in list_files(INPUT_PATH):
        if t == 0:
            continue
        if not file.endswith('.flac'):
            continue

        try:
            metadata = FileMetadata(file)
            if metadata.filter(BLOCK_WORDS):
                metadata.print()
        except Exception as e:
            print(f'file: {file}')
            print(f'error: {e}')
            continue
