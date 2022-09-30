# subscribe to events, and listen for "SYSLOG_V2" in event.type
# used https://github.com/aristanetworks/cloudvision-python/blob/trunk/examples/resources/event/sub_events.py as inspiration

# the script will stop listning after a period (around 30 minutes??)
# the question is - can i send a keep-alive, to CVaaS and keep listening indefinetly  ???


import grpc
import datetime

# import the events models and services
from arista.event.v1 import models
from arista.event.v1 import services

#RPC_TIMEOUT = 300000  # in seconds
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

    subscribe.partial_eq_filter.append(event_filter)
    
    # initialize a connection to the server using our connection settings (auth + TLS)
    with grpc.secure_channel(args["server"], connCreds) as channel:
        event_stub = services.EventServiceStub(channel) #i am thinking that wihtout a timeout, the session will never end

        #for resp in event_stub.Subscribe(subscribe, timeout=RPC_TIMEOUT):  
        for resp in event_stub.Subscribe(subscribe):  #<---------- this is the timeout

            eventType = resp.value.event_type.value
            print ("event type: "+resp.value.event_type.value)
            
            if resp.value.severity==0: # show that strange event with severity 0
                print(resp)

            # react to to custom syslog messages here
            if eventType=="SYSLOG_V2":
                if resp.value.title.value=="new LLDP event": #this is where the provisioning takes place
                    #grab neighbor information from upstream device = resp.value.data.data["hostname"]
                    print ("start provisioning here!")
            
            # print all others, except those 'annoying' interface errors
            if eventType!="DEVICE_INTF_ERR_SMART" and eventType!="LOW_DEVICE_DISK_SPACE" and eventType!="HIGH_INTF_OUT_DISCARDS" and eventType!="HIGH_INTF_IN_ERRS":  # do not show IFdown, Low disk, discards, errors
                print ("title:"+resp.value.title.value)
                print ("severity: "+str(resp.value.severity))
                print ("description: "+resp.value.description.value)
                print ("timestamp: "+str(resp.value.key.timestamp.seconds)+" - "+datetime.datetime.fromtimestamp(resp.value.key.timestamp.seconds).strftime('%Y-%m-%d %H:%M:%S'))
                print ("event data:")
                dictionary_items = resp.value.data.data.items()
                for item in dictionary_items:
                    print(item)

            # just mention those 'annoying' interface errors
            if eventType=="DEVICE_INTF_ERR_SMART" or eventType=="HIGH_INTF_OUT_DISCARDS" or eventType=="HIGH_INTF_IN_ERRS":  # do not show IFdown, Low disk, discards, errors
                print ("interface errors")

            print ("time is now: "+datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            print("end of event -----\n")

if __name__ == '__main__':
    args ={}

    #args["severity"] = 4

    # read the file containing a session token to authenticate with
    args["server"]="www.cv-prod-euwest-2.arista.io"
    args["token"] = "xxxxx"
    args["cert"] = "xxxx.crt"
  

    subscribe(args)