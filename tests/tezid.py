import os
import smartpy as sp

cwd = os.getcwd()
Store = sp.io.import_script_from_url("file://%s/contracts/store.py" % cwd)
Controller = sp.io.import_script_from_url("file://%s/contracts/controller.py" % cwd)

## Tests
#

allKind = 'all'

def init(admin, scenario):
  store = Store.TezIDStore(
    admin.address, 
    sp.big_map(), 
    sp.big_map(
      {
        "": sp.utils.bytes_of_string("tezos-storage:content"),
        "content": sp.utils.bytes_of_string('{"name": "TezID Store"}')
      }
    )
  )
  scenario += store
  ctrl = Controller.TezIDController(
    admin.address, 
    store.address, 
    sp.big_map(
      {
        "": sp.utils.bytes_of_string("tezos-storage:content"),
        "content": sp.utils.bytes_of_string('{"name": "TezID Controller"}')
      }
    )
  )
  scenario += ctrl
  scenario += store.setAdmin(ctrl.address).run(sender = admin)
  return store, ctrl

@sp.add_target(name = "Register proof", kind=allKind)
def test():
  admin = sp.test_account("admin")
  user = sp.test_account("User")

  scenario = sp.test_scenario()
  store, ctrl = init(admin, scenario)

  ## A user can self-register a unverified proof
  #
  scenario += ctrl.registerProof('phone').run(sender=user, amount=sp.tez(5))
  scenario.verify(store.data.identities.contains(user.address))
  scenario.verify(store.data.identities[user.address]['phone'].verified == False)

  ## Too low fee results in failure
  #
  scenario += ctrl.registerProof('phone').run(sender=user, amount=sp.tez(4), valid=False, exception='Amount too low')
  
@sp.add_target(name = "Verify proof", kind=allKind)
def test():
  admin = sp.test_account("admin")
  user = sp.test_account("User")
  cost = sp.tez(5)

  scenario = sp.test_scenario()
  store, ctrl = init(admin, scenario)
  scenario += ctrl.registerProof('email').run(sender = user, amount = sp.tez(5))
  scenario += ctrl.registerProof('phone').run(sender = user, amount = sp.tez(5))

  ## Admin can verify a proof
  #
  scenario += ctrl.verifyProof(sp.record(address=user.address,prooftype='email')).run(sender = admin)
  scenario.verify(store.data.identities[user.address]['email'].verified == True)

  ## User cannot verify a proof
  #
  scenario += ctrl.verifyProof(sp.record(address=user.address, prooftype='phone')).run(sender = user, valid = False)
  scenario.verify(store.data.identities[user.address]['phone'].verified == False)
  
  ## Admin cannot verif a proof that is not added by a user first
  #
  scenario += ctrl.verifyProof(sp.record(address=user.address,prooftype='twitter')).run(sender = admin, valid = False)
    
@sp.add_target(name = "Remove proof", kind=allKind)
def test():
  admin = sp.test_account("admin")
  user = sp.test_account("User")

  scenario = sp.test_scenario()
  store, ctrl = init(admin, scenario)
  scenario += ctrl.registerProof('email').run(sender = user, amount = sp.tez(5))
  scenario += ctrl.registerProof('phone').run(sender = user, amount = sp.tez(5))
  scenario += ctrl.verifyProof(sp.record(address=user.address,prooftype='email')).run(sender = admin)
  scenario += ctrl.verifyProof(sp.record(address=user.address,prooftype='phone')).run(sender = admin)

  ## A user cannot remove a proof
  #
  to_remove = sp.record(prooftype='email', address=user.address)
  scenario.verify(store.data.identities[user.address].contains('email') == True)
  scenario.verify(store.data.identities[user.address].contains('phone') == True)
  scenario += ctrl.removeProof(to_remove).run(sender = user, amount = sp.tez(5), valid = False)
  scenario.verify(store.data.identities[user.address].contains('email') == True)
  scenario.verify(store.data.identities[user.address].contains('phone') == True)

  ## Admin can remove a proof
  #
  scenario += ctrl.removeProof(to_remove).run(sender = admin, amount = sp.tez(5))
  scenario.verify(store.data.identities[user.address].contains('email') == False)
  scenario.verify(store.data.identities[user.address].contains('phone') == True)

@sp.add_target(name = "Remove identity", kind=allKind)
def test():
  admin = sp.test_account("admin")
  user = sp.test_account("User")

  scenario = sp.test_scenario()
  store, ctrl = init(admin, scenario)
  scenario += ctrl.registerProof('email').run(sender = user, amount = sp.tez(5))
  scenario += ctrl.verifyProof(sp.record(address=user.address,prooftype='email')).run(sender = admin)

  ## A user cannot remove self (and all proofs)
  #
  scenario.verify(store.data.identities.contains(user.address))
  scenario += ctrl.removeIdentity(user.address).run(sender = user, amount = sp.tez(5), valid = False)
  scenario.verify(store.data.identities.contains(user.address))

  ## Admin can remove all proofs for an address
  #
  scenario += ctrl.removeIdentity(user.address).run(sender = admin, amount = sp.tez(5))
  scenario.verify(store.data.identities.contains(user.address) == False)

