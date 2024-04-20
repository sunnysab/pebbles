#! /usr/bin/env python3

import os
import sys
from typing import Iterable
from tag import FileMetadata


BLOCK_WORDS = ['车载', '酷我', '酷狗', 'wx', '排行榜', '无损', '正版', 'www.', '.com', 'qq', '出品', '精品', '3D环绕', '优音', '抖音', '歌曲', '流行', '音樂論壇', '音乐论坛', '收藏']


def walk_files(path: str) -> Iterable[str]:
    for (root, _, fs) in os.walk(path):
        for f in fs:
            yield os.path.join(root, f)


if __name__ == '__main__':
    INPUT_PATH = sys.argv[1] if len(sys.argv) > 1 else '.'

    for file in walk_files:
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
