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
    """
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

    scenario = sp.test_scenario()
    store = TezID.TezIDStore(admin.address, iids)
    scenario += store