@sp.add_target(name = "Set cost", kind=allKind)
def test():
  admin = sp.test_account("admin")
  user = sp.test_account("User")

  scenario = sp.test_scenario()
  store, ctrl = init(admin, scenario)

  ## Admin can update cost
  #
  scenario += ctrl.setCost(sp.tez(10)).run(sender = admin)
  scenario.verify(ctrl.data.cost == sp.tez(10))

  ## User cannot update cost
  #
  scenario += ctrl.setCost(sp.tez(1000)).run(sender = user, valid = False)

  ## Need correct amount to register
  #
  scenario += ctrl.registerProof('email').run(sender = user, amount = sp.tez(9), valid = False)
  scenario += ctrl.registerProof('email').run(sender = user, amount = sp.tez(10))
  
@sp.add_target(name = "Send", kind=allKind)
def test():
  admin = sp.test_account("admin")
  user = sp.test_account("User")
  receiver = sp.test_account("Receiver")

  scenario = sp.test_scenario()
  store, ctrl = init(admin, scenario)
  scenario += ctrl.registerProof('email').run(sender = user, amount = sp.tez(5))

  ## Admin can send balance elsewhere
  #
  scenario += ctrl.send(sp.record(receiverAddress=receiver.address, amount=sp.tez(2))).run(sender = admin)
  scenario.verify(ctrl.balance == sp.tez(3))

  ## User cannot send
  #
  scenario += ctrl.send(sp.record(receiverAddress=receiver.address, amount=sp.tez(2))).run(sender = user, valid = False)
    
@sp.add_target(name = "Store send", kind=allKind)
def test():
  admin = sp.test_account("admin")
  user = sp.test_account("User")
  receiver = sp.test_account("Receiver")

  scenario = sp.test_scenario()
  store, ctrl = init(admin, scenario)
  scenario += ctrl.registerProof('email').run(sender = user, amount = sp.tez(5))

  ## Send some coins to store
  #
  scenario += ctrl.send(sp.record(receiverAddress=store.address, amount=sp.tez(5))).run(sender = admin)
  scenario.verify_equal(store.balance, sp.tez(5))
  scenario.verify_equal(ctrl.balance, sp.tez(0))

  ## Controller admin can send from store via storeSend
  #
  scenario += ctrl.storeSend(sp.record(receiverAddress = ctrl.address, amount = sp.tez(5))).run(sender = admin)
  scenario.verify_equal(store.balance, sp.tez(0))
  scenario.verify_equal(ctrl.balance, sp.tez(5))

  ## Non admin cannot storeSend or send on store directly
  #
  scenario += ctrl.storeSend(sp.record(receiverAddress=receiver.address, amount=sp.tez(2))).run(sender = user, valid = False)
  scenario += store.send(sp.record(receiverAddress=receiver.address, amount=sp.tez(2))).run(sender = admin, valid = False)
    
@sp.add_target(name = "Set admin", kind=allKind)
def test():
  admin = sp.test_account("admin")
  admin2 = sp.test_account("admin2")
  user = sp.test_account("user")

  scenario = sp.test_scenario()
  store, ctrl = init(admin, scenario)

  ## Admin can update admin
  #
  scenario += ctrl.setAdmin(admin2.address).run(sender = admin)
  scenario.verify(ctrl.data.admin == admin2.address)

  ## Non-admin cannot update admin
  #
  scenario += ctrl.setAdmin(admin.address).run(sender = admin, valid=False)

  ## Controller admin (or other user) cannot set store admin directly
  #
  scenario += store.setAdmin(admin.address).run(sender = admin, valid=False)
  scenario += store.setAdmin(admin.address).run(sender = user, valid=False)
  
  ## Admin can set store admin via setStoreAdmin
  #
  scenario.verify(store.data.admin == ctrl.address)
  ctrl2 = Controller.TezIDController(admin.address, store.address, sp.big_map({}))
  scenario += ctrl2
  scenario += ctrl.setStoreAdmin(ctrl2.address).run(sender = admin2)
  scenario.verify(store.data.admin == ctrl2.address)
  
  ## Users cannot set store admin via setStoreAdmin
  #
  scenario += ctrl.setStoreAdmin(user.address).run(sender = user, valid=False)
  scenario += ctrl.setStoreAdmin(admin.address).run(sender = admin, valid=False)
    
@sp.add_target(name = "Set store", kind=allKind)
def test():
  admin = sp.test_account("admin")
  user = sp.test_account("User")

  scenario = sp.test_scenario()
  store, ctrl = init(admin, scenario)
  store2 = Store.TezIDStore(admin.address, sp.big_map(), sp.big_map())
  scenario += store2

  ## Admin can update store
  #
  scenario.verify(ctrl.data.idstore == store.address)
  scenario += ctrl.setStore(store2.address).run(sender = admin)
  scenario.verify(ctrl.data.idstore == store2.address)

  ## User cannot update store
  #
  scenario += ctrl.setStore(store.address).run(sender = user, valid = False)
    
