import functools
import json
import flask
import utils
import rcmsws
import config
import configurator_errors as err
import custom_logging


# prepare logging
log = custom_logging.get_logger(__name__)
actionlog = custom_logging.get_action_logger()

# module attributes
dbcon = None
# static_folder - hardcoded, for dev only
app = flask.Flask(__name__, static_folder='client', static_url_path='')

appv = 0  # just some variable to send to client when asked


def init():
    app.logger.addHandler(custom_logging.handler)
    servicemap = utils.parse_service_map(config.authfile)
    global dbcon
    dbcon = utils.dbconnect(servicemap)


def finalize():
    print('finalizing...')
    dbcon.close()


def default_configurator_error_response(fun):
    @functools.wraps(fun)
    def inner(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except err.ConfiguratorInternalError as e:
            return flask.Response(e.text(), mimetype='text/plain', status=500)
        except err.ConfiguratorUserError as e:
            return flask.Response(e.text(), mimetype='text/plain', status=400)

    return inner


def get_name_from_cookie(request):
    if 'clientname' in request.cookies:
        return str(request.cookies['clientname'])[:16]
    else:
        return '<no name>'


# route: /static_base/app_base
@app.route('/gui/')
@app.route('/gui')
@app.route('/gui/<path:path>')
def index(path=None):
    return app.send_static_file('index.html')


@app.route('/help')
def get_endpoints():
    endpoints = {}
    for rule in app.url_map.iter_rules():
        if (rule.endpoint not in endpoints):
            endpoints[rule.endpoint] = []
            endpoints[rule.endpoint].append(str(rule))
    return flask.Response(json.dumps(endpoints, indent=2),
                          mimetype='application/json')


@app.route('/owners/')
@app.route('/owners')
@default_configurator_error_response
def get_owners():
    r = utils.get_owners(dbcon)
    return flask.Response(json.dumps(r), mimetype='application/json')


@app.route('/configurations/<string:owner>')
@app.route('/configurations')
@default_configurator_error_response
def get_configurations(owner=None):
    r = utils.get_configurations(dbcon, owner)
    return flask.Response(json.dumps(r), mimetype='application/json')


@app.route('/running/<string:owner>')
@app.route('/running')
@default_configurator_error_response
def get_running(owner=None):
    log.info('getting running')
    r = utils.get_running_configurations(dbcon, owner)
    return flask.Response(json.dumps(r), mimetype='application/json')


@app.route('/states/', methods=['GET', 'POST'])
@app.route('/states', methods=['GET', 'POST'])
@default_configurator_error_response
def get_states():
    if flask.request.method == 'GET':
        return flask.Response(
            'Use POST method (or GET /state/<path>). Request body: json array '
            'of configuration URIs (string)', status=405)
    data = flask.request.json
    r = rcmsws.get_states(data)
    return flask.Response(json.dumps(r), mimetype='application/json')


@app.route('/state/<path:path>')
@default_configurator_error_response
def get_state(path):
    uri = utils.path2uri('/' + path)
    r = rcmsws.get_state(uri)
    return flask.Response(json.dumps(r), mimetype='application/json')


@app.route('/send/<string:command>/<path:path>', methods=['GET', 'POST'])
@app.route('/send/<string:command>', methods=['GET', 'POST'])
@default_configurator_error_response
def send_command(command, path=None):
    if flask.request.method == 'GET':
        uri = utils.path2uri('/' + path)
    else:
        uri = flask.request.json
        path = utils.uri2path(uri)
    client = get_name_from_cookie(flask.request)
    actionlog.info('{:<8} {}; {}; {}; {}'.format(
        command.upper(), path, client, flask.request.user_agent.string,
        flask.request.environ['HTTP_X_FORWARDED_FOR']))
    if rcmsws.send_command(command, uri):
        return ('OK', 200)
    else:
        return flask.Response('Send command failed', status=400)


@app.route('/create/<path:path>', methods=['GET', 'POST'])
@app.route('/create', methods=['GET', 'POST'])
@default_configurator_error_response
def create_fm(path=None):
    if flask.request.method == 'GET':
        uri = utils.path2uri('/' + path)
    else:
        uri = flask.request.json
        path = utils.uri2path(uri)
    client = get_name_from_cookie(flask.request)
    actionlog.info('CREATE   {}; {}; {}; {}'.format(
        path, client, flask.request.user_agent.string,
        flask.request.environ['HTTP_X_FORWARDED_FOR']))
    if rcmsws.create(uri):
        return ('OK', 200)
    else:
        return flask.Response('Failed to create', status=400)


@app.route('/destroy/<path:path>', methods=['GET', 'POST'])
@app.route('/destroy', methods=['GET', 'POST'])
@default_configurator_error_response
def destroy_fm(path=None):
    if flask.request.method == 'GET':
        uri = utils.path2uri('/' + path)
    else:
        uri = flask.request.json
        path = utils.uri2path(uri)
    client = get_name_from_cookie(flask.request)
    actionlog.info('DESTROY  {}; {}; {}; {}'.format(
        path, client, flask.request.user_agent.string,
        flask.request.environ['HTTP_X_FORWARDED_FOR']))
    if rcmsws.destroy(uri):
        return ('OK', 200)
    else:
        return flask.Response('Failed to destroy', status=400)


@app.route('/history/<path:path>')
@app.route('/history/<path:path>/limit=<int:limit>')
@app.route('/history/<path:path>/limit=<int:limit>/bellow=<int:bellow>')
@default_configurator_error_response
def get_versions(path, limit=None, bellow=None):
    r = utils.get_versions(dbcon, '/' + path, limit, bellow)
    if r is None:
        flask.abort(404)
    return flask.Response(json.dumps(r), mimetype='application/json')


@app.route('/configxml/<path:path>')
@app.route('/configxml/<path:path>/v=<int:version>')
@default_configurator_error_response
def get_config_xml(path, version=None):
    r = utils.get_config_xml(dbcon, '/' + path, version)
    if r is None:
        flask.abort(404)
    return flask.Response(r, mimetype='text/xml')


@app.route('/config/<path:path>/v=<int:version>/noxml')
@app.route('/config/<path:path>/v=<int:version>')
@app.route('/config/<path:path>/noxml')
@app.route('/config/<path:path>')
@default_configurator_error_response
def get_config(path, version=None):
    log.debug(flask.request.url)
    if flask.request.url.endswith('/noxml'):
        r = utils.get_config(dbcon, '/' + path, version, includexml=False)
    else:
        r = utils.get_config(dbcon, '/' + path, version)
    if r is None:
        flask.abort(404)
    return flask.Response(json.dumps(r), mimetype='application/json')


@app.route('/buildfinalxml', methods=['POST'])
@default_configurator_error_response
def make_full_xml():
    data = flask.request.json
    r = utils.build_final_from_xml(
        dbcon, path=data['path'], xml=data['xml'],
        executive=data['executive'], version=data['version'])
    return flask.Response(r, mimetype='text/xml')


@app.route('/buildxml', methods=['POST'])
@default_configurator_error_response
def make_easy_xml():
    """Take configuration fields, version from POST data and construct xml

    :returns: constructed xml configuration
    :rtype: flask.Response
    """
    data = flask.request.json
    r = utils.build_from_fields(
        dbcon, path=data['path'], fields=data['fields'],
        version=data['version'])
    return flask.Response(r, mimetype='text/xml')


@app.route('/submitfields', methods=['POST'])
@default_configurator_error_response
def submit_fields():
    data = flask.request.json
    comment = data['comment']
    v = data['version'] if ('version' in data) else None
    final = utils.build_final_from_fields(
        dbcon, path=data['path'], fields=data['fields'], version=v)
    if final:
        r = utils.populate_RSDB_with_DUCK(final, comment)
        if r[0]:
            return flask.Response('Successfully submitted', status=200)
        else:
            return flask.Response(r[1], status=500)
    else:
        return flask.Response('Failed to build final xml', status=500)


@app.route('/submitxml', methods=['POST'])
@default_configurator_error_response
def submit_xml():
    data = flask.request.json
    comment = data['comment']
    v = data['version'] if ('version' in data) else None
    final = utils.build_final_from_xml(
        dbcon, path=data['path'], xml=data['xml'],
        executive=data['executive'], version=v)
    if final:
        r = utils.populate_RSDB_with_DUCK(final, comment)
        if r[0]:
            return flask.Response('Successfully submitted', status=200)
        else:
            return flask.Response(r[1], status=500)
    else:
        return flask.Response('Failed to build final xml', status=500)


@app.route('/submitfull', methods=['POST'])
@default_configurator_error_response
def submit_full():
    data = flask.request.json
    try:
        comment = data['comment']
        final = data['xml']
    except ValueError:
        raise err.ConfiguratorUserError(
            '/submitfull request data must be {comment:..., xml:...}',
            details=data)
    r = utils.populate_RSDB_with_DUCK(final, comment)
    if r[0]:
        return flask.Response('Successfully submitted', status=200)
    else:
        return flask.Response(r[1], status=500)


@app.route('/fullxml/<path:path>')
@app.route('/fullxml/<path:path>/v=<int:version>')
@default_configurator_error_response
def get_full_xml(path, version=None):
    path = '/' + path
    final = utils.get_final_xml(dbcon, path=path, version=version)
    return flask.Response(final, mimetype='text/xml')


@app.route('/appv')
def get_appv():
    return flask.Response(str(appv), mimetype='application/json')


@app.route('/appv=<int:new_appv>', methods=['GET', 'PUT', 'POST'])
def set_appv(new_appv):
    global appv
    appv = new_appv
    return ('OK', 200)


if __name__ == '__main__':
    init()
    try:
        # app.run(host='0.0.0.0')
        app.run(host='0.0.0.0', debug=True, threaded=True)
    except BaseException as e:
        print e
        finalize()
