import re
import requests
import logging

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

FMLIFECYCLE_URL = 'http://cmsrc-lumi.cms:46000/rcms/services/FMLifeCycle'
COMMANDSERVICE_URL = 'http://cmsrc-lumi.cms:46000/rcms/services/CommandService'

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


class RequestFailed(Exception):
    def __init__(self, message, status_code):
        super(RequestFailed, self).__init__(message)
        self.status_code = status_code


def post_soap_body(url, body):
    request = TPL_SOAP_ENVELOPE.format(body=body)
    headers = {'SOAPAction': ''}
    resp = requests.post(url, headers=headers, data=request)
    return resp


def is_ok(resp):
    return resp.status_code == requests.codes.ok


def get_running():
    """Return running (created) configurations."""
    resp = post_soap_body(FMLIFECYCLE_URL, TPL_GET_RUNNING)
    if is_ok(resp):
        ## match: (path, id)
        matches = RE_GET_RUNNING_PARSE.findall(resp.text)
        if matches:
            matches = {
                x[1]: {
                    'URI': x[0], 'resGID':
                    int(x[2])}
                for x in matches}
        return matches or {}
    else:
        log.error("Failed get running configurations: %s", resp.text)
        raise RequestFailed(resp.text, resp.status_code)


def get_states(uris):
    """Return state for each uri in uris list."""
    result = {}
    some_good = False
    for uri in uris:
        body = TPL_GET_STATE.format(uri=uri)
        resp = post_soap_body(COMMANDSERVICE_URL, body)
        if is_ok(resp):
            found = RE_GET_STATE_PARSE.search(resp.text)
            result[uri] = found.group(1) if found else None
            some_good = True if found else False
        else:
            result[uri] =  None
    if not some_good:
        log.error("Failed get running configurations: %s", resp.text)
        raise RequestFailed(resp.text, resp.status_code)
    return result


def send_command(command, uri):
    log.info('SEND "%s" %s', command, uri)
    body = TPL_COMMAND.format(uri=uri, cmd=command)
    resp = post_soap_body(COMMANDSERVICE_URL, body)
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
