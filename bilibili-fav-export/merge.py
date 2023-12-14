

MUSICS: dict = {}


def load_and_merge(file: str) -> int:
    """
    Loads a music file and merges it with the current music list.
    """
    global MUSIC_LIST

    count: int = 0
    with open(file, "r") as f:
        music_list = f.readlines()
        for line in music_list:
            if not line:
                continue

            columns = line.strip().split('\t')
            bv = columns[0]
            title = columns[1]
            length = columns[-1]
            try:
                length = int(length)
            except:
                pass


            if title == '已失效视频':
                continue

            MUSICS[bv] = (title, length)
            count += 1


def load_files():
    """
    Loads all music files.
    """
    
    import os

    for _, _, filenames in os.walk('.'):
        for filename in [f for f in filenames if f.endswith('.csv')]:
            load_and_merge(filename)


load_files()


from pprint import pprint
MUSICS = [(bv, title, length) for bv, (title, length) in MUSICS.items()]

pprint(MUSICS)