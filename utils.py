'''
Configurator server utilities.
'''
import ConfigParser
import sqlalchemy as sql
import requests
import re
import gzip
import datetime
import cStringIO
import subprocess
import tempfile
import javabinary
import configbuilder


GET_RUNNING_CONF_URL = 'http://cmsrc-lumi.cms:46000/rcms/services/FMLifeCycle'
GET_RUNNING_CONF_SOAP_XML = '<?xml version="1.0" encoding="UTF-8"?><soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><ns1:getRunningConfigurations xsi:nil="true" xmlns:ns1="urn:FMLifeCycle"/></soap:Body></soap:Envelope>'
RUNNING_CONF_SOAP_RESPONSE_RE = re.compile(
    r'<multiRef .*?<directoryFullPath.*?>(.+?)<.*?<resourceGroupID.*?>([0-9]+)<', flags=re.DOTALL)


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


def get_running_configurations():
    headers = {'SOAPAction': ''}
    r = requests.post(GET_RUNNING_CONF_URL, headers=headers,
                      data=GET_RUNNING_CONF_SOAP_XML)
    if (r.status_code == requests.codes.ok):
        print(r.text)
        ## match: (path, id)
        matches = re.findall(RUNNING_CONF_SOAP_RESPONSE_RE, r.text)
        matches = [(x[0], int(x[1])) for x in matches]
        return matches
    else:
        return[]


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


def build_final_xml(dbcon, path, xml, version=None):
    group = get_parsed_groupblob(dbcon, path, version)
    final = configbuilder.build_final(path, xml, group)
    return final


def populate_RSDB_with_DUCK(xml, comment=None):
    with tempfile.NamedTemporaryFile(mode='w') as f:
        print(f.name)
        f.write(xml)
        f.flush()
        cmd = ['java', '-jar', 'duck.jar', f.name]
        if comment:
            cmd += ['-c', str(comment)]
        print("Subprocess: {}".format(' '.join(cmd)))
        out = subprocess.check_output(cmd, cwd='tools')
        if 'ERROR' in out:
            skip = out.find('Continueing...')
            print(skip)
            if skip < 0:
                return False, ""
            out = out[(skip+15):]
            return False, 'duck.jar failed:' + out
        return True, "OK"
