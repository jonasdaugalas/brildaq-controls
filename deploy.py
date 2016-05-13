import os
import sys
import shutil
import glob
import json
import re
import ConfigParser
import argparse


srvpath = '/var/www/wsruncontrol'
srvmount = '/wsruncontrol'
srvmountset = False
clpath = '/var/www/html/runcontrol'
clmount = '/runcontrol'


def main():
    argp = argparse.ArgumentParser()
    argp.add_argument('-c', dest='cpconf', type=str,
                      help='cherrypy config file path')
    args = argp.parse_args()

    cpinfo = get_cpinfo(args.cpconf)
    print(cpinfo)
    print('Deploy server? (y/n)')
    line = readline()
    server = True if line.lower() == 'y' else False
    if server:
        deploy_server()

    print('Deploy client? (y/n)')
    line = readline()
    client = True if line.lower() == 'y' else False
    if client:
        deploy_client()

    if not client and not server:
        print('Nothing to do.')
        return

    print_notes(server, client, cpinfo)


def print_notes(server, client, cpinfo):
    vals = {
        'cphost': cpinfo['host'],
        'cpport': cpinfo['port']
    }

    if client:
        nginx_client = (
            '        location {clmount} {{ \n'
            '            alias {clpath};\n'
            '            index index.html;\n'
            '            try_files $uri/ /index.html =404;\n'
            '        }}\n'
        )
        vals['clmount'] = clmount
        vals['clpath'] = os.path.abspath(clpath)
    else:
        nginx_client = ''

    if server:
        nginx_server = (
            '        location {srvmount} {{ \n'
            '            proxy_set_header X-Forwarded-For $remote_addr;\n'
            '            proxy_pass http://{cphost}:{cpport}/;\n'
            '        }}\n'
        )
        vals['srvmount'] = srvmount
    else:
        nginx_server = ''

    nginx_conf = (
        'http {{\n'
        '    server {{\n'
        '        listen 80;\n' +
        nginx_client +
        nginx_server +
        '    }}\n'
        '}}\n\n'
    )

    print('\nMake sure nginx configuration contains this part:')
    print(nginx_conf.format(**vals))

    if server:
        print('To start cherrypy server:\n'
              '$ cd {}\n'
              '$ [sudo] ./brildaqconfigurator -c {} -d [-u <user>] [-g <group>]\n'
              '# make sure credential files are readable by user'
              .format(srvpath, cpinfo['path']))


def get_cpinfo(path):
    parser = ConfigParser.SafeConfigParser()

    if path is None:
        path = 'cherrypy.config'

    if os.path.isfile(path):
        with open(path, 'r') as f:
            parser.readfp(f)
        host = parser.get('global', 'server.socket_host')[1:-1]
        port = parser.get('global', 'server.socket_port')
    else:
        host = '127.0.0.1'
        port = '5010'
        print('No cherrypy config file found. '
              'Creating default "{}"'.format(path))
        parser.add_section('global')
        parser.set('global', 'server.socket_host', '"' + host + '"')
        parser.set('global', 'server.socket_port', port)
        parser.set('global', 'log.access_file',
                   '"/var/log/cherrypy_brildaq_access.log"')
        parser.set('global', 'log.error_file',
                   '"/var/log/cherrypy_brildaq_error.log"')
        parser.set('global', 'tree.wsgi', "{'/', wsgi.app}")
        with open(path, 'w') as f:
            parser.write(f)

    return {
        'path': path,
        'host': host,
        'port': port
    }


def readline():
    return sys.stdin.readline()[:-1]


def deploy_server():
    global srvpath
    print('Put server files on file system: (default:"{}")'.format(srvpath))
    line = readline()
    if len(line) > 0:
        srvpath = line
    if os.path.isdir(srvpath):
        print('Directory "{}" exists'.format(srvpath))
    else:
        print('Creating directory "{}" with permissions 755'.format(srvpath))
        os.makedirs(srvpath, 0755)
    print('Copy python (.py) files')
    copyfiles(r'*.py', srvpath)
    print('Copy json (.json, .jsn) files')
    copyfiles(r'*.json', srvpath)
    copyfiles(r'*.jsn', srvpath)
    print('Copy other config (.config, .cfg, .conf) files')
    copyfiles(r'*.config', srvpath)
    copyfiles(r'*.cfg', srvpath)
    copyfiles(r'*.conf', srvpath)
    print('Copy README.org')
    copyfiles('README.org', srvpath)

    copydir('easyconfig', os.path.join(srvpath, 'easyconfig'))
    copydir('tools', os.path.join(srvpath, 'tools'))

    set_server_mount()


def set_server_mount():
    global srvmount
    global srvmountset
    print('Server mount point on host: (default:"{}")'.format(srvmount))
    line = readline()
    if len(line) > 0:
        srvmount = line
    srvmountset = True
    print('Server mount point set: {}'.format(srvmount))


def deploy_client():
    global clmount
    global clpath

    print('Put client files on file system: (default:"{}")'.format(clpath))
    line = readline()
    if len(line) > 0:
        clpath = line
    if os.path.isdir(clpath):
        print('Directory "{}" exists'.format(clpath))
    else:
        print('Creating directory "{}" with permissions 755'.format(clpath))
        os.makedirs(clpath, 0755)

    if not os.path.isfile('client/bundle.js'):
        print('Looks like client code is not compiled '
              '("client/bundle.js" missing). Please compile client and '
              'rerun deployment.\nTo compile client:\n'
              '$ cd client\n'
              '$ npm install')
        sys.exit(1)

    copyfiles(r'client/bundle.js', clpath)
    copyfiles(r'client/index.html', clpath)
    copyfiles(r'client/viewlog.html', clpath)
    copyfiles(r'client/const.json', clpath)
    copydir('client/styles', os.path.join(clpath, 'styles'))
    copydir('client/vendor', os.path.join(clpath, 'vendor'))
    copydir('client/img', os.path.join(clpath, 'img'))
    copydir('client/templates', os.path.join(clpath, 'templates'))

    print('Client mount point on host: (default: "{}")'.format(clmount))
    line = readline()
    if len(line) > 0:
        clmount = line
    indexbase = clmount if clmount[-1] == '/' else clmount + '/'

    print('Setting client base tag')
    with open(os.path.join(clpath, 'index.html'), 'r') as f:
        indexfile = f.read()
    indexfile, subs = re.subn(r'<base href="(.*?)" />',
                              '<base href="' + indexbase + '" />',
                              indexfile,
                              count=1)
    if subs != 1:
        print('Failed to substitute "base" tag in index.html. '
              'Subs.count ({}) != 1'.format(subs))
        sys.exit(1)
    with open(os.path.join(clpath, 'index.html'), 'w') as f:
        f.write(indexfile)

    if not srvmountset:
        print('Client needs to know server mount point.')
        set_server_mount()
    print('Setting client constants.')
    with open(os.path.join(clpath, 'const.json'), 'r') as f:
        clconst = json.load(f)
    clconst['server_endpoint'] = srvmount
    with open(os.path.join(clpath, 'const.json'), 'w') as f:
        json.dump(clconst, f)


def copydir(src, dest):
    if os.path.isdir(dest):
        print('Directory "{}" exists - removing..'.format(dest))
        shutil.rmtree(dest)
    print('COPYING "{}" TO {}'.format(src, dest))
    shutil.copytree(src, dest)


def copyfiles(pattern, dest):
    for fname in glob.glob(pattern):
        print('COPYING "{}" TO "{}"'.format(fname, dest))
        shutil.copy(fname, dest)


if __name__ == '__main__':
    main()
