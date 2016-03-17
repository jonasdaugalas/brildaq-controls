'''
Configure server utilities.
'''
import os
import ConfigParser
import sqlalchemy as sql
import xml.etree.ElementTree as ET
import requests
import re
import gzip
import datetime
import cStringIO
import StringIO
import subprocess
import tempfile
import custom_logging
import javabinary
import configbuilder
import rcmsws
import configurator_errors as err
import config as CONFIG
from easyconfig import easyconfigmap

log = custom_logging.get_logger(__name__)


RE_GET_CONFIGS_PARSE = re.compile('.*?fullpath=(.*?),')


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


def path2uri(path):
    owner = path.split('/')[1]
    if owner not in CONFIG.owners:
        raise err.ConfiguratorUserError('Unknown owner for path.', details=path)
    uri = ('http://' + CONFIG.owners[owner]['rcms_location'] +
           '/urn:rcms-fm:fullpath=' + path +
           ',group=BrilDAQFunctionManager,owner=' + owner)
    return uri


def get_owners(dbcon):
    select = (
        'select user_name '
        'from CMS_LUMI_RS.CONFIGRESOURCES res, CMS_LUMI_RS.CONFIGURATIONS cfg '
        'where cfg.configurationid=res.configurationid'
        ' and res.name=:resname group by user_name')
    var = {'resname': 'BrilDAQFunctionManager'}
    r = dbcon.execute(select, var).fetchall()
    return [str(x[0]) for x in r]


def get_configurations(dbcon, owner=None):
    var = {'cfgtype': 'lightConfiguration',
           'resname': 'BrilDAQFunctionManager'}
    if owner is not None:
        var['owner'] = owner
        ownerclause = ' and cfg.user_name=:owner '
    else:
        ownerclause = ''
    select = (
        'select res.urn, cfg.user_name, res.portnumber,'
        ' hst.hostname, newest.version '
        'from CMS_LUMI_RS.CONFIGRESOURCES res,'
        ' CMS_LUMI_RS.CONFIGURATIONS cfg,'
        ' CMS_LUMI_RS.CONFIGHOSTS hst,'
        ' (select name, parent, max(version) as version'
        ' from CMS_LUMI_RS.CONFIGURATIONS'
        ' where type=:cfgtype group by name, parent) newest '
        'where cfg.name=newest.name and'
        ' cfg.parent=newest.parent and'
        ' cfg.version=newest.version and'
        ' res.configurationid=cfg.configurationid and'
        ' hst.configurationid=cfg.configurationid and'
        ' res.name=:resname {}'.format(ownerclause))
    result = dbcon.execute(select, var).fetchall()
    result = {RE_GET_CONFIGS_PARSE.search(x[0]).group(1): {
        'urn': x[0],
        'owner': x[1],
        'port': x[2],
        'host': x[3],
        'version': x[4]} for x in result}

    for r in result.itervalues():
        _set_owner_host_port_flags(
            r, r['owner'], r['host'] + ':' + str(r['port']))

    return result


def _set_owner_host_port_flags(obj, owner, fmhostport):
    if owner not in CONFIG.owners:
        _set_flag(obj, 'danger', "Unconfigured owner: '{}\'".format(owner))
    elif fmhostport != CONFIG.owners[owner]['rcms_location']:
        _set_flag(obj, 'danger',
                  "Owner '{}' is not allowed on {}"
                  .format(owner, fmhostport))


def _set_flag(cfgmeta, flagtype, flagname, desc=''):
    flagtype = flagtype.upper()
    if 'flags' not in cfgmeta:
        cfgmeta['flags'] = {}
    if flagtype not in cfgmeta['flags']:
        cfgmeta['flags'][flagtype] = {}
    cfgmeta['flags'][flagtype][flagname] = str(desc)


def get_running_configurations(dbcon, owner=None):
    """Get dict of running configurations.

    :param dbcon:
    :returns: {path: config}, where config
      is {'URI': , 'version': , 'host': , 'port': }
    :rtype: dict or None

    """
    cfgs = rcmsws.get_running(owner)
    if not cfgs:
        return {}
    resgids = [x['resGID'] for x in cfgs.values()]
    # (Jonas) Unable to pass list as parameter to oracle
    # Could potentially be security problem: non-parameterized query!
    resgids = [str(int(x)) for x in resgids]
    if not resgids:
        return {}
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


