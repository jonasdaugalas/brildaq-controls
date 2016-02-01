def build_final(fullpath, xml, group):
    service = build_service(group)
    executive = build_executive(group, xml)
    fm = build_fm(group, executive, service)
    tpl = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<Configuration '
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'user="{user}" path="{path}">{fm}</Configuration>')
    fullpath = fullpath.split('/')
    user = fullpath[1]
    path = '/'.join(fullpath[2:])
    return tpl.format(user=user, path=path, fm=fm)


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


def build_service(group):
    tpl = ('<Service name="{name}" hostname="{host}" port="{port}" '
           'urn="{urn}" qualifiedResourceType="{qrt}" />')
    data = group[0]['childrenResources']['data'][1]
    name = data['name']
    qrt = data['qualifiedResourceType']
    uri = data['uri']['string'][7:]       # drop 'http://'
    host = uri.split(':')[0]
    urn = '/' + uri.split('/')[1]
    port = uri.split('/')[0].split(':')[1]
    return tpl.format(name=name, host=host, port=port, urn=urn, qrt=qrt)


def build_executive(group, xml):
    tpl = ('<XdaqExecutive hostname="{host}" port="{port}" urn="{urn}" '
           'qualifiedResourceType="{qrt}" role="{role}" instance="{inst}" '
           'logURL="{logurl}" logLevel="{loglevel}" pathToExecutive="{path}" '
           'unixUser="{unixuser}" environmentString="{envstr}">'
           '<configFile>{xml}</configFile></XdaqExecutive>')
    data = group[0]['childrenResources']['data'][0]
    uri = data['uri']['string'][7:]       # drop 'http://'
    host = uri.split(':')[0]
    urn = '/' + uri.split('/')[1]
    port = uri.split('/')[0].split(':')[1]
    logurl = data['logURL']['string']
    xml = unxmlify(xml)
    return tpl.format(
        host=host, port=port, urn=urn, qrt=data['qualifiedResourceType'],
        role=data['role'], inst=data['instance'], logurl=logurl,
        loglevel=data['logLevel'], path=data['pathToExecutive'],
        unixuser=data['unixUser'], envstr=data['environmentString'], xml=xml)


def unxmlify(xml):
    r = xml.replace('<','&lt;')
    r = r.replace('>','&gt;')
    return r
