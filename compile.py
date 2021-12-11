import smartpy as sp
import json
import os
env = os.environ

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
  "authors": ["asbjornenge <asbjorn@tezid.net>"]
}
TezIDControllerMetadata = {
  "name": "TezID Controller",
  "description": "Controller for TezID",
  "version": "3.0.0",
  "homepage": "https://tezid.net",
  "authors": ["asbjornenge <asbjorn@tezid.net>"]
}

sp.add_compilation_target("store", Store.TezIDStore(
    admin, 
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
        "content": sp.utils.bytes_of_string('{"name": "TezID Controller"}')
      }
    )
  )
)