def get_versions(dbcon, path, limit, bellow):
    select = (
        'select cfg.VERSION, cfg.MODIFICATIONDATE, cfg.VERSIONCOMMENT '
        'from CMS_LUMI_RS.CONFIGRESOURCES res, CMS_LUMI_RS.CONFIGURATIONS cfg '
        'where res.NAME=:resname '
        'and res.URN LIKE :path and '
        'res.CONFIGURATIONID=cfg.CONFIGURATIONID {bellow} '
        'order by cfg.version desc')
    variables = {
        'resname': 'BrilDAQFunctionManager',
        'path': '%' + path + ',%'}
    log.debug(bellow)
    if bellow:
        select = select.format(bellow=' and version < :BELLOW')
        variables['BELLOW'] = (bellow or 0)
    else:
        select = select.format(bellow='')
    if limit:
        select = 'select * from (' + select + ') where ROWNUM <= :LIMIT'
        variables['LIMIT'] = (limit or 0)
    log.debug(select)
    r = dbcon.execute(select, variables).fetchall()
    if not r:
        return None
    r = [(x[0],
          (x[1] - datetime.datetime(1970, 1, 1)).total_seconds()*1000,
          x[2])
         for x in r]
    r.sort(key=lambda x:x[1], reverse=True)
    return r


def _get_parsed_groupblob(dbcon, path, version):
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
        raise err.ConfiguratorUserError(
            'Configuration groupblob not found by path and version in RS DB.',
            details={'path': path, 'version': version})
    r = r[0]
    fobj = cStringIO.StringIO(r)
    gzf = gzip.GzipFile('dummy', 'rb', 9, fobj)
    return javabinary.parse(gzf)


def get_config_xml(dbcon, path, version):
    group = _get_parsed_groupblob(dbcon, path, version)
    return _get_config_xml_from_groupblob(group)


def _get_config_xml_from_groupblob(group):
    return group[0]['childrenResources']['data'][0]['configFile']


def get_config(dbcon, path, version):
    easyconfig = None
    if path in easyconfigmap:
        easyconfig = easyconfigmap[path]
    group = _get_parsed_groupblob(dbcon, path, version)
    xml = group[0]['childrenResources']['data'][0]['configFile']
    if not xml:
        return None
    result = {'xml': xml}
    owner = path.split('/')[1]
    fmhostport = group[0]['thisResource']['uri']['string'][7:].split('/')[0]
    _set_owner_host_port_flags(result, owner, fmhostport)
    result['fields'] = _parse_fields(easyconfig, xml) if easyconfig else None
    result['executive'] = configbuilder.get_executive(group)
    return result


def _parse_fields(easyconfig, xml):
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
    fields = [{'name': f['name'], 'type': f['type'], 'value': f['value']}
              for f in easyconfig['fields']]
    return fields


def _check_hosts_and_ports(executive, xml):
    """Check if needed hosts and ports match between executive and xml.

    :param executive: dict executive fields (important: 'host', 'port')
    :param xml: str xdaq configuration xml
    :returns: True if (executive is None) or
      (executive.host=context.host=endpoint.host and
      executive.port=context.port and context.port!=endpoint.port)
      else raise ConfiguratorUserError
    :rtype: Boolean

    """
    log.debug('In "_check_hosts_and_ports"')
    if executive is None:
        log.debug('executive is None - all good')
        return True
    root = ET.fromstring(xml)
    context = root.find('.//{' + CONFIG.xdaqxmlnamespace + '}Context')
    contexturl = context.attrib['url'].split(':')
    contexthost = contexturl[-2][2:] # drop two slashes after 'http:'
    contextport = int(contexturl[-1])
    endpoint = context.find('.//{' + CONFIG.xdaqxmlnamespace + '}Endpoint')
    endpointhost = endpoint.attrib['hostname']
    endpointport = int(endpoint.attrib['port'])
    log.debug(
        'executive.host: {}, executive.port: {}, context.host: {}, '
        'context.port: {}, endpoint.host: {}, endpoint.port: {}'.format(
            executive['host'], executive['port'], contexthost, contextport,
            endpointhost, endpointport))
    if executive['host'] == contexthost and executive['host'] == endpointhost:
        if executive['port'] == contextport and contextport != endpointport:
            return True
    raise err.ConfiguratorUserError(
        'Failed hosts&ports check',
        details=(
            'Some of the following violated:\n'
            '1) Executive.host ({}) = Context.host ({}) = Endpoint.host ({})\n'
            '2) Executive.port ({}) = Context.port ({})\n'
            '3) Context.port ({}) != Endpoint.port ({})').format(
                executive['host'], contexthost, endpointhost,
                executive['port'], contextport, contextport,  endpointport))


