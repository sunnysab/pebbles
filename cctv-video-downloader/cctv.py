#! /usr/bin/sh

import re
import subprocess
import asyncio
import requests
from pprint import pprint
from typing import List, Tuple
from downloader import AsyncDownloader


__TMP_DIR = '/tmp/'
__SESSION = requests.Session()
__PATTERN_GUID = re.compile(r'var guid = "([a-z0-9]{32})";')


def parse_guid(html: str) -> str | None:
    return __PATTERN_GUID.findall(html)[0]

def get_video_info(video_guid: str) -> dict:
    url = 'https://vdn.apps.cntv.cn/api/getHttpVideoInfo.do'
    params = {
        'pid': video_guid,
        'client': 'flash',
        'im': 0,
    }

    response = __SESSION.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    video_alternative_count = data['video']['validChapterNum']
    best_chapter = data['video'][f'chapters{video_alternative_count}']
    return {
        'title': data['title'],
        'tag': data['tag'],
        'mp4': [x['url'] for x in best_chapter]
    }

def concat_videos_by_ffmpeg(file_list: List[str], output_title: str):
    input_parameters = '\n'.join([f'file {f}' for f in file_list])

    # cat list.txt | ffmpeg -f concat -safe 0 -protocol_whitelist "file,http,https,tcp,tls" -i /dev/stdin -c:v libsvtav1 output990.mp4
    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', '/dev/stdin', '-c:v', 'libsvtav1', f'{output_title}.mp4'], input=input_parameters.encode())


if __name__ == '__main__':
    import sys

    if len(sys.argv) == 1:
        print('需要指定一个视频链接')
        exit()

    web_url = sys.argv[1]
    html = __SESSION.get(web_url).text
    video_info = get_video_info(parse_guid(html))

    pprint(video_info)

    downloader = AsyncDownloader()
    file_list = asyncio.run(downloader.download_files(video_info['mp4'], __TMP_DIR))

    print(f'下载完成，共 {len(file_list)} 个片段.')
    concat_videos_by_ffmpeg(file_list, video_info['title'])
