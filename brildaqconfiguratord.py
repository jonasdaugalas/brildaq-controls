#!/nfshome0/lumipro/brilconda/bin/python
"""Start cherrypy http server and run brildaq configurator flask app inside"""

import sys
import argparse
import cherrypy
from cherrypy.process import plugins


class Cherryd:

    def configure(self, configfiles=None, environment=None):
        import wsgi
        for c in configfiles or []:
            cherrypy.config.update(c)

        if environment is not None:
            try:
                cherrypy.config.update({'environment': environment})
            except KeyError:
                # allow environments undefined in
                # cherrypy._cpconfig.environments
                pass

    def run(self, daemonize=None, pidfile=None, user=None, group=None):
        engine = cherrypy.engine

        if daemonize:
            # Don't print anything to stdout/sterr.
            cherrypy.config.update({'log.screen': False})
            plugins.Daemonizer(engine).subscribe()

        if pidfile:
            plugins.PIDFile(engine, pidfile).subscribe()

        if user or group:
            plugins.DropPrivileges(engine, uid=user, gid=group).subscribe()

        if hasattr(engine, "signal_handler"):
            engine.signal_handler.subscribe()
        if hasattr(engine, "console_control_handler"):
            engine.console_control_handler.subscribe()

        # Always start the engine; this will start all other services
        try:
            engine.start()
        except:
            # Assume the error has been logged already via bus.log.
            sys.exit(1)
        else:
            engine.block()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', type=str, nargs='*',
                        default=['cherrypy.config'],
                        help="config file(s). default: 'cherrypy.config'")
    parser.add_argument('-d', dest='daemonize', action='store_true',
                        help="run the server as a daemon")
    parser.add_argument('-u', '--user', type=str, default=None,
                        help="run the server as user")
    parser.add_argument('-g', '--group', type=str, default=None,
                        help="run the server as group")
    parser.add_argument('-e', '--environment', type=str, default=None,
                        help="apply the given config environment")
    parser.add_argument('-p', '--pid', type=str, default=None,
                        help='file to store PID (use absolute path when '
                        'runnung as daemon)')

    args = parser.parse_args()
    print(args.__dict__)

    cherryd = Cherryd()

    cherryd.configure(args.config, args.environment)
    cherryd.run(args.daemonize, args.pid, args.user, args.group)
