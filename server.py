import json
import flask
import utils
import re
import time


dbcon = None
config = None
# static_url_path: static_base
app = flask.Flask(__name__, static_folder='client', static_url_path='')


def init():
    global config
    with open('config.json', 'r') as f:
        config = json.load(f)
    servicemap = utils.parse_service_map(config['authfile'])
    global dbcon
    dbcon = utils.dbconnect(servicemap)


def finalize():
    print('finalizing...')
    dbcon.close()


# route: /static_base/app_base
@app.route('/gui')
@app.route('/gui/')
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


@app.route('/configurations/')
@app.route('/configurations')
def get_configurations(path=None):
    ## would be nice to also get CONFIGRESOURCEID but it depends on
    ## CONFIGHOSTID.. So we identify configurations only by path
    select = ('select URN from CMS_LUMI_RS.CONFIGRESOURCES '
              'where name=:fmname GROUP BY URN')
    r = dbcon.execute(select, {'fmname': 'BrilDAQFunctionManager'}).fetchall()
    r = [re.search('=(.*?)(?:,|$)', x[0]).group(1) for x in r]
    return flask.Response(json.dumps(r), mimetype='application/json')


@app.route('/running/')
@app.route('/running')
def get_running():
    r = json.dumps(utils.get_running_configurations())
    return flask.Response(r, mimetype='application/json')


@app.route('/history/<path:path>')
def get_versions(path):
    r = utils.get_versions(dbcon, '/' + path)
    if r is None:
        flask.abort(404)
    return flask.Response(json.dumps(r), mimetype='application/json')


@app.route('/configxml/<path:path>')
@app.route('/configxml/<path:path>/v=<int:version>')
def get_config_xml(path, version=None):
    r = utils.get_config_xml(dbcon, '/' + path, version)
    if r is None:
        flask.abort(404)
    return flask.Response(r, mimetype='text/xml')


@app.route('/buildfinalxml', methods=['POST'])
def make_full_xml():
    data = flask.request.json
    r = utils.build_final_xml(dbcon, data['path'], data['xml'], data['version'])
    return flask.Response(r, mimetype='text/xml')


@app.route('/submitxml', methods=['POST'])
def submit_xml():
    data = flask.request.json
    comment = data['comment']
    final = utils.build_final_xml(dbcon, data['path'], data['xml'],
                                  data['version'])
    if final:
        r = utils.populate_RSDB_with_DUCK(final, comment)
        if r[0]:
            return flask.Response("Successfully submitted", status=201)
        else:
            return flask.Response(r[1], status=500)
    else:
        return flask.Response('Failed to build final xml', status=500)


if __name__ == '__main__':
    init()
    try:
        app.run(host='0.0.0.0')
        # app.run(host='0.0.0.0', debug=True)
    except e:
        print e
    finalize()