def get_final_xml(dbcon, path, version=None):
    group = _get_parsed_groupblob(dbcon, path, version)
    xml = _get_config_xml_from_groupblob(group)
    final = configbuilder.build_final(path, xml, group)
    return final


def build_final_from_xml(dbcon, path, xml, executive=None, version=None):
    _check_hosts_and_ports(executive, xml)
    group = _get_parsed_groupblob(dbcon, path, version)
    _check_danger_flags(path, group) # raises configurator user error
    final = configbuilder.build_final(path, xml, group, executive)
    return final


def build_final_from_fields(dbcon, path, fields, version=None):
    group = _get_parsed_groupblob(dbcon, path, version)
    _check_danger_flags(path, group) # raises configurator user error
    easyconfig = _get_easyconfig(path)
    xml = _get_config_xml_from_groupblob(group)
    xml = _modify_xml_by_fields(xml, fields, easyconfig)
    final = configbuilder.build_final(path, xml, group)
    return final


def _check_danger_flags(path, group):
    owner = path.split('/')[1]
    fmhostport = group[0]['thisResource']['sourceURL']['authority']
    tmp = {}
    _set_owner_host_port_flags(tmp, owner, fmhostport)
    if tmp:
        raise err.ConfiguratorUserError('Configuration has DANGER flags.',
                                        details=tmp)


def build_from_fields(dbcon, path, fields, version=None):
    """Construct xml for given path from modification fields and version.

    :param dbcon:
    :param path: config path
    :param fields: [{'name': ..., 'value': ..., 'type': ...}]
    :param version: config version (int)
    :returns: constructed xml
    :rtype: str
    """
    easyconfig = _get_easyconfig(path)
    xml = get_config_xml(dbcon, path, version)
    return _modify_xml_by_fields(xml, fields, easyconfig)


def _get_easyconfig(path):
    if path in easyconfigmap:
        return easyconfigmap[path]
    else:
        raise err.ConfiguratorUserError(
            'Could not find easyconfig for given configuration path',
            details='given path: {},\neasyconfigs exist for:{}'
            .format(path, str(easyconfigmap.keys())))


def _modify_xml_by_fields(xml, fields, easyconfig):
    _register_xml_nsprefixes(xml)
    root = ET.fromstring(xml)
    for field in fields:
        log.debug(field)
        try:
            field['xpath'] = [f['xpath'] for f in easyconfig['fields']
                              if f['name'] == field['name']][0]
        except IndexError as e:
            raise err.ConfiguratorUserError(
                'Could not find predefined field with this name', details=field)
        _modify_xml_value(root, field['xpath'], field['type'],
                         field['value'], easyconfig['namespaces'])
    return ET.tostring(root, encoding='UTF-8')


def _register_xml_nsprefixes(xml):
    source = StringIO.StringIO(xml)
    events = ("end", "start-ns", "end-ns")
    counter = 0
    namespaces = []
    for event, elem in ET.iterparse(source, events=events):
        if event == "start-ns":
            if re.match('^ns[0-9]+$', elem[0]):
                namespaces.append(('', elem[1]))
            else:
                namespaces.append(elem)
    for ns in namespaces:
        if len(ns[0]) > 0:
            ET.register_namespace(ns[0], ns[1])
    return namespaces


def _modify_xml_value(root, xpath, dtype, val, ns):
    node = root.find(xpath, ns)
    if dtype in ('Integer', 'unsignedInt'):
        node.text = str(int(val))
    elif dtype == 'commaSeparatedString':
        node.text = ','.join(val)
    else:
        node.text = str(val)


def populate_RSDB_with_DUCK(xml, comment=None):
    with tempfile.NamedTemporaryFile(mode='w') as f:
        f.write(xml)
        f.flush()
        cmd = ['java', '-jar', 'duck.jar', f.name]
        if comment:
            cmd += ['-c', str(comment)]
        log.debug("Subprocess: {}".format(' '.join(cmd)))
        fdir = os.path.dirname(os.path.realpath(__file__))
        cwd = os.path.join(fdir, 'tools')
        log.debug('subprocess cwd: {}'.format(cwd))
        out = subprocess.check_output(cmd, cwd=cwd)
        log.debug('cwd: {}'.format(os.getcwd()))
        if 'ERROR' in out:
            log.debug('duck.jar output: {}'.format(out))
            skip = out.find('Continueing...')
            if skip < 0:
                return False, ""
            out = out[(skip+15):]
            return False, 'duck.jar failed:' + out
        return True, 'OK'
