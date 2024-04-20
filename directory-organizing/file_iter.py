#!/usr/bin/env python

import os
from typing import Iterable


""" 遍历目录（含子目录）下的所有文件 """
def list_files(directory: str) -> Iterable[tuple[int, str]]:
    for root, subdirectories, files in os.walk(directory):
        # 先处理子目录
        for subdirectory in subdirectories:
            path = os.path.join(root, subdirectory)
            yield (0, path)

            for (t, file) in list_files(path):
                yield (t, file)

        # 处理当前目录下的文件
        for file in files:
            yield (1, os.path.join(root, file))



if __name__ == "__main__":
    for (t, file) in list_files("."):
        print(file)