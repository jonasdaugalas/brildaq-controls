import sys
import os
import json
import config


easyconfigmap = {}


with open(config.easyconfigmap, 'r') as f:
    parsed = json.load(f)

    for k, v in parsed.iteritems():
        path = os.path.join(config.easyconfigdir, v)
        with open(path, 'r') as ec:
            easyconfig = json.load(ec)
            easyconfigmap[k] = easyconfig
