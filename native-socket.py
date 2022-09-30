#!/usr/bin/env python

'''Sample python program that allows you to subscribe to Arista Telemetry
Events and then send them to a third-party API
'''
import sys

# pylint: disable=W0613,C0103
import base64

#from Crypto.Hash import SHA256
import logging
from logging import handlers
import hashlib
import json
import random
import requests
import string
import websocket
import threading
import ssl
import dns.resolver
import time

VERSION_09 = '0.9.0'
VERSION_1 = '1.0.0'
SUBSCRIBE_CMD = 'subscribe'

AERIS_URL = '/aeris/v1/wrpc/'
EVENT_PATH = '/events/v1/allEvents'
DEVICES_PATH = '/DatasetInfo/EosSwitches'
cvp_url = "10.10.10.10"


class TelemetryWs(object):
    '''Class to handle connection methods required to get
    and subscribe to steaming data.
    '''
    def __init__(self, fabric):
        '''Initialize variabled and objects
        '''
        super(TelemetryWs, self).__init__()
        self.fabric=fabric
        self.initLogging()
        self.cvp_auth()
        aeris_url_with_auth = 'wss://%s%s' % (self.aerisIp, AERIS_URL)
        self.socket = websocket.WebSocketApp(aeris_url_with_auth,
                                             on_message=self.on_message,
                                             on_error=self.on_error,
                                             on_close=self.on_close,
                                             header={"Cookie: session_id="+self.sessionId })
        self.ping_token = self.make_token()
        self.ping_thread = None
        self.events_token = None
        self.events_thread = None
        self.device_names = {}
        self.device_token = None
        self.device_thread = None
        self.socket.on_open = self.on_run


    def cvp_auth(self,url):
       ''' Authenticate with CVP and save sessionId '''

      AUTH_URL = 'https://%s/cvpservice/login/authenticate.do' % url
      AUTH_USER=config[cvp]['user']
      AUTH_PASS=base64.b64decode('pass')
      payload = "{\r\n  \"userId\": \"%s\",\r\n  \"password\": \"%s\"\r\n}" % (AUTH_USER, AUTH_PASS)
      headers = {
          'content-type': "application/json",
          'cache-control': "no-cache",
          }
      response = requests.request("POST", AUTH_URL, data=payload, headers=headers, verify=False)
      if response.status_code == 200:
        jsondata = json.loads(response.text)
        sessionId = jsondata["sessionId"]
        print "string sessionId :"+str(sessionId)
        self.sessionId = sessionId
        self.aerisIp = str(a)
        return #Stop looping through A records, if we succeeded in authenticating.


    def on_run(self, *args):
        '''Methods to run when the ws connects
        '''
        self.start_ping()
        self.get_events()
        self.get_devices()

    def start_ping(self, *args):
        '''Begins a periodic ping to the ws server
        '''
        self.ping_thread = threading.Timer(5.0, self.start_ping)
        self.ping_thread.start()
        self.send_message('versions', self.ping_token, {}, VERSION_1)

    def send_message(self, command, token, args, version=VERSION_1):
        '''Formats a message to be send to Telemetry WS server
        '''
        #print '>>> Sending Message...'
        argName = 'args' if version == VERSION_09 else 'params'
        data = {
            'token': token,
            'command': command,
            argName: args,
            'version': version,
        }
        #print data
        self.socket.send(json.dumps(data))

    def on_close(self, *args):
        '''Run when ws closes. This will kill the ping thread
        '''
        self.logger.log(logging.INFO,"arista-cvp-events.py closing for fabric "+self.fabric+"...")
        self.ping_thread.cancel()
        print '### closed ###'

    @staticmethod
    def on_error(ws, error):
        '''Print websocket error'''
        print 'Error: %s' % error

    @staticmethod
    def make_token():
        '''Generate request token
        '''
        seed = ''.join(random.choice(string.ascii_uppercase + string.digits)
                       for _ in range(20))
