import sys
import json
import requests
import argparse


URL = 'http://srv-s2d16-22-01/wsbrildaqcfgtest'


def main():
    args = parse_args()
    cmd = args.cmd
    if cmd == 'list':
        do_list(args)
    elif cmd == 'get':
        do_get(args)
    elif cmd == 'exec':
        do_exec(args)
    elif cmd == 'submit':
        do_submit(args)
    else:
        raise ValueError('Oops.. unknown command {}'.format(cmd))


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Command line interface for brildaq configurator\n\n'
        'Examples:\n\n'
        'list owners\n'
        'list paths -u lumipro\n'
        'list running -u lumipro\n'
        'get state /lumipro/central/global/bestLumiProcessor\n'
        'get config /lumipro/central/global/bestLumiProcessor\n'
        'get fields /lumipro/central/global/bestLumiProcessor\n'
        'exec create /lumipro/central/global/bestLumiProcessor\n'
        'exec turnon /lumipro/central/global/bestLumiProcessor\n'
        'submit fields -p /lumipro/central/global/bestLumiProcessor -i path/to/fields_file.json -c "comment for new version"\n')
    subparsers = parser.add_subparsers(dest='cmd')
    ls_parser = subparsers.add_parser('list')
    ls_parser.add_argument('object', type=str,
                           help='One of "owners", "paths", "running"')
    ls_parser.add_argument('-u', dest='owner', type=str, metavar='user',
                           help='Filter "paths" or "running" by owner')
    get_parser = subparsers.add_parser('get')
    get_parser.add_argument(
        'object', type=str,
        help='One of "state", "history", "config", "fields", "full". '
        '"state" - get configuration state. '
        '"history" - get configuration version history. '
        '"config" - get xdaq configuration xml. '
        '"fields" - get configuration predefined fields. '
        '"full" - get full configuration xml.')
    get_parser.add_argument('path', type=str, help='Configuration path')
    exec_parser = subparsers.add_parser('exec')
    exec_parser.add_argument(
        'exec_command', type=str,
        help='One of "create", "destroy", "turnon", "turnoff", "reset". '
        '"create" - instantiate function manager. '
        '"destroy" - destroy function manager. '
        '"turnon" - turn executive on. '
        '"turnoff" - turn executive off. '
        '"reset" - reset executive (from error state).')
    exec_parser.add_argument('path', type=str, help='Configuration path')
    submit_parser = subparsers.add_parser('submit')
    submit_parser.add_argument(
        'type', type=str,
        help='Type of content. One of "fields", "full". '
        '"fields" - content file will be treated as predefined fields (json). '
        '"full" - content file will be treated as final function '
        'manager configuration (xml).')
    submit_parser.add_argument('-p', '--path', required=False, type=str,
        help='Configuration path (not needed for "submit full")')
    submit_parser.add_argument('-i', '--input', type=str, required=True,
                               help='Input file (full.xml, fields.json, ...)')
    submit_parser.add_argument('-c', dest='comment', required=False, type=str,
                               help='Comment for new version')
    return parser.parse_args()


def do_list(args):
    obj = args.object
    if obj == 'owners':
        resp = requests.get(URL + '/owners')
        exit_if_failed(resp)
        print(resp.text)
    elif obj == 'paths':
        req = URL + '/configurations'
        if args.owner:
            req += '/' + args.owner
        resp = requests.get(req)
        exit_if_failed(resp)
        result = json.loads(resp.text)
        result = result.keys()
        print(json.dumps(result, indent=2))
    elif obj == 'running':
        req = URL + '/running'
        if args.owner:
            req += '/' + args.owner
        resp = requests.get(req)
        exit_if_failed(resp)
        result = json.loads(resp.text)
        result = result.keys()
        print(json.dumps(result, indent=2))
    else:
        raise ValueError('Unknown object {}'.format(obj))


def do_get(args):
    obj = args.object
    path = args.path
    if obj == 'state':
        resp = requests.get(URL + '/state' + path)
        exit_if_failed(resp)
        print(resp.text)
    elif obj == 'history':
        resp = requests.get(URL + '/history' + path)
        exit_if_failed(resp)
        result = json.loads(resp.text)
        print(json.dumps(result, indent=2))
    elif obj == 'config':
        resp = requests.get(URL + '/configxml' + path)
        exit_if_failed(resp)
        print(resp.text)
    elif obj == 'fields':
        resp = requests.get(URL + '/config' + path)
        exit_if_failed(resp)
        result = json.loads(resp.text)
        if 'fields' not in result or result['fields'] is None:
            print([])
            sys.exit(1)
        print(json.dumps(result['fields'], indent=2))
    elif obj == 'full':
        resp = requests.get(URL + '/fullxml' + path)
        exit_if_failed(resp)
        print(resp.text)
    else:
        raise ValueError('Unknown object {}'.format(obj))


def do_exec(args):
    cmd = args.exec_command.lower()
    path = args.path
    if cmd == 'create':
        resp = requests.get(URL + '/create' + path)
        exit_if_failed(resp)
        print(resp.text)
    elif cmd == 'destroy':
        resp = requests.get(URL + '/destroy' + path)
        exit_if_failed(resp)
        print(resp.text)
    elif cmd == 'turnon':
        resp = requests.get(URL + '/send/TurnON' + path)
        exit_if_failed(resp)
        print(resp.text)
    elif cmd == 'turnoff':
        resp = requests.get(URL + '/send/TurnOFF' + path)
        exit_if_failed(resp)
        print(resp.text)
    elif cmd == 'reset':
        resp = requests.get(URL + '/send/Reset' + path)
        exit_if_failed(resp)
        print(resp.text)
    else:
        raise ValueError('Unknown exec_command {}'.format(cmd))


def do_submit(args):
    t = args.type.lower()
    path = args.path
    comment = args.comment

    if t == 'fields':
        if path is None:
            print('"path" argument required for submitting fields.')
            sys.exit(1)
        with open(args.input, 'r') as f:
            content = json.load(f)
        data = {
            "path": path,
            "fields": content,
            "comment": comment
        }
        resp = requests.post(URL + '/submitfields', json=data)
        exit_if_failed(resp)
        print(resp.text)
    elif t == 'full':
        with open(args.input, 'r') as f:
            content = f.read()
        data = {
            "xml": content,
            "comment": comment
        }
        resp = requests.post(URL + '/submitfull', json=data)
        exit_if_failed(resp)
        print(resp.text)
    else:
        raise ValueError('Unknown submit type {}'.format(t))


def exit_if_failed(resp):
    if resp.status_code != 200:
        print(resp.text)
        sys.exit(1)


if __name__ == '__main__':
    main()
