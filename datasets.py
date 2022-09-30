import json
import grpc
import datetime

# import the events models and services
from arista.event.v1 import models
from arista.event.v1 import services

RPC_TIMEOUT = 300000  # in seconds
SEVERITIES = ["UNSPECIFIED","INFO", "WARNING", "ERROR", "CRITICAL"]

targetDataset = "analytics"
path = ["DatasetInfo", "Devices"]
# No filtering done on keys, accept all
keys = []
ProtoBufQuery = CreateQuery([(path, keys)], targetDataset)
with GRPCClient("www.cv-prod-euwest-2.arista.io:9900") as client:
     for notifBatch in client.Get([query]):
         for notif in notifBatch["notifications"]:
             # Get timestamp for all update here with notif.Timestamp
             PrettyPrint(notif["updates"])