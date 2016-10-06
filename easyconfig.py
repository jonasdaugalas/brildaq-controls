import os
import json
import StringIO
import re
import xml.etree.ElementTree as ET
import configurator_errors as err
import custom_logging


NS_SOAPENC = 'http://schemas.xmlsoap.org/soap/encoding/'
NS_XSI = 'http://www.w3.org/2001/XMLSchema-instance'

log = custom_logging.get_logger(__name__)
easyconfigmap = {}


with open('easyconfigmap.json', 'r') as f:
    parsed = json.load(f)

    for k, v in parsed.iteritems():
        path = os.path.join('easyconfig', v)
        log.info('Loading easyconfig for {}: {}'.format(k, path))
        with open(path, 'r') as ec:
            easyconfig = json.load(ec)
            easyconfigmap[k] = easyconfig


def get_easyconfig(path):
    """Raise ConfiguratorUserError if not found"""
    if path in easyconfigmap:
        return easyconfigmap[path]
    else:
        raise err.ConfiguratorUserError(
            'Could not find easyconfig for given configuration path',
            details='given path: {},\neasyconfigs exist for:{}'
            .format(path, str(easyconfigmap.keys())))


def parse_fields(configpath, xml):
    if configpath in easyconfigmap:
        easy = easyconfigmap[configpath]
    else:
        return None
    ns = easy['namespaces']
    root = ET.fromstring(xml)
    fields = []
    for field in easy['fields']:
        node = root.find(field['xpath'], ns)

        # check if multiple values are the same
        if 'multiple' in field and field['multiple']:
            nodes = root.findall(field['xpath'], ns)
            for node2 in nodes:
                if node2.text != node.text:
                    raise ValueError('Field {} has flag "multiple" and values'
                                     'are different e.g. {}; {}'.format(
                                         field['name'], node.text, node2.text))

        f = {'name': field['name'], 'type': field['type']}
        if f['type'] in ('integer', 'Integer', 'unsignedInt'):
            f['value'] = int(node.text)
        elif f['type'] == 'float':
            f['value'] = float(node.text)
        elif f['type'] == 'commaSeparatedString':
            t = node.text
            f['value'] = str(t).split(',') if t is not None else []
        elif f['type'] == 'stringArray':
            f['value'] = _parse_string_array(node)
        elif f['type'] == 'stringMap':
            f['value'] = _parse_string_map(node)
        else:
            f['value'] = node.text

        if 'multiple' in field:
            f['multiple'] = field['multiple']
        if 'hideInOverview' in field:
            f['hideInOverview'] = field['hideInOverview']
        if 'typeahead' in field:
            f['typeahead'] = field['typeahead']
        if 'help' in field:
            f['help'] = field['help']

        fields.append(f)
    return fields


def update_xml_fields(path, xml, fields):
    easy = get_easyconfig(path)
    _register_xml_nsprefixes(xml)
    root = ET.fromstring(xml)
    for field in fields:
        multi = field['multiple'] if 'multiple' in field else False
        log.debug(field)
        try:
            field['xpath'] = [f['xpath'] for f in easy['fields']
                              if f['name'] == field['name']][0]
        except IndexError:
            raise err.ConfiguratorUserError(
                'Could not find predefined field with this name',
                details=field)
        _modify_xml_value(
            root, field['xpath'], field['type'], field['value'],
            easy['namespaces'], multi)
    # log.debug(ET.tostring(root, encoding='UTF-8'))
    return ET.tostring(root, encoding='UTF-8')


def _parse_string_array(node):
    log.debug('Parsing string array')
    log.debug(ET.tostring(node))
    result = []
    for e in node:
        result.append((_drop_ns(e.tag), e.text))
    log.debug('Parsed:{}'.format(result))
    return result


def _set_string_array(node, val):
    log.debug('Setting string array')
    log.debug(ET.tostring(node))
    log.debug(val)
    ns = _only_ns(node.tag)
    log.debug('clearing')
    node.clear()
    pos = 0
    for v in val:
        newe = ET.SubElement(node, ns + str(v[0]))
        newe.text = str(v[1]) if v[1] is not None else ''
        newe.set(_encurl(NS_XSI) + 'type', 'xsd:string')
        newe.set(_encurl(NS_SOAPENC) + 'position', '[{}]'.format(str(pos)))
        pos += 1

    node.set(_encurl(NS_XSI) + 'type', 'soapenc:Array')
    node.set(_encurl(NS_SOAPENC) + 'array-Type',
             'xsd:ur-type[{}]'.format(str(pos)))  # pos is now length
    log.debug('parsed')
    log.debug(ET.tostring(node))
    return node


def _parse_string_map(node):
    log.debug('Parsing string map')
    log.debug(ET.tostring(node))
    result = {}
    for e in node:
        result[_drop_ns(e.tag)] = e.text
    log.debug('Parsed:{}'.format(result))
    return result


def _set_string_map(node, newmap):
    log.debug('Setting string map')
    log.debug(ET.tostring(node))
    log.debug(newmap)
    ns = _only_ns(node.tag)
    log.debug('clearing')
    node.clear()
    for (k, v) in newmap.items():
        newe = ET.SubElement(node, ns + k)
        newe.text = str(v) if v is not None else ''
        newe.set(_encurl(NS_XSI) + 'type', 'xsd:string')

    node.set(_encurl(NS_XSI) + 'type', 'soapenc:struct')
    log.debug('parsed')
    log.debug(ET.tostring(node))
    return node


def _only_ns(tagname):
    return str(tagname)[:str(tagname).rfind('}')+1]


def _drop_ns(tagname):
    return str(tagname)[str(tagname).rfind('}')+1:]


def _encurl(string):
    return '{' + str(string) + '}'


def _register_xml_nsprefixes(xml):
    source = StringIO.StringIO(xml)
    events = ("end", "start-ns", "end-ns")
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


def _modify_xml_value(root, xpath, dtype, val, ns, multi):
    if multi:
        nodes = root.findall(xpath, ns)
    else:
        nodes = [root.find(xpath, ns)]
    for node in nodes:
        log.debug(node.attrib)
        if dtype in ('integer', 'Integer', 'unsignedInt'):
            node.text = str(int(val))
        elif dtype == 'float':
            node.text = str(float(val))
        elif dtype == 'commaSeparatedString':
            node.text = ','.join(
                map((lambda x: x if x is not None else ''), val))
        elif dtype == 'stringArray':
            _set_string_array(node, val)
        elif dtype == 'stringMap':
            _set_string_map(node, val)
        else:
            node.text = str(val)
