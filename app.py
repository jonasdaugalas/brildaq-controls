import functools
import json
import flask
import utils
import re
import time
import rcmsws
import config
import configurator_errors as err
import custom_logging


# prepare logging
log = custom_logging.get_logger(__name__)

# module attributes
dbcon = None
# static_folder - hardcoded, for dev only
app = flask.Flask(__name__, static_folder='client', static_url_path='')


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
        return flask.Response('Use POST method. Request body: json array '
                              'of configuration URIs (string)', status=405)
    data = flask.request.json
    r = rcmsws.get_states(data)
    return flask.Response(json.dumps(r), mimetype='application/json')


@app.route('/send/<string:command>', methods=['POST'])
@default_configurator_error_response
def send_command(command):
    data = flask.request.json
    return ('', 200) if rcmsws.send_command(command, data) else flask.abort(400)


@app.route('/create', methods=['POST'])
@default_configurator_error_response
def create_fm():
    data = flask.request.json
    return ('', 200) if rcmsws.create(data) else flask.abort(400)


@app.route('/destroy', methods=['POST'])
@default_configurator_error_response
def destroy_fm():
    data = flask.request.json
    return ('', 200) if rcmsws.destroy(data) else flask.abort(400)


@app.route('/history/<path:path>')
@default_configurator_error_response
def get_versions(path):
    r = utils.get_versions(dbcon, '/' + path)
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


@app.route('/config/<path:path>')
@app.route('/config/<path:path>/v=<int:version>')
@default_configurator_error_response
def get_config(path, version=None):
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
    final = utils.build_final_from_fields(
        dbcon, path=data['path'], fields=data['fields'],
        version=data['version'])
    if final:
        r = utils.populate_RSDB_with_DUCK(final, comment)
        if r[0]:
            return flask.Response('Successfully submitted', status=200)
        else :
            return flask.Response(r[1], status=500)
    else:
        return flask.Response('Failed to build final xml', status=500)


@app.route('/submitxml', methods=['POST'])
@default_configurator_error_response
def submit_xml():
    data = flask.request.json
    comment = data['comment']
    final = utils.build_final_from_xml(
        dbcon, path=data['path'], xml=data['xml'],
        executive=data['executive'], version=data['version'])
    if final:
        r = utils.populate_RSDB_with_DUCK(final, comment)
        if r[0]:
            return flask.Response('Successfully submitted', status=200)
        else :
            return flask.Response(r[1], status=500)
    else:
        return flask.Response('Failed to build final xml', status=500)


if __name__ == '__main__':
    init()
    try:
        # app.run(host='0.0.0.0')
        app.run(host='0.0.0.0', debug=True, threaded=True)
    except BaseException as e:
        print e
        finalize()
