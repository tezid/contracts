# TezID Contracts

These are the Tezos contracts used by [TezID](https://tezid.net).

They are written in [SmartPy](https://smartpy.io).

## Contracts

* Mainnet
  * Store - [KT1RaNxxgmVRXpyu927rbBFq835pnQk6cfvM](https://better-call.dev/mainnet/KT1RaNxxgmVRXpyu927rbBFq835pnQk6cfvM/)
  * Controller - [KT1KbV8dBrkFopgjcCc4qb2336fcGgTvRGRC](https://better-call.dev/mainnet/KT1KbV8dBrkFopgjcCc4qb2336fcGgTvRGRC/)
* Hangzhounet
  * Store - [KT1DB16Rv92C8uAmuMqdhKziTTcXrVHrpqBt](https://better-call.dev/hangzhou2net/KT1DB16Rv92C8uAmuMqdhKziTTcXrVHrpqBt/)
  * Controller - [KT1LpPaw3F7hAW8HBzD9b5EggUYSYWRKe7G4](https://better-call.dev/hangzhou2net/KT1LpPaw3F7hAW8HBzD9b5EggUYSYWRKe7G4/)

## Import

```
# Store v2.0.0 
Store = sp.io.import_script_from_url("https://ipfs.infura.io/ipfs/QmTTEnvDraWsqDr17utXw9KufeUE42JrdMxXcJSpcpc7tK")
# Controller v4.0.0 
Controller = sp.io.import_script_from_url("https://ipfs.infura.io/ipfs/QmTPz7pC826X7KfcQudw5X92WkUBpi2kJ7QdYVqBjiPpGP")
```

## Init

```
./scripts/init-env.sh
source bin/activate
```

## Test

```
spy kind all tests/tezid.py output --html
```

## Store API

### Entrypoints

```
getProofs
  parameters:
    address: TAddress
    callback_address: TAddress

  Get all proofs for `address` and transfer to `callback_address`.
```

### Views

```
getProofsForAddress
  parameters:
    address: TAdress
  result:
    TProofs (see contract/types.py)  

  Get all proofs for `address`.
```

enjoy.
