# TezID Contracts

These are the Tezos contracts used by [TezID](https://tezid.net).

They are written in [SmartPy](https://smartpy.io).

## Contracts

* Mainnet
  * Store - [KT1RaNxxgmVRXpyu927rbBFq835pnQk6cfvM](https://better-call.dev/mainnet/KT1RaNxxgmVRXpyu927rbBFq835pnQk6cfvM/)
  * Controller - [KT1KbV8dBrkFopgjcCc4qb2336fcGgTvRGRC](https://better-call.dev/mainnet/KT1KbV8dBrkFopgjcCc4qb2336fcGgTvRGRC/)
* Hangzhounet
  * Store - [KT1BfyfcaVhR8wThLgdsS4xricxMKvwkh1a1](https://better-call.dev/hangzhou2net/KT1BfyfcaVhR8wThLgdsS4xricxMKvwkh1a1/)
  * Controller - [KT1JstwQxj4sQVb9TDVG6Dr4jGjzxs5YQu7Y](https://better-call.dev/hangzhou2net/KT1JstwQxj4sQVb9TDVG6Dr4jGjzxs5YQu7Y/)

## Import

```
# Store v2.0.0 
Store = sp.io.import_script_from_url("https://tezid.infura-ipfs.io/ipfs/QmYbSGKoJiDve7WTmU452wxGivwx1Q2R9iNyNw3gyYBGhu")
# Controller v4.0.0 
Controller = sp.io.import_script_from_url("https://tezid.infura-ipfs.io/ipfs/Qma7XGTEjczQcjpAcC3cgV8j7VEWgwp442DnnLn2UyhgZS")
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

## Integration

See [here](tests/integrations.py) for integration examples.

```
spy kind all tests/integrations.py output --html
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
