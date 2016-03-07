import re
import requests
import custom_logging
import config as CONFIG
import configurator_errors as err


log = custom_logging.get_logger(__name__)

FMLIFECYCLE_URL = '/rcms/services/FMLifeCycle'
COMMANDSERVICE_URL = '/rcms/services/CommandService'

TPL_SOAP_ENVELOPE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<soap:Envelope '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
    'xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" '
    'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
    'soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" '
    'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
    '<soap:Body>{body}</soap:Body></soap:Envelope>')

TPL_GET_STATE = (
    '<ns1:getState xmlns:ns1="urn:FMCommand">'
    '<uriPath xsi:type="soapenc:Array">'
    '<uriPath xsi:type="soapenc:string">{uri}</uriPath>'
    '</uriPath></ns1:getState>')

TPL_COMMAND = (
    '<ns1:execute xmlns:ns1="urn:FMCommand"><uriPath xsi:type="soapenc:Array">'
    '<uriPath xsi:type="soapenc:string">{uri}</uriPath></uriPath>'
    '<commandBean xsi:type="ns1:CommandBean">'
    '<commandString xsi:type="soapenc:string">{cmd}</commandString>'
    '</commandBean></ns1:execute>')

TPL_DESTROY = (
    '<ns1:destroy xmlns:ns1="urn:FMLifeCycle">'
    '<uriPath xsi:type="soapenc:Array">'
    '<uriPath xsi:type="soapenc:string">{uri}</uriPath></uriPath>'
    '</ns1:destroy>')

TPL_CREATE = (
    '<ns1:create xmlns:ns1="urn:FMLifeCycle">'
    '<uriPath xsi:type="soapenc:Array">'
    '<uriPath xsi:type="soapenc:string">{uri}</uriPath></uriPath>'
    '</ns1:create>')

TPL_GET_RUNNING = (
    '<ns1:getRunningConfigurations '
    'xsi:nil="true" xmlns:ns1="urn:FMLifeCycle"/>')

RE_GET_RUNNING_PARSE = re.compile(
    r'<multiRef .*?<URI .*?>(.+?)<.*?<directoryFullPath.*?>(.+?)<.*?<resourceGroupID .*?>(.+?)<', flags=re.DOTALL)

RE_GET_CREATED_PARSE = re.compile(
    r'<multiRef .*?<directoryFullPath.*?>(.+?)<.*?'
    '<resourceGroupID.*?>([0-9]+)<', flags=re.DOTALL)

RE_GET_STATE_PARSE = re.compile(
    r'<stateString .*?>(.+?)</stateString>', flags=re.DOTALL)


def post_soap_body(url, body):
    request = TPL_SOAP_ENVELOPE.format(body=body)
    headers = {'SOAPAction': ''}
    resp = requests.post(url, headers=headers, data=request)
    return resp


def is_ok(resp):
    return resp.status_code == requests.codes.ok


def get_service_from_uri(uri):
    return uri[7:].split('/')[0]


def get_running(owner=None):
    """Return running (created) configurations."""
    result = {}
    for key in CONFIG.owners:
        if owner is not None and key != owner:
            continue
        for service in CONFIG.owners[owner]['allowed_fm_locations']:
            url = 'http://' + service + FMLIFECYCLE_URL
            try:
                # ConnectionError
                resp = post_soap_body(url, TPL_GET_RUNNING)
                if not is_ok(resp):
                    raise requests.exceptions.RequestException(resp.text)
                matches = RE_GET_RUNNING_PARSE.findall(resp.text)
                if matches:
                    matches = {
                        x[1]: {
                            'URI': x[0],
                            'resGID': int(x[2])}
                        for x in matches}
                    result.update(matches)
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.RequestException) as e:
                log.exception(e)
                raise err.ConfiguratorInternalError(
                    'Failed to get running configurations',
                    details=(str(url) + '\n' + str(e.message)))
    return result


def get_states(uris):
    """Return state for each uri in uris list."""
    if not uris:
        return {}
    result = {}
    some_good = False
    for uri in uris:
        body = TPL_GET_STATE.format(uri=uri)
        service = get_service_from_uri(uri)
        url = 'http://' + service + COMMANDSERVICE_URL
        try:
            resp = post_soap_body(url, body)
            if is_ok(resp):
                found = RE_GET_STATE_PARSE.search(resp.text)
                result[uri] = found.group(1) if found else None
                if found:
                    some_good = True
            else:
                raise requests.exceptions.RequestException(resp.text)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.RequestException) as e:
            result[uri] =  None
    if not some_good:
        log.error("Failed to get states for all uris: %s", uris)
        raise err.ConfiguratorInternalError(
            'Failed to get states for all uris', details=uris)
    return result


def send_command(command, uri):
    log.info('SEND "%s" %s', command, uri)
    body = TPL_COMMAND.format(uri=uri, cmd=command)
    service = SERVICE_OWNERS[get_ownwer(uri)]
    resp = post_soap_body(service + COMMANDSERVICE_URL, body)
    if is_ok(resp):
        log.info('SUCCESS "%s" %s', command, uri)
        return True
    else:
        log.info('FAIL "%s" %s', command, uri)


def turn_on(uri):
    return send_command('TurnON', uri)


def turn_off(uri):
    return send_command('TurnOFF', uri)


def reset(uri):
    return send_command('Reset', uri)


def create(uri):
    log.info('CREATE %s', uri)
    body = TPL_CREATE.format(uri=uri)
    service = SERVICE_OWNERS[get_ownwer(uri)]
    resp = post_soap_body(service + FMLIFECYCLE_URL, body)
    if is_ok(resp):
        log.info('CREATED %s', uri)
        return True
    else:
        log.info('FAILED to CREATE %s', uri)


def destroy(uri):
    log.info('DESTROY %s', uri)
    body = TPL_DESTROY.format(uri=uri)
    service = SERVICE_OWNERS[get_ownwer(uri)]
    resp = post_soap_body(service + FMLIFECYCLE_URL, body)
    if is_ok(resp):
        log.info('DESTROYED %s', uri)
        return True
    else:
        log.info('FAILED to DESTROY %s', uri)
