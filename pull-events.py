import time
import google.protobuf.wrappers_pb2
import grpc
from arista.event.v1 import models, services
import requests
import json

# setup credentials as channelCredentials


CV_HOST = "cvp.corp.lego.com"
CV_API_PORT = "443"
USERNAME = "dk10kebrd"
PASSWORD = "-2scg-Dm6ej-BqN."


r = requests.post('https://' + CV_HOST + '/cvpservice/login/authenticate.do',auth=(USERNAME, PASSWORD),verify=False)
#print (json.dumps(r.json(),indent=4))
channelCredentials = grpc.ssl_channel_credentials()
call_credentials = grpc.access_token_call_credentials(r.json()['sessionId'])
combined_credentials = grpc.composite_channel_credentials(channelCredentials, call_credentials)
channel = grpc.insecure_channel(CV_HOST + ':' + CV_API_PORT, combined_credentials)

#print (channelCredentials)

#read certificate
#=argparse.FileType('rb')
#cert = "cvp.corp.lego.com.crt".read()
#channelCreds = grpc.ssl_channel_credentials(root_certificates=cert)

#with grpc.secure_channel(CV_HOST, channelCredentials) as channel:
with grpc.insecure_channel(CV_HOST, channelCredentials) as channel:
    event_stub = services.EventServiceStub(channel)
    event_annotation_stub = services.EventAnnotationConfigServiceStub(channel)

    event_watch_request = services.EventStreamRequest(
        partial_eq_filter=[models.Event(severity=models.EVENT_SEVERITY_CRITICAL)],
    )
    for resp in event_stub.Subscribe(event_watch_request):
        print(f"Critical event {resp.title.value} raised at {resp.key.timestamp}")
        # send alert here via email, webhook, or incident reporting tool

        # then make a note on the event indicating an alert has been sent
        now_ms = int(time.time() * 1000)
        notes_to_set = {
            now_ms: models.EventNoteConfig(
                note=google.protobuf.wrappers_pb2.StringValue(
                    value="Administrator alerted",
                ),
            ),
        }
        annotation_config = models.EventAnnotationConfig(
            key=resp.key,
            notes=models.EventNotesConfig(
                notes=notes_to_set,
            ),
        )
        event_note_update = services.EventAnnotationConfigSetRequest(value=annotation_config)
        event_annotation_stub.Set(event_note_update)