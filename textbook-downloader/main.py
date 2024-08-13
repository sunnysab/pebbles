#! /usr/bin/python

import os
import json
import sys
import requests
from tqdm import tqdm
from typing import List, Tuple
from pprint import pprint


session = requests.Session()


def convert(single_line: dict) -> Tuple[str, str, str, str]:
    return single_line['title'], single_line['path'], single_line['id'], single_line['cover']


def load(path: str) -> List[dict]:
    file = open(path, 'r')
    data = json.load(file)

    # data 是嵌套的 dict 对象, 嵌套层数未知. 需要将其转换为 List[(title, path, id, cover)]
    def dfs(obj: list | dict):
        if isinstance(obj, dict):
            # 如果是一个课本对象, 将其添加到结果中
            if 'id' in obj:
                return [convert(obj)]
            else:
                return dfs(obj['children'])
        elif isinstance(obj, list):
            result = []
            for item in obj:
                result += dfs(item)
            return result
        else:
            raise ValueError('Invalid data type')
        
    return dfs(data)


def download_to(url: str, path: str, exception: bool = False):
    # 避免重复下载
    if os.path.exists(path):
        return 

    response = session.get(url)
    if response.status_code != 200:
        print(f'[{response.status_code}] failed to download {url} to {path}', file=sys.stderr)
        if exception:
            raise Exception('Failed to download')

    with open(path, 'wb') as file:
        file.write(response.content)


def download(data: Tuple[str, str, str, str]):
    title, path, id, cover = data

    # 创建文件夹
    path_on_disk = path.rsplit('/', 2)[0] + '/'
    if not os.path.exists(path_on_disk):
        os.makedirs(path_on_disk)

    # 下载封面
    download_to(cover, path_on_disk + title + '_cover.jpg')

    # 下载课本
    try:
        download_to(f'https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets_document/{id}.pkg/pdf.pdf', path_on_disk + title + '.pdf', exception=True)
    except:
        download_to(f'https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets/{id}.pkg/pdf.pdf', path_on_disk + title + '.pdf')


def main():
    data = load('data.json')
    print(f'length of data: {len(data)}')
    for item in tqdm(data):
        download(item)


if __name__ == '__main__':
    main()