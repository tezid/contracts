import smartpy as sp

TezID = sp.io.import_stored_contract("TezID v2")

@sp.add_test(name = "We can prepopulate a store create")
def test():
    admin = sp.test_account("admin")

    """ EDO
    iids = sp.big_map({
        sp.address("tz1LzNPygNPtwdL9MkZu9BYXAFeNMVqT3Tk3"): {
            "email" : sp.record(
                register_date = sp.timestamp_from_utc(2021, 5, 5, 7, 22, 17),
                verified = True,
                meta = {}
            ),
            "phone" : sp.record(
                register_date = sp.timestamp_from_utc(2021, 4, 15, 13, 3, 19),
                verified = True,
                meta = {}
            )
        },
        sp.address("tz1UZZnrre9H7KzAufFVm7ubuJh5cCfjGwam"): {
            "email" : sp.record(
                register_date = sp.timestamp_from_utc(2021, 5, 20, 9, 49, 19),
                verified = True,
                meta = {}
            )
        },
        sp.address("tz1VN6niFJvTYckEqjhASEu5nc2CgLt65QEz"): {
            "email" : sp.record(
                register_date = sp.timestamp_from_utc(2021, 3, 31, 0, 0, 0),
                verified = False,
                meta = {}
            )
        },
        sp.address("tz1Wf3Ggf4WaqKGC6KxNDS4rs7ECFRUAjoSH"): {
            "email" : sp.record(
                register_date = sp.timestamp_from_utc(2021, 4, 16, 0, 0, 0),
                verified = False,
                meta = {}
            )
        },
        sp.address("tz1acr6qBRFsX7oTwh6nt3xpvoSZabs7FRrv"): {
            "email" : sp.record(
                register_date = sp.timestamp_from_utc(2021, 4, 6, 0, 0, 0),
                verified = True,
                meta = {}
            ),
            "phone" : sp.record(
                register_date = sp.timestamp_from_utc(2021, 4, 6, 0, 0, 0),
                verified = False,
                meta = {}
            )
        },
        sp.address("tz1cp2TFke4GdtSYVBtuTPfvawnemuaJwSno"): {
            "email" : sp.record(
                register_date = sp.timestamp_from_utc(2021, 3, 30, 0, 0, 0),
                verified = False,
                meta = {}
            )
        },
        sp.address("tz1fMq8JoDmQxknjWjXLw1JhfnJ7j4DSkjK2"): {
            "email" : sp.record(
                register_date = sp.timestamp_from_utc(2021, 3, 31, 0, 0, 0),
                verified = True,
                meta = {}
            )
        }
    })
    """
    
    """ Florence
    iids = sp.big_map({
        sp.address("tz1LzNPygNPtwdL9MkZu9BYXAFeNMVqT3Tk3"): {
            "email" : sp.record(
                register_date = sp.timestamp_from_utc(2021, 3, 29, 10, 23, 11),
                verified = True,
                meta = {}
            ),
            "phone" : sp.record(
                register_date = sp.timestamp_from_utc(2021, 3, 29, 10, 26, 11),
                verified = True,
                meta = {}
            )
        },
        sp.address("tz1VFf24FHGEYfYaR7f1Fu72ksov45SC1UXz"): {
            "email" : sp.record(
                register_date = sp.timestamp_from_utc(2021, 4, 8, 14, 10, 19),
                verified = False,
                meta = {}
            )
        },
        sp.address("tz1Wf3Ggf4WaqKGC6KxNDS4rs7ECFRUAjoSH"): {
            "email" : sp.record(
                register_date = sp.timestamp_from_utc(2021, 3, 29, 10, 47, 15),
                verified = True,
                meta = {}
            )
        },
        sp.address("tz1aW9v8Ka7UCuoGFWjzag9Fv599mLbWVSq9"): {
            "email" : sp.record(
                register_date = sp.timestamp_from_utc(2021, 4, 9, 11, 10, 15),
                verified = False,
                meta = {}
            )
        },
    })
    """
    
    """ Mainnet
    """
    iids = sp.big_map({
        sp.address("tz1PuipWs33aqS2KSG5k1qQtC6Dff1P1GBmM"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,20,23,56,20),
                verified = True,
                meta = {}
            ),
            "phone": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,21,0,48,20),
                verified = True,
                meta = {}
            ),
        },
        sp.address("tz1QBSiKTwj4KW9C63NwU7Ep4Heg8yyRaU76"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,3,31,12,55,3),
                verified = True,
                meta = {}
            ),
            "phone": sp.record(
                register_date = sp.timestamp_from_utc(2021,3,31,13,0,3),
                verified = False,
                meta = {}
            ),
        },
        sp.address("tz1QBu5mAvRc5GAZNpUUmSR6Ukc6TYZ99ao7"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,5,1,44,1),
                verified = False,
                meta = {}
            ),
            "phone": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,5,1,47,1),
                verified = False,
                meta = {}
            ),
        },
        sp.address("tz1TCg1w8A1onHWEXWw66FoVjVVUiX1zpqAR"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,5,7,10,1,1),
                verified = True,
                meta = {}
            ),
        },
        sp.address("tz1ThHmbYNh5yxEqD12d9SyMa2Erxu1PF1fR"): {
            "phone": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,7,21,50,59),
                verified = True,
                meta = {}
            ),
        },
        sp.address("tz1UZZnrre9H7KzAufFVm7ubuJh5cCfjGwam"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,3,29,13,5,44),
                verified = True,
                meta = {}
            ),
        },
        sp.address("tz1X8b2jEPjp8raxMvniYH8vwJmch2tP3YEQ"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,8,16,31,55),
                verified = False,
                meta = {}
            ),
        },
        sp.address("tz1X9EAdNxKVqf8szY4MBEw99sT96XdcNmg4"): {
            "phone": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,6,6,55,1),
                verified = True,
                meta = {}
            ),
        },
        sp.address("tz1Xtw4QseYemiFGrxUyVD3XCZeuou5nmoXp"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,9,4,24,35),
                verified = True,
                meta = {}
            ),
        },
        sp.address("tz1bkhCGUuA5bveCsMqXe9tEkopkZX3hiB9i"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,3,30,17,33,32),
                verified = False,
                meta = {}
            ),
        },
        sp.address("tz1ccChjQckbojW39Rd9U2z2oqe9m7wNeoLf"): {
            "phone": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,7,8,4,35),
                verified = True,
                meta = {}
            ),
        },
        sp.address("tz1chAZukD7QacpWDUJ33dGqeWFvknj5Xpj9"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,4,23,29,21),
                verified = True,
                meta = {}
            ),
            "phone": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,4,23,45,21),
                verified = True,
                meta = {}
            ),
        },
        sp.address("tz1dd2tmTJFRJh8ycLuZeMpKLquJYkMypu2Q"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,3,30,14,38,32),
                verified = True,
                meta = {}
            ),
        },
        sp.address("tz1enSmESCGkRYo2CtDYKhqUHFTAQkpXjYjg"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,5,31,17,54,58),
                verified = True,
                meta = {}
            ),
        },
        sp.address("tz1iAAJhH465Cf3BnsKQ744XHypQGY1v7Ps9"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,3,29,12,34,44),
                verified = True,
                meta = {}
            ),
            "phone": sp.record(
                register_date = sp.timestamp_from_utc(2021,3,31,10,50,3),
                verified = True,
                meta = {}
            ),
        },
        sp.address("tz1isUkFmwZvUqrBPLnfTn9hVqMcNzKCdCp3"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,8,4,37,19),
                verified = True,
                meta = {}
            ),
            "phone": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,8,4,27,19),
                verified = True,
                meta = {}
            ),
        },
        sp.address("tz2ALu8Jxf2SMgzSZaZEwfiJQbogpUDPStwz"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,5,30,6,6,58),
                verified = True,
                meta = {}
            ),
            "phone": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,8,22,11,35),
                verified = True,
                meta = {}
            ),
        },
        sp.address("tz2NPxZSAEKxoQjonv5uJKsEdt773Sk3dvx6"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,5,4,16,40,13),
                verified = True,
                meta = {}
            ),
            "phone": sp.record(
                register_date = sp.timestamp_from_utc(2021,5,4,16,46,13),
                verified = True,
                meta = {}
            ),
        },
        sp.address("tz2Tix6DQiAeunkSTSVqPmLFQEgFjCzqtzf9"): {
            "email": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,14,14,22,21),
                verified = False,
                meta = {}
            ),
            "phone": sp.record(
                register_date = sp.timestamp_from_utc(2021,4,14,14,40,21),
                verified = False,
                meta = {}
            ),
        },
    })


    scenario = sp.test_scenario()
    store = TezID.TezIDStore(admin.address, iids)
    scenario += store
