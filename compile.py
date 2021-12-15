import smartpy as sp
import json
import os
from datetime import datetime, timezone
env = os.environ

def UTCTimestamp(datestring):
  dt = datetime.strptime(datestring, '%Y-%m-%dT%H:%M:%S')
  dt_utc = dt.replace(tzinfo=timezone.utc)
  return int(dt_utc.timestamp())

cwd = os.getcwd()
Store = sp.io.import_script_from_url("file://%s/contracts/store.py" % cwd)
Controller = sp.io.import_script_from_url("file://%s/contracts/controller.py" % cwd)
admin = sp.address(env['TEZID_ADMIN'])
store = sp.address(env['TEZID_STORE'])

TezIDStoreMetadata = {
  "name": "TezID Store",
  "description": "Datastore for TezID",
  "version": "2.0.0",
  "homepage": "https://tezid.net",
  "authors": ["asbjornenge <asbjorn@tezid.net>"],
  "interfaces": ["TZIP-016"]
}
TezIDControllerMetadata = {
  "name": "TezID Controller",
  "description": "Controller for TezID",
  "version": "4.0.0",
  "homepage": "https://tezid.net",
  "authors": ["asbjornenge <asbjorn@tezid.net>"],
  "interfaces": ["TZIP-016"]
}

sp.add_compilation_target("store", Store.TezIDStore(
    sp.set([admin]), 
    sp.big_map(),
    sp.big_map(
      {
        "": sp.utils.bytes_of_string("tezos-storage:content"),
        "content": sp.utils.bytes_of_string(json.dumps(TezIDStoreMetadata))
      }
    )
  )
)

sp.add_compilation_target("controller", Controller.TezIDController(
    admin, 
    store, 
    sp.big_map(
      {
        "": sp.utils.bytes_of_string("tezos-storage:content"),
        "content": sp.utils.bytes_of_string(json.dumps(TezIDControllerMetadata))
      }
    )
  )
)
