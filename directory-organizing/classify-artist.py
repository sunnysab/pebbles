#! /usr/bin/env python3

import re
import os
import sys
from tag import FileMetadata
from artist import ALL
from detect import suspect

ALL_ARTISTS = set(ALL)

INPUT_PATH = sys.argv[1] if len(sys.argv) > 1 else '.'
OUTPUT_PATH = sys.argv[2] if len(sys.argv) > 2 else INPUT_PATH


for path in os.listdir(INPUT_PATH):
    path = os.path.join(INPUT_PATH, path)

    if not os.path.isfile(path):
        continue

    try:
        metadata = FileMetadata(path)
    except Exception as e:
        print(f'file: {path}')
        print(f'error: {e}')
        continue
        
    metadata = metadata.get_metadata()
    artist = metadata['artist'].strip()
    album = metadata['album'].strip()
    title = metadata['title'].strip()

    # 如果从文件信息中读取不到歌手或歌名，则根据文件名判断.
    if not artist or not title:
        file = path.rsplit('/', 1)[-1]
        parts = re.split(r's*-s*|s+', file)
        # 如果文件名无法分割，直接删了吧
        if len(parts) < 2:
            print(f'file: {file}')
            print(f'error: cannot parse artist and title')
            os.remove(path)
        # 分割完成，如果分割超出预期，需要手动处理
        elif len(parts) > 2:
            continue
        else:
            maybe_artist = parts[0].strip()
            maybe_title = parts[1].rsplit('.', 1)[0].strip()
            if maybe_artist in ALL_ARTISTS:
                artist = maybe_artist
                title = maybe_title
            elif maybe_title in ALL_ARTISTS:
                artist = maybe_title
                title = maybe_artist
            else: # 无法判断歌手，用 AI 处理
                print(f'file: {file}')
                print(f'metadata: {metadata}')

                suspect_result = suspect(metadata, file)
                print(f'  => suspect: {suspect_result}')
                artist = suspect_result['artist']
                title = suspect_result['title']
                if not artist or not title:
                    print(f'error: cannot parse artist and title')
                    os.remove(path)
                    continue

    if '金曲' in album or '精选' in album or '合辑' in album or '粤语' in album or '国语' in album:
        album = None
    if not album or not album.strip():
        album = '单曲'

    ext = path.rsplit('.', 1)[1].lower()
    new_name = f'{artist} - {title}.{ext}'

    if ',' in artist:
        artist = artist.split(',')[0].strip()

    new_path = os.path.join(OUTPUT_PATH, artist, album, new_name)

    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    print(f'{path} -> {new_path}')
    os.rename(path, new_path)
        