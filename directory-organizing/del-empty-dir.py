#! /usr/bin/env python3

import os
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else '.'

for root, dirs, files in os.walk(PATH, topdown=False):
    if not files and not dirs:
        print(f'deleting empty directory: {root}')
        os.rmdir(root)