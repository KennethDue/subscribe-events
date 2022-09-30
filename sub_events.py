# Copyright (c) 2020 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the COPYING file.

# Subscribing to CVP events
#
# Examples:
# 1) Subscribe to all events
#    python sub_events.py --server 10.83.12.79:443 --token-file token.txt \
#    --cert-file cvp.crt
# 2) Subscribe to only DEVICE_INTF_ERR_SMART events
#    python sub_events.py --server 10.83.12.79:443 --token-file token.txt \
#    --cert-file cvp.crt --event-type DEVICE_INTF_ERR_SMART
# 3) Subscribe to events with INFO severity
#    python sub_events.py --server 10.83.12.79:443 --token-file token.txt \
#    --cert-file cvp.crt --severity INFO

import json
import grpc
import datetime

# import the events models and services
from arista.event.v1 import models
from arista.event.v1 import services

RPC_TIMEOUT = 300000  # in seconds
SEVERITIES = ["UNSPECIFIED","INFO", "WARNING", "ERROR", "CRITICAL"]


def subscribe(args):

    callCreds = grpc.access_token_call_credentials(args["token"])

    # if using a self-signed certificate 
    if "cert" in args.keys():
        cert_file = open(args["cert"],'rb')

    if cert_file:
        cert = cert_file.read()
        channelCreds = grpc.ssl_channel_credentials(root_certificates=cert)
    else:
        # otherwise default to checking against CAs
        channelCreds = grpc.ssl_channel_credentials()

    connCreds = grpc.composite_channel_credentials(channelCreds, callCreds)

    # create a stream request
    subscribe = services.EventStreamRequest()

    # create a filter model
    event_filter = models.Event()

    #if "events" in args.keys():
    #    event_filter.event_type.value = args["events"]

    #if "severity" in args.keys():
        # enum with val 0 is always unset
        #event_filter.severity = SEVERITIES.index(args["severity"]) + 1  #  event_filter.severity = 0to4
    #event_filter.severity=1

    subscribe.partial_eq_filter.append(event_filter)
    
    # initialize a connection to the server using our connection settings (auth + TLS)
    with grpc.secure_channel(args["server"], connCreds) as channel:
        event_stub = services.EventServiceStub(channel)
        #for resp in event_stub.Subscribe(subscribe, timeout=RPC_TIMEOUT):
        for resp in event_stub.Subscribe(subscribe):  #no timeout
            #react here
            if resp.value.severity==0: # show that strange event
                print(resp.value)

            eventType = resp.value.event_type.value
            #if eventType!="DEVICE_INTF_ERR_SMART" and eventType!="LOW_DEVICE_DISK_SPACE" and eventType!="HIGH_INTF_OUT_DISCARDS" and eventType!="HIGH_INTF_IN_ERRS":  # do not show IFdown, Low disk, discards, errors
            print ("title:"+resp.value.title.value)
            print ("event type:"+resp.value.event_type.value)
            print ("severity : "+str(resp.value.severity))
            print ("description:"+resp.value.description.value)
            print ("timestamp: "+str(resp.value.key.timestamp.seconds)+" - "+datetime.datetime.fromtimestamp(resp.value.key.timestamp.seconds).strftime('%Y-%m-%d %H:%M:%S'))
            print ("event data:")
            dictionary_items = resp.value.data.data.items()
            for item in dictionary_items:
                print(item)
            print("-----\n")



if __name__ == '__main__':
    args ={}

    #args["severity"] = 4

    # read the file containing a session token to authenticate with
    args["server"]="www.cv-prod-euwest-2.arista.io"
    args["token"] = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJkaWQiOjY5NTkxNjIyNjczNTUwNjM0NzUsImRzbiI6IlRlbGVtZXRyeUJyb3dzZXIiLCJkc3QiOiJhY2NvdW50IiwiZXhwIjoxNjgyNTA1Njg1LCJpYXQiOjE2NjQzNjE2OTAsInNpZCI6ImIyODQ2YTQ1Mzc2N2Q0MGQ1YWM4YTk3YzI2Yjk1MWU1ZjczZGM2ZDI5OGMyMmJiODNiM2FhNTNlY2VlMmZjNWQtN1NhMTZpdVRfWlN4WU42UWxGMW00aWpfRnJEa0FRQ2cwcXF1R09HdyJ9.1AAod5E6yFI0QIgCLJrP58BhRZ6Fjl02EGOoNMtFBnVG9TU5rZFE1zrCTtPIBJ86twVA6bZ_rFULq6Mx_b73Tg"
    args["cert"] = "www.cv-prod-euwest-2.arista.io.crt"
  

    subscribe(args)