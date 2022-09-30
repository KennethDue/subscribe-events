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
    #args["server"]="cvp.corp.lego.com"
 
    #cloud
    args["token"] = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJkaWQiOjY5NTkxNjIyNjczNTUwNjM0NzUsImRzbiI6IlRlbGVtZXRyeUJyb3dzZXIiLCJkc3QiOiJhY2NvdW50IiwiZXhwIjoxNjgyNTA1Njg1LCJpYXQiOjE2NjQzNjE2OTAsInNpZCI6ImIyODQ2YTQ1Mzc2N2Q0MGQ1YWM4YTk3YzI2Yjk1MWU1ZjczZGM2ZDI5OGMyMmJiODNiM2FhNTNlY2VlMmZjNWQtN1NhMTZpdVRfWlN4WU42UWxGMW00aWpfRnJEa0FRQ2cwcXF1R09HdyJ9.1AAod5E6yFI0QIgCLJrP58BhRZ6Fjl02EGOoNMtFBnVG9TU5rZFE1zrCTtPIBJ86twVA6bZ_rFULq6Mx_b73Tg"
    #local
    #args["token"] = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJkaWQiOjE2NjMsImRzbiI6IlRlbGVtZXRyeUJyb3dzZXIiLCJkc3QiOiJhY2NvdW50IiwiZXhwIjoxNjk1ODc4NjE2LCJpYXQiOjE2NjQ0MjkwMjYsInNpZCI6ImIzMDczMWU2ZjVmODYyN2YxYjYyNDY0NmE5YWVjNjUyYjdiODdjYWQyZWFlZmM4YzZlYmJhODY1YTZlMWZmMDktOVNWX3FlNjZJZF9ncXdwajZtWEp6UUE2UnNIdU9Bd2dkcFlNTVQwSyJ9.e0mOWOXl_rHdK9pu0uSs1fQ8rW4pdz-iQWoQ20yiH4dYpYcn9Qhv-zUQ4rmCYw6N4aExSbkXAwfUreKM-AyaoCTcVND5y0yKM5GxrQ_-MvkPpsSVmgPYM-lNGT3xecZDAiQDkonkj86zVjTQKwVaIkjosMJdkn8Dv3d_gqmpjS-4IJG6vYDVgT07fv4OH-I1RqnECa_Qp2UyFOpTiJckiJizT_7hFI-4_RHx4xl_kzsgIyg-nfxbvsXo4CgI_ZdAMXHnl46x5Lan1jJZsp0MonvlOsUKQMs_Ce-I_PyLlE0XPEFWEq31yFd1z2umfIh4LBrHYvNYu6VTJCIwVRQQgIGcph_uVzJXleYC1M1J3IXIHb-pL47toVO1Wx0NLeu-gT-HK6nsT7H_hjPLoR5CeDgxPlLrR6Q4OchO9QzHFXdgyh6_qE-Pu1Nva5NpL3uAUAVva7TJpAckotniMPomeigLUEOHwX6CmeuDk9EnXgzCvPDX99g9uTNz-iJnQD78ZnvmjmRCq3SawMuDVcBa4JpSs0TpzdYvo4r35OLG9aYSyv_8UD-2I1_fanv_yAMs3rfWx3vuTNqoMKpNB3Y81iGtgdYQAYiwX9ppJFoS71aExafmGIPklGsi4zu0omMe-Gq9aS94qw_WMwTeiJtVmhmOYizM67oGOvaBBd30FoE"
    
    args["cert"] = "www.cv-prod-euwest-2.arista.io.crt"
    #args["cert"] = "cvp.corp.lego.com.crt"

    subscribe(args)