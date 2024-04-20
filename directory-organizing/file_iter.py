#!/usr/bin/env python

import os
from typing import Iterable


""" 遍历给定目录下的所有文件 

@param directory: 目录路径
@param is_iter_subdir: 是否遍历子目录
@return: 一个迭代器，每次返回一个元组。第一个元素是文件类型，0表示目录，1表示文件；第二个元素是文件的绝对路径。
"""
def list_files(directory: str, is_iter_subdir: bool = True) -> Iterable[tuple[int, str]]:
    for root, subdirectories, files in os.walk(directory):
        # 先处理子目录
        for subdirectory in subdirectories:
            path = os.path.join(root, subdirectory)
            yield (0, path)

            if is_iter_subdir:
                for (t, file) in list_files(path, is_iter_subdir):
                    yield (t, file)

        # 处理当前目录下的文件
        for file in files:
            yield (1, os.path.join(root, file))


if __name__ == "__main__":
    for (t, file) in list_files("."):
        print(file)