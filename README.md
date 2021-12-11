# TezID Contracts

These are the Tezos contracts used by [TezID](https://tezid.net).

They are written in [SmartPy](https://smartpy.io).

## Contracts

* Mainnet
  * Store - [KT19gfem4ukWAgj4dZuCyQyKQe1WnSbR8DRp](https://better-call.dev/mainnet/KT19gfem4ukWAgj4dZuCyQyKQe1WnSbR8DRp/)
  * Controller - [KT1QSoZXBwCdARaJJU6ciptagM316TDWx4vr](https://better-call.dev/mainnet/KT1QSoZXBwCdARaJJU6ciptagM316TDWx4vr/)
* Hangzhounet
  * Store - [KT1DB16Rv92C8uAmuMqdhKziTTcXrVHrpqBt](https://better-call.dev/hangzhou2net/KT1DB16Rv92C8uAmuMqdhKziTTcXrVHrpqBt/)
  * Controller - [KT1LpPaw3F7hAW8HBzD9b5EggUYSYWRKe7G4](https://better-call.dev/hangzhou2net/KT1LpPaw3F7hAW8HBzD9b5EggUYSYWRKe7G4/)

## Init

```
./scripts/init-env.sh
source bin/activate
```

## Test

```
spy kind all tests/tezid.py output --html
```

## Originate

```
...
```

enjoy.
