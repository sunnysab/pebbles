#!/usr/bin/env python

import os
import argparse
from typing import Iterable
from zhconv import convert


DRY_RUN = True


def rename(old_name: str, new_name: str):
    print(f'{old_name} -> {new_name}')

    if not DRY_RUN:
        os.rename(old_name, new_name)


def walk_files(path: str) -> Iterable[str]:
    for (root, _, fs) in os.walk(path):
        for f in fs:
            yield os.path.join(root, f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='convert-to-simplified-chinese.py',
        description='Convert filenames to simplified Chinese')
    
    parser.add_argument('path', help='Path to the directory to convert')
    parser.add_argument('--dry-run', action='store_true', help='Don\'t actually rename files')

    args = parser.parse_args()
    PATH = args.path
    DRY_RUN = args.dry_run

    for file in walk_files(PATH):
        new_name = convert(file, 'zh-cn')
        if new_name != file:
            rename(file, new_name)