@sp.add_target(name = "Set baker", kind=allKind)
def test():
  admin = sp.test_account("admin")
  user = sp.test_account("User")
  baker = sp.key_hash("tz1YB12JHVHw9GbN66wyfakGYgdTBvokmXQk")
  voting_powers = {
      baker: 0,
  }

  scenario = sp.test_scenario()
  store, ctrl = init(admin, scenario)

  ## Admin can update baker
  #
  scenario.verify_equal(ctrl.baker, sp.none)
  scenario += ctrl.setBaker(sp.some(baker)).run(sender = admin, voting_powers = voting_powers)
  scenario.verify_equal(ctrl.baker, sp.some(baker))

  ## User cannot update baker
  #
  scenario += ctrl.setBaker(sp.some(baker)).run(sender = user, voting_powers = voting_powers, valid = False)
  
  ## Controller admin (or other user) cannot set store baker directly
  #
  scenario += store.setBaker(sp.some(baker)).run(sender = admin, voting_powers = voting_powers, valid=False)
  scenario += store.setBaker(sp.some(baker)).run(sender = user, voting_powers = voting_powers, valid=False)
  
  ## Admin can set store baker via setStoreBaker
  #
  scenario.verify_equal(store.baker, sp.none)
  scenario += ctrl.setStoreBaker(sp.some(baker)).run(sender = admin, voting_powers = voting_powers)
  scenario.verify(store.baker == sp.some(baker))
  
  ## Users cannot set store baker via setStoreBaker
  #
  scenario += ctrl.setStoreBaker(sp.some(baker)).run(sender = user, voting_powers = voting_powers, valid=False)
    
@sp.add_target(name = "Set proof metadata", kind=allKind)
def test():
  admin = sp.test_account("admin")
  user = sp.test_account("User")

  scenario = sp.test_scenario()
  store, ctrl = init(admin, scenario)

  ## Controller admin can update proof metadata
  #
  scenario += ctrl.registerProof('twitter').run(sender = user, amount = sp.tez(5))
  scenario += ctrl.setProofMeta(sp.record(address=user.address, prooftype="twitter", key="handle", value="@asbjornenge")).run(sender = admin)
  scenario.verify_equal(store.data.identities[user.address]['twitter'].meta['handle'], "@asbjornenge")
  
  ## Updating proof should keep metadata
  #
  scenario += ctrl.verifyProof(sp.record(address=user.address, prooftype="twitter")).run(sender = admin)
  scenario.verify_equal(store.data.identities[user.address]['twitter'].verified, True)
  scenario.verify_equal(store.data.identities[user.address]['twitter'].meta['handle'], "@asbjornenge")

@sp.add_target(name = "Enable KYC metadata", kind=allKind)
def test():
  admin = sp.test_account("admin")
  user = sp.test_account("User")

  scenario = sp.test_scenario()
  store, ctrl = init(admin, scenario)

  ## Owner of gov proof can set metadata kyc: true
  #
  scenario += ctrl.registerProof('gov').run(sender = user, amount = sp.tez(5))
  scenario += ctrl.enableKYC().run(sender = user)
  scenario.verify_equal(store.data.identities[user.address]['gov'].meta['kyc'], "true")
  
  ## Verify proof should keep KYC metadata
  #
  scenario += ctrl.verifyProof(sp.record(address=user.address, prooftype="gov")).run(sender = admin)
  scenario.verify_equal(store.data.identities[user.address]['gov'].verified, True)
  scenario.verify_equal(store.data.identities[user.address]['gov'].meta['kyc'], "true")

  ## Renewing proof should keep KYC metadata
  #
  scenario += ctrl.registerProof('gov').run(sender = user, amount = sp.tez(5))
  scenario.verify_equal(store.data.identities[user.address]['gov'].verified, False)
  scenario.verify_equal(store.data.identities[user.address]['gov'].meta['kyc'], "true")

  ## Admin can set supported KYC platforms
  #
  scenario += ctrl.setKycPlatforms({ 'kyc_crunchy', 'kyc_yaynay' }).run(sender = admin)
  scenario.verify(ctrl.data.kycPlatforms.contains('kyc_crunchy'))

  ## User can enable supported KYC platforms
  #
  scenario += ctrl.enableKYCPlatform('kyc_crunchy').run(sender = user)
  scenario.verify_equal(store.data.identities[user.address]['gov'].meta['kyc_crunchy'], "true")

  ## User cannot enable unsupported KYC platforms
  #
  scenario += ctrl.enableKYCPlatform('kyc_yolo').run(sender = user, valid = False)
  scenario += ctrl.enableKYCPlatform('kyc').run(sender = user, valid = False)

