GOOD_EXECUTIVE_KEYS =[
    'qualifiedResourceType', 'role', 'instance', 'logLevel',
    'pathToExecutive', 'unixUser', 'environmentString']

def get_executive(group):
    data = group[0]['childrenResources']['data'][0]
    uri = data['uri']['string'][7:]       # drop 'http://'
    e = {
        'host': uri.split(':')[0],
        'urn': '/' + uri.split('/')[1],
        'port': int(uri.split('/')[0].split(':')[1]),
        'logURL': data['logURL']['string']
    }
    for key in GOOD_EXECUTIVE_KEYS:
        e[key] = data[key]

    return e


def build_final(fullpath, xml, group, executive=None):
    service_xml = build_service(group, executive)
    executive_xml = build_executive(group, xml, executive)
    fm_xml = build_fm(group, executive_xml, service_xml)
    tpl = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<Configuration '
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'user="{user}" path="{path}">{fm}</Configuration>')
    fullpath = fullpath.split('/')
    user = fullpath[1]
    path = '/'.join(fullpath[2:])
    return tpl.format(user=user, path=path, fm=fm_xml)


def build_fm(group, executive, service):
    tpl = ('<FunctionManager name="{name}" hostname="{host}" port="{port}" '
           'qualifiedResourceType="{qrt}" sourceURL="{srcurl}" '
           'className="{cls}">{executive}{service}</FunctionManager>')
    data = group[0]['thisResource']
    srcurld = data['sourceURL']
    host = srcurld['host']
    port = srcurld['port']
    srcurl = (srcurld['protocol'] + '://' +
              srcurld['authority'] + srcurld['file'])
    qrt = data['qualifiedResourceType']
    return tpl.format(
        name=data['name'], host=host, port=port, qrt=qrt, srcurl=srcurl,
        cls=data['className'], executive=executive, service=service)


def build_service(group, executive):
    tpl = ('<Service name="{name}" hostname="{host}" port="{port}" '
           'urn="{urn}" qualifiedResourceType="{qrt}" />')
    data = group[0]['childrenResources']['data'][1]
    name = data['name']
    qrt = data['qualifiedResourceType']
    uri = data['uri']['string'][7:]       # drop 'http://'
    host = uri.split(':')[0]
    if executive:
        if executive['host']:
            # overwrite host
            host = executive['host']
    urn = '/' + uri.split('/')[1]
    port = uri.split('/')[0].split(':')[1]
    return tpl.format(name=name, host=host, port=port, urn=urn, qrt=qrt)


def build_executive(group, xml, executive=None):
    tpl = ('<XdaqExecutive hostname="{host}" port="{port}" urn="{urn}" '
           'qualifiedResourceType="{qualifiedResourceType}" role="{role}" '
           'instance="{instance}" logURL="{logURL}" logLevel="{logLevel}" '
           'pathToExecutive="{pathToExecutive}" unixUser="{unixUser}" '
           'environmentString="{environmentString}">'
           '<configFile>{xml}</configFile></XdaqExecutive>')
    e = get_executive(group)
    if executive:
        e.update(executive)
    xml = unxmlify(xml)
    return tpl.format(xml=xml, **e)


def unxmlify(xml):
    r = xml.replace('<','&lt;')
    r = r.replace('>','&gt;')
    return r
