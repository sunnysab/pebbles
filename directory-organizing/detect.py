#! /usr/bin/env python
# This file requires ollama to be installed. You can install it with:
# pip install ollama

import ollama
from pprint import pprint

_SYSTEM_PROMPT = """
你是一个程序组件。
我会给你提供音频文件的元信息、原始的文件名，它们可能包含错误，也可能缺失。
一首歌可能由多个歌手创作，并且标题可能也包含了歌手，你需要将他们识别出来。
如，“刘若英_黄韵玲-听！是谁在唱歌” 中，歌手为“刘若英, 黄韵玲”；“高明骏陈艾湄-那种心跳的感觉“ 中，歌手为“高明骏, 陈艾湄”；“小星星Aurora-红黑” 中，歌手为“小星星Aurora”。
字段里可能包含一些广告或来源信息，忽略它们。
你需要给我提供实际的歌手名称、专辑名称和音乐标题，回答的数据应包含artist、album、title、type四部分内容。若某字段不存在则内容留空。
如果歌手有多个，请用逗号分隔。
如果你认为这是一首现场版音乐（live版本），将type置为“live”，若为 DJ 则标记“DJ”，否则留空。
请按照以下纯文本格式回答：
artist: 周杰伦
album: 
title: 双节棍
type: live
不要任何额外的说明！
"""

_client = ollama.Client(host='http://192.168.130.200:11434')



def suspect(metadata: dict, filename: str) -> dict:
    text_metadata = '\n'.join([f'{k}: {v}' for k, v in metadata.items()])
    
    for ext in ['mp3', 'flac', 'ape', 'wav', 'm4a']:
        if filename.endswith(ext):
            filename = filename.rstrip(ext)
            break
    text_filename = filename

    response = _client.generate(
        model='azure99/blossom-v5',
        system=_SYSTEM_PROMPT,
        prompt=f'metadata: {text_metadata}\nfilename: {text_filename}',
        keep_alive=600,
    )['response'].strip()

    print(response)
    # 有时候抽风，返回的结果是 JSON 格式.
    if response.startswith('```json'):
        response = response[7:-3]

        import json
        parsed_dict = json.loads(response)
        return parsed_dict

    # 有时候抽风，仍然会返回多余的信息.
    lines = response.split('\n')[:4]
    parsed_dict = {}
    for line in lines:
        parts = line.split(':', 1)
        key = parts[0]
        value = parts[1].strip() if len(parts[1]) > 1 else None
        parsed_dict[key] = value
    if 'album' not in parsed_dict or not parsed_dict['album']:
        parsed_dict['album'] = None

    return parsed_dict
