#! /usr/bin/python

"""
API document: https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/docs/fav/list.md
"""

import requests 
from typing import List, Any
from dataclasses import dataclass


@dataclass
class StaredVideo:
    bv_id: str
    title: str
    introduction: str
    duration: int


def export(id: int) -> List[StaredVideo]:
    def do_map(o: Any) -> StaredVideo:
        return StaredVideo(bv_id=o['bv_id'],
                        duration=o['duration'],
                        introduction='',
                        title=o['title'])

    def query_by_page(id: int, page: int) -> List[StaredVideo]:
        response = requests.get('https://api.bilibili.com/x/v3/fav/resource/list', 
                                params={'media_id': id, 'pn': page, 'ps': 20})
        response.raise_for_status()

        try:
            video_list = response.json()['data']['medias'] or []
        except:
            print(f'Server returned text: {response.text}')
            return []
        
        return [do_map(e) for e in video_list]
    
    result: List[StaredVideo] = []
    last_size: int = 20
    last_page: int = 1
    while last_size == 20:
        page = query_by_page(id, last_page)
        result.extend(page)

        last_page += 1
        last_size = len(page)

    return result


if __name__ == '__main__':
    import sys
    import os

    assert len(sys.argv) == 2

    fav_collection_id = int(sys.argv[1])
    exported_collection = export(fav_collection_id)

    filename = f'collection-{fav_collection_id}'
    count = 0
    make_filename = lambda: filename + '.csv' if count == 0 else f'{filename}-{count}.csv'
    while os.path.exists(make_filename()) and count < 100:
        count += 1


    with open(make_filename(), 'w+') as f:
        for v in exported_collection:        
            l = '\t'.join([str(x) for x in v.__dict__.values()]) + '\n'
            f.write(l)
