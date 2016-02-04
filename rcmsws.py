import re
import requests
import logging

log = logging.getLogger(__name__)

RCMS_FMLIFECYCLE_URL = 'http://cmsrc-lumi.cms:46000/rcms/services/FMLifeCycle'

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
    r'<multiRef .*?<directoryFullPath.*?>(.+?)<', flags=re.DOTALL)

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
    resp = post_soap_body(RCMS_FMLIFECYCLE_URL, TPL_GET_RUNNING)
    if is_ok(resp):
        ## match: (path, id)
        matches = RE_GET_RUNNING_PARSE.findall(resp.text)
        return matches
    else:
        log.error("Failed get running configurations: %s", resp.text)
        raise RequestFailed(resp.text, resp.status_code)
