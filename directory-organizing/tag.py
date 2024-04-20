#! /usr/bin/env python3
# 脚本需要兼容 Python3.9 (FreeBSD)

import os
from typing import Union
from mutagen import FileType
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.apev2 import APEv2


class FileMetadata:
    file_path: str = ''
    metadata: FileType = None
    dirty: bool = False

    def __init__(self, file_path: str):
        self.file_path = file_path
        if not os.path.isfile(file_path):
            raise Exception('file not found')

        ext = file_path.rsplit('.', 1)[1].lower()
        if ext == 'flac':
            self.metadata = FLAC(file_path)
        elif ext == 'mp3':
            self.metadata = MP3(file_path)
        elif ext == 'ape':
            self.metadata = APEv2(file_path)
        else:
            raise Exception('unsupported file type')

    def get_metadata(self) -> dict:
        sep = lambda l: ';'.join(l) if l else ''

        artist = sep(self.metadata['artist']) if 'artist' in self.metadata else ''
        album = sep(self.metadata['album']) if 'album' in self.metadata else ''
        title = sep(self.metadata['title']) if 'title' in self.metadata else ''
        return {'artist': artist, 'album': album, 'title': title}
    
    def set_metadata(self, metadata: dict) -> None:
        for key, value in metadata.items():
            if isinstance(value, str):
                value = value.split(';')
            self.metadata[key] = value
        self.metadata.save()

    def __getitem__(self, key: str) -> Union[str, list]:
        return self.metadata.get(key)

    def _save(self) -> None:
        self.metadata.save()

    def _filter_one_list(self, lst: list, block_words: list) -> tuple[bool, list]:
        modified = False

        for e in lst:
            for word in block_words:
                if word in e.lower():
                    lst.remove(e)
                    self.dirty = True
                    modified = True
                    break
        return (modified, lst)

    def filter(self, block_words: list) -> bool:
        for (key, value) in self.metadata.items():
            if isinstance(value, list):
                flag, new_list = self._filter_one_list(value, block_words)
                if flag:
                    self.metadata[key] = new_list

        if 'encoded_by' in self.metadata:
            self.metadata['encoded_by'] = ''
            self.dirty = True

        if self.dirty:
            self._save()
        return self.dirty

    def print(self) -> None:
        for key in self.metadata:
            print(f'{key}: {self.metadata[key]}')
        print()


if __name__ == '__main__':
    file = '/mnt/nas/wd-2T/音乐/flac/周传雄/华语流行排行榜/周传雄 - 我难过.flac'
    metadata = FileMetadata(file)

    metadata.print()
    metadata.filter(['车载', '酷我', '酷狗', 'wx', '排行榜', '无损', '正版', 'www.', '.com', 'qq'])
    
    print('after filter:')
    metadata.print()
