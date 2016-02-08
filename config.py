import sys
import json


REQUIRED = ['authfile', 'easyconfigmap', 'easyconfigdir']


with open('config.json', 'r') as f:
    parsed = json.load(f)
    for req in REQUIRED:
        if req not in parsed:
            raise KeyError('config.json missing required key: ', req)

    for k, v in parsed.iteritems():
        setattr(sys.modules[__name__], k, v)
