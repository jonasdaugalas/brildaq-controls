'''
Configurator server utilities.
'''
import ConfigParser
import sqlalchemy as sql
import xml.etree.ElementTree as ET
import requests
import re
import gzip
import datetime
import cStringIO
import subprocess
import tempfile
import javabinary
import configbuilder
import logging
import rcmsws
from easyconfig import easyconfigmap

log = logging.getLogger(__name__)


RE_GET_CONFIGS_PARSE = re.compile(
    '.*?fullpath=(.*?),')


def parse_service_map(path):
    '''
    parse service config ini file
    output: {servicealias:[protocol,user,passwd,descriptor]}
    '''
    result = {}
    parser = ConfigParser.SafeConfigParser()
    can_parse = parser.read(path)
    if (not can_parse):
        raise IOError('Cannot parse service config '
                      'file. authfile:{0}'.format(path))
    for s in parser.sections():
        protocol = parser.get(s, 'protocol')
        user = parser.get(s, 'user')
        passwd = parser.get(s, 'pwd')
        descriptor = parser.get(s, 'descriptor')
        result[s] = [protocol, user, passwd, descriptor]
    return result


def dbconnect(servicemap):
    dbuser = servicemap['online'][1]
    dbpass = servicemap['online'][2].decode('base64')
    dbdesc = servicemap['online'][3]
    dburl = 'oracle+cx_oracle://{0:s}:{1:s}@{2:s}'.format(
        dbuser, dbpass, dbdesc)
    engine = sql.create_engine(dburl)
    return engine.connect()


def get_configurations(dbcon):
    select = (
        'select res.urn, res.portnumber, hst.hostname, newest.version '
        'from CMS_LUMI_RS.CONFIGRESOURCES res,'
        ' CMS_LUMI_RS.CONFIGURATIONS cfg,'
        ' CMS_LUMI_RS.CONFIGHOSTS hst,'
        ' (select name, max(version) as version'
        ' from CMS_LUMI_RS.CONFIGURATIONS'
        ' where type=:cfgtype group by name) newest '
        'where cfg.name=newest.name and'
        ' cfg.version=newest.version and'
        ' res.configurationid=cfg.configurationid and'
        ' hst.configurationid=cfg.configurationid and'
        ' res.name=:resname')
    var = {'cfgtype': 'lightConfiguration',
           'resname': 'BrilDAQFunctionManager'}
    r = dbcon.execute(select, var).fetchall()
    r = {RE_GET_CONFIGS_PARSE.search(x[0]).group(1): {
        'urn': x[0],
        'port': x[1],
        'host': x[2],
        'version': x[3]}
         for x in r}
    return r


def get_running_configurations(dbcon):
    """Get dict of running configurations.

    :param dbcon:
    :returns: {path: config}, where config
      is {'URI': , 'version': , 'host': , 'port': }
    :rtype: dict or None

    """
    cfgs = rcmsws.get_running()
    print(cfgs)
    if not cfgs:
        return None
    resgids = [x['resGID'] for x in cfgs.values()]
    # (Jonas) Unable to pass list as parameter to oracle
    # Could potentially be security problem: non-parameterized query!
    resgids = [str(int(x)) for x in resgids]
    print(resgids)
    if not resgids:
        return None
    select = (
        'select res.configresourceid, cfg.version '
        'from CMS_LUMI_RS.CONFIGRESOURCES res,'
        ' CMS_LUMI_RS.CONFIGURATIONS cfg '
        'where res.configresourceid in (' + ','.join(resgids) +') and '
        'res.configurationid=cfg.configurationid')
    res = dbcon.execute(select).fetchall()
    for r in res:
        for v in cfgs.values():
            if int(r[0]) == v['resGID']:
                v['version'] = int(r[1])
    return cfgs


def get_versions(dbcon, path):
    select = (
        'select cfg.VERSION, cfg.MODIFICATIONDATE, cfg.VERSIONCOMMENT '
        'from CMS_LUMI_RS.CONFIGRESOURCES res, CMS_LUMI_RS.CONFIGURATIONS cfg '
        'where res.NAME=:resname '
        'and res.URN LIKE :path and '
        'res.CONFIGURATIONID=cfg.CONFIGURATIONID ')
    variables = {
        'resname': 'BrilDAQFunctionManager',
        'path': '%' + path + ',%'}
    r = dbcon.execute(select, variables).fetchall()
    if not r:
        return None
    r = [(x[0],
          (x[1] - datetime.datetime(1970, 1, 1)).total_seconds()*1000,
          x[2])
         for x in r]
    r.sort(key=lambda x:x[1], reverse=True)
    return r


def get_parsed_groupblob(dbcon, path, version):
    select = (
        'select res.GROUPBLOB '
        'from CMS_LUMI_RS.CONFIGRESOURCES res, CMS_LUMI_RS.CONFIGURATIONS cfg '
        'where res.NAME=:resname '
        'and res.URN LIKE :path and '
        'res.CONFIGURATIONID=cfg.CONFIGURATIONID ')
    variables = {
        'resname': 'BrilDAQFunctionManager',
        'path': '%' + path + ',%'}
    if version is None:
        select += 'ORDER BY cfg.VERSION DESC'
    else:
        select += 'and cfg.VERSION=:cfgversion'
        variables['cfgversion'] = version
    r = dbcon.execute(select, variables).fetchone()
    if r is None:
        return None
    r = r[0]
    fobj = cStringIO.StringIO(r)
    gzf = gzip.GzipFile('dummy', 'rb', 9, fobj)
    return javabinary.parse(gzf)


def get_config_xml(dbcon, path, version):
    group = get_parsed_groupblob(dbcon, path, version)
    if not group:
        return None
    configxml =  group[0]['childrenResources']['data'][0]['configFile']
    return configxml


def get_config(dbcon, path, version):
    easyconfig = None
    if path in easyconfigmap:
        easyconfig = easyconfigmap[path]
    group = get_parsed_groupblob(dbcon, path, version)
    xml = group[0]['childrenResources']['data'][0]['configFile']
    if not xml:
        return None
    result = {'xml': xml}
    result['fields'] = parse_fields(easyconfig, xml) if easyconfig else None
    result['executive'] = configbuilder.get_executive(group)
    return result


def parse_fields(easyconfig, xml):
    ns = easyconfig['namespaces']
    root = ET.fromstring(xml)
    for field in easyconfig['fields']:
        node = root.find(field['xpath'], ns)
        if field['type'] in ('Integer', 'unsignedInt'):
            field['value'] = int(node.text)
        elif field['type'] == 'commaSeparatedString':
            field['value'] = node.text.split(',')
        else:
            field['value'] = node.text
    return easyconfig['fields']


def build_final_xml(dbcon, path, xml, version=None):
    group = get_parsed_groupblob(dbcon, path, version)
    final = configbuilder.build_final(path, xml, group)
    return final


def populate_RSDB_with_DUCK(xml, comment=None):
    with tempfile.NamedTemporaryFile(mode='w') as f:
        f.write(xml)
        f.flush()
        cmd = ['java', '-jar', 'duck.jar', f.name]
        if comment:
            cmd += ['-c', str(comment)]
        log.debug("Subprocess: {}".format(' '.join(cmd)))
        out = subprocess.check_output(cmd, cwd='tools')
        if 'ERROR' in out:
            skip = out.find('Continueing...')
            if skip < 0:
                return False, ""
            out = out[(skip+15):]
            return False, 'duck.jar failed:' + out
        return True, "OK"
