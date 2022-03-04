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
Farm = sp.io.import_script_from_url("file://%s/contracts/farm.py" % cwd)
Store = sp.io.import_script_from_url("file://%s/contracts/store.py" % cwd)
Tokens = sp.io.import_script_from_url("file://%s/contracts/tokens.py" % cwd)
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
TezIDxFarmMetadata = {
  "name": "TezID xFarm",
  "description": "Farm for IDZ reward distribution",
  "version": "1.0.0",
  "homepage": "https://tezid.net",
  "authors": ["asbjornenge <asbjorn@tezid.net>"],
  "interfaces": ["TZIP-016"]
}
TezIDAOTokenMetadata = {
  "name": "TezIDAO Tokens",
  "description": "Tokens for TezID DAO and reward distribution",
  "version": "1.0.0",
  "homepage": "https://tezid.net",
  "authors": ["asbjornenge <asbjorn@tezid.net>"],
  "interfaces": ["TZIP-012","TZIP-016","TZIP-021"]
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

sp.add_compilation_target("tezidao-token", Tokens.FA2Token(
    Tokens.TezIDAO_TOKEN_config,
    admin = admin, 
    metadata = sp.big_map(
      {
        "": sp.utils.bytes_of_string("tezos-storage:content"),
        "content": sp.utils.bytes_of_string(json.dumps(TezIDAOTokenMetadata))
      }
    )
  )
)

sp.add_compilation_target("xfarm", Farm.TezIDForeverFarm(
    sp.set([admin]), 
    sp.big_map(
      {
        "": sp.utils.bytes_of_string("tezos-storage:content"),
        "content": sp.utils.bytes_of_string(json.dumps(TezIDxFarmMetadata))
      }
    )
  )
)
