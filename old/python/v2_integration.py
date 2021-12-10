import smartpy as sp

TezID = sp.io.import_stored_contract("TezID v2")

class AirDrop(sp.Contract):
    def __init__(self, tezidStore, requiredProofs):
      self.init(
        tezidStore = tezidStore,
        requiredProofs = requiredProofs,
        signups = {},
        participants = {}
      )

    @sp.entry_point
    def register(self, address, proofs):
        sp.if sp.sender != self.data.tezidStore:
            sp.failwith('Only TezID can register')
        sp.set_type(address, sp.TAddress)
        sp.set_type(proofs, TezID.TProofs)
        sp.if self.data.signups.contains(address) == False:
            sp.failwith('Address has not signed up')
        validProofs = sp.local("validProofs", [])
        sp.for requiredProof in self.data.requiredProofs:
            sp.if proofs.contains(requiredProof):
                sp.if proofs[requiredProof].verified:
                    validProofs.value.push(requiredProof)
        sp.if sp.len(self.data.requiredProofs) == sp.len(validProofs.value):
            self.data.participants[address] = True
        del self.data.signups[address]

    @sp.entry_point
    def signup(self):
        self.data.signups[sp.sender] = True
        callback_address = sp.self_entry_point_address(entry_point = 'register')
        c = sp.contract(TezID.TGetProofsRequestPayload, self.data.tezidStore, entry_point="getProofs").open_some()
        sp.transfer(sp.record(address=sp.sender, callback_address=callback_address), sp.mutez(0), c)

@sp.add_test(name = "Call TezID from other contract")
def test():
  admin = sp.test_account("admin")
  user1 = sp.test_account("User1")
  user2 = sp.test_account("User2")
  user3 = sp.test_account("User3")

  scenario = sp.test_scenario()
  store, ctrl = TezID.initTests(admin, scenario)
  ico = AirDrop(store.address, ["email","phone"])
  scenario += ico

  ## A user with the correct valid proofs can register as participant
  #
  scenario += ctrl.registerProof('email').run(sender = user1, amount = sp.tez(5))
  scenario += ctrl.registerProof('phone').run(sender = user1, amount = sp.tez(5))
  scenario += ctrl.verifyProof(sp.record(address=user1.address, prooftype='email')).run(sender = admin)
  scenario += ctrl.verifyProof(sp.record(address=user1.address, prooftype='phone')).run(sender = admin)
  scenario += ico.signup().run(sender = user1)
  scenario.verify(ico.data.participants.contains(user1.address))

  ## A user without the correct valid proofs cannot register as participant
  #
  scenario += ctrl.registerProof('email').run(sender = user2, amount = sp.tez(5))
  scenario += ctrl.verifyProof(sp.record(address=user2.address, prooftype='email')).run(sender = admin)
  scenario += ico.signup().run(sender = user2)
  scenario.verify(ico.data.participants.contains(user2.address) == False)

  ## A user not registered on TezID cannot register as participant
  #
  scenario += ico.signup().run(sender = user3, valid=False)
  scenario.verify(ico.data.participants.contains(user3.address) == False)

  ## Only TezID can call register endpoiint
  #
  scenario += ico.register(sp.record(
        address = user3.address,
        proofs = {
            "email": sp.record(
                register_date = sp.timestamp(0),
                verified = True,
                meta = {}
            ),
            "phone": sp.record(
                register_date = sp.timestamp(0),
                verified = True,
                meta = {}
            )
        }
    )).run(sender = user3, valid=False)
