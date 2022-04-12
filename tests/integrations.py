import os
import smartpy as sp

cwd = os.getcwd()
Types = sp.io.import_script_from_url("file://%s/contracts/types.py" % cwd)
Store = sp.io.import_script_from_url("file://%s/contracts/store.py" % cwd)
Controller = sp.io.import_script_from_url("file://%s/contracts/controller.py" % cwd)
TezIDTests = sp.io.import_script_from_url("file://%s/tests/tezid.py" % cwd)

one_year_in_seconds = 31556926
proof_register_time = 1637752889

class AirDrop(sp.Contract):
  def __init__(self, tezidStore, requiredProofs):
    self.init(
      tezidStore = tezidStore,
      requiredProofs = requiredProofs,
      signups = {},
      participants = {}
    )

  def check_proofs(self, proofs):
    sp.set_type(proofs, Types.TProofs)
    validProofs = sp.local("validProofs", [])
    sp.for requiredProof in self.data.requiredProofs:
      sp.if proofs.contains(requiredProof):
        sp.if proofs[requiredProof].verified:
          diff = sp.now - proofs[requiredProof].register_date
          # Less than 1 year
          sp.if diff <= one_year_in_seconds: 
            validProofs.value.push(requiredProof)
    valid = sp.len(self.data.requiredProofs) == sp.len(validProofs.value)
    sp.if ~valid:
      sp.failwith('Invalid TezID proofs')
      

  @sp.entry_point
  def register_callback(self, address, proofs):
      sp.if sp.sender != self.data.tezidStore:
        sp.failwith('Only TezID can call register_callback')
      sp.set_type(address, sp.TAddress)
      sp.set_type(proofs, Types.TProofs)
      sp.if self.data.signups.contains(address) == False:
        sp.failwith('Address has not signed up')
      self.check_proofs(proofs)
      del self.data.signups[address]
      self.data.participants[address] = True

  @sp.entry_point
  def signup_callback(self):
      self.data.signups[sp.sender] = True
      callback_address = sp.self_entry_point_address(entry_point = 'register_callback')
      c = sp.contract(Types.TGetProofsRequestPayload, self.data.tezidStore, entry_point="getProofs").open_some()
      sp.transfer(sp.record(address=sp.sender, callback_address=callback_address), sp.mutez(0), c)

  @sp.entry_point
  def signup_direct(self):
      proofs = sp.view('getProofsForAddress', self.data.tezidStore, sp.sender, t=Types.TProofs).open_some('Invalid view')
      self.check_proofs(proofs)
      self.data.participants[sp.sender] = True

@sp.add_target(name="Call getProofs from other contract", kind=TezIDTests.allKind)
def test():
  admin = sp.test_account("admin")
  user1 = sp.test_account("User1")
  user2 = sp.test_account("User2")
  user3 = sp.test_account("User3")

  scenario = sp.test_scenario()
  store, ctrl = TezIDTests.init(admin, scenario)
  ico = AirDrop(store.address, ["email","phone"])
  scenario += ico

  ## A user with the correct valid proofs can register as participant
  #
  scenario += ctrl.registerProof('email').run(sender = user1, amount = sp.tez(5))
  scenario += ctrl.registerProof('phone').run(sender = user1, amount = sp.tez(5))
  scenario += ctrl.verifyProof(sp.record(address=user1.address, prooftype='email')).run(sender = admin)
  scenario += ctrl.verifyProof(sp.record(address=user1.address, prooftype='phone')).run(sender = admin)
  scenario += ico.signup_callback().run(sender = user1)
  scenario.verify(ico.data.participants.contains(user1.address))

  ## A user without the correct valid proofs cannot register as participant
  #
  scenario += ctrl.registerProof('email').run(sender = user2, amount = sp.tez(5))
  scenario += ctrl.verifyProof(sp.record(address=user2.address, prooftype='email')).run(sender = admin)
  scenario += ico.signup_callback().run(sender=user2, valid=False, exception='Invalid TezID proofs')
  scenario.verify(ico.data.participants.contains(user2.address) == False)

  ## A user not registered on TezID cannot register as participant
  #
  scenario += ico.signup_callback().run(sender=user3, valid=False, exception='Invalid TezID proofs')
  scenario.verify(ico.data.participants.contains(user3.address) == False)

  ## Only TezID can call register endpoiint
  #
  scenario += ico.register_callback(sp.record(
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
    )).run(sender = user3, valid=False, exception="Only TezID can call register_callback")

  ## A user with outdated proofs cannot sign up 
  #
  scenario += ctrl.registerProof('email').run(sender=user3, amount=sp.tez(5), now=sp.timestamp(proof_register_time))
  scenario += ctrl.registerProof('phone').run(sender=user3, amount=sp.tez(5), now=sp.timestamp(proof_register_time))
  scenario += ctrl.verifyProof(sp.record(address=user3.address, prooftype='email')).run(sender=admin)
  scenario += ctrl.verifyProof(sp.record(address=user3.address, prooftype='phone')).run(sender=admin)
  scenario += ico.signup_callback().run(sender=user3, now=sp.timestamp(proof_register_time + one_year_in_seconds + 10), valid=False, exception="Invalid TezID proofs")
  scenario.verify(ico.data.participants.contains(user3.address) == False)
  scenario += ico.signup_callback().run(sender=user3, now=sp.timestamp(proof_register_time + one_year_in_seconds - 10))
  scenario.verify(ico.data.participants.contains(user3.address) == True)

@sp.add_target(name="Call getProofsForAddress from other contract", kind=TezIDTests.allKind)
def test():
  admin = sp.test_account("admin")
  user1 = sp.test_account("User1")
  user2 = sp.test_account("User2")
  user3 = sp.test_account("User3")

  scenario = sp.test_scenario()
  store, ctrl = TezIDTests.init(admin, scenario)
  ico = AirDrop(store.address, ["email","phone"])
  scenario += ico

  ## Users with valid proofs can sign up usign signup_direct
  # 
  scenario += ctrl.registerProof('email').run(sender = user1, amount = sp.tez(5))
  scenario += ctrl.registerProof('phone').run(sender = user1, amount = sp.tez(5))
  scenario += ctrl.verifyProof(sp.record(address=user1.address, prooftype='email')).run(sender = admin)
  scenario += ctrl.verifyProof(sp.record(address=user1.address, prooftype='phone')).run(sender = admin)
  scenario += ico.signup_direct().run(sender = user1)
  scenario.verify(ico.data.participants.contains(user1.address))

  ## A user with outdated proofs cannot sign up 
  #
  scenario += ctrl.registerProof('email').run(sender=user3, amount=sp.tez(5), now=sp.timestamp(proof_register_time))
  scenario += ctrl.registerProof('phone').run(sender=user3, amount=sp.tez(5), now=sp.timestamp(proof_register_time))
  scenario += ctrl.verifyProof(sp.record(address=user3.address, prooftype='email')).run(sender=admin)
  scenario += ctrl.verifyProof(sp.record(address=user3.address, prooftype='phone')).run(sender=admin)
  scenario += ico.signup_direct().run(sender=user3, now=sp.timestamp(proof_register_time + one_year_in_seconds + 10), valid=False, exception="Invalid TezID proofs")
  scenario.verify(ico.data.participants.contains(user3.address) == False)
  scenario += ico.signup_direct().run(sender=user3, now=sp.timestamp(proof_register_time + one_year_in_seconds - 10))
  scenario.verify(ico.data.participants.contains(user3.address) == True)
