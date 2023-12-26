"""
Audio related helper functions
"""

import re
import audioread
import requests
import os

# add other audio filetypes as you support them
TYPE_REGEX = '\.mp3'

def test_length(url: str) -> int:
    '''
    Test the length of a mp3 at the given url
    '''
    time = 0
    ext = re.search(TYPE_REGEX, url)
    if ext is None:
        return time
    ext = ext.group(0)
    name = f"temp{ext}"
    try:
        with open(name, 'wb') as f:
            doc = requests.get(url)
            f.write(doc.content)
        with audioread.audio_open(name) as f:
            # totalsec contains the length in float
            time = f.duration
    except:
        # just to make sure the file gets removed if there are
        # any errors after creation
        pass
    os.remove(name)
    return int(time)