#        token = SHA256.new(seed).hexdigest()[0:38]
        token = hashlib.sha256(seed).hexdigest()[0:38]
        #print token
        return token

    def on_message(self, ws, message):
        '''Handle message received from websocket.
           Based on token, we can identify if this is an event, deviceinfo or something else
        '''
        #print '<<< Receiving Message: %s' % message
        data = json.loads(message)
        if data['token'] == self.ping_token:
            ''' Do nothing '''
            #print 'Got pong'
        elif data['token'] == self.events_token:
            if data.get('result'):
                self.relay_event(data.get('result'))
            #print 'Got events data'
            #print data['result']
        elif data['token'] == self.devices_token:
            #print 'Got Devices Data'
            if data.get('result'):
                self.update_device_names(data.get('result'))
        else:
            print 'Got unexpected data for token:'+data['token']+' I know about device:'+self.devices_token+', events:'+self.events_token
            print data['result']

    def get_events(self):
        '''Subscribes to Telemetry events
        '''
        self.events_token = self.make_token()
        args = {'query': {'analytics': {EVENT_PATH: True}}}
        self.event_thread = threading.Thread(target=self.send_message,
                                     args=(SUBSCRIBE_CMD, self.events_token,
                                           args, VERSION_1))
        self.event_thread.start()

    def get_devices(self):
      '''Get and Subscribes to Telemetry device data
      We subscribe to get new updates. This script is expected to run for years, so RMA and new installations must be learned
      '''
      self.devices_token = self.make_token()
      args= {'query': {'analytics': {DEVICES_PATH: True}}}
      self.device_thread = threading.Thread(target=self.send_message,
                                          args=(SUBSCRIBE_CMD, self.devices_token,
                                                args, VERSION_1))
      self.device_thread.start()
              self.send_message('get', self.devices_token, args , VERSION_1)

          def update_device_names(self, events):
            ''' Handle device_name update and write information to dictionary
            '''
            #print json.dumps(events,sort_keys=True, indent=4, separators=(',', ': '))
            for event in events:
              #print "event"
              for notification in event.get('Notifications',[]):
                #print "notification"
                if all(key in notification.keys() for key in ['path','updates']):
                  if notification['path']==DEVICES_PATH:
                    #print "updates"
                    print notification['updates'].keys()
                    for key,val in notification['updates'].iteritems():
                      self.device_names[key]=val.get('value',{}).get('hostname',key)

    def relay_event(self, events):
        ''' Handle event and send data via syslog (temp print it)
        '''
        #print json.dumps(events,sort_keys=True, indent=4, separators=(',', ': '))
        for event in events:
          #print "event"
          if event.get('DeviceID')=='analytics':
            for notification in event.get('Notifications',[]):
              #print "notification"
              if all(key in notification.keys() for key in ['path','updates']):
                if notification['path']==EVENT_PATH:
                  #print "updates"
                  #print notification['updates'].keys()
                  if all(key in notification['updates'].keys() for key in ['data','description','eventType','severity','title']):
                    myTimeS,myTimeMS = divmod(notification['updates']['timestamp']['value'], 1000)
                    myTimeString='%s.%03d' % (time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(myTimeS)), myTimeMS)
                    print "Event:"
                    myEvent={'timestamp':notification['updates']['timestamp']['value'],
                             'time':myTimeString,
                             'severity':notification['updates']['severity']['value'],
                             'event':notification['updates']['eventType']['value'],
                             'description':notification['updates']['description']['value'],
                             'deviceSerial':notification['updates']['data']['value']['deviceId'],
                             'interface':notification['updates']['data']['value'].get('interfaceId',''),
                             'deviceName':self.device_names.get(notification['updates']['data']['value']['deviceId']) }
                    print json.dumps(myEvent,sort_keys=True, indent=4, separators=(',', ': '))
                    syslogMsg="CVP Event:%s,%s,%s,%s,%s,%s" % (myEvent['time'],myEvent['deviceName'],myEvent['interface'],myEvent['severity'],myEvent['event'],myEvent['description'])
                    self.logger.log(logging.INFO,syslogMsg)

if __name__ == "__main__":
    #websocket.enableTrace(True)
    logging.basicConfig()
    if len(sys.argv)==2:
      fabric=sys.argv[1]
      connection = TelemetryWs(fabric)
      connection.socket.run_forever(sslopt={'check_hostname': False, 'cert_reqs': ssl.CERT_NONE})
