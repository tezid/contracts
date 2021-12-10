import smartpy as sp

## Types
#

TGetProofsRequestPayload = sp.TRecord(
    address=sp.TAddress, 
    callback_address=sp.TAddress, 
    callback_entrypoint=sp.TString
)
TGetProofsResponsePayload = sp.TRecord(
  address = sp.TAddress,
  proofs = sp.TMap(sp.TString, sp.TRecord(
    register_date = sp.TTimestamp, 
    verified = sp.TBool
  ))
)

## TezID
#

class TezID(sp.Contract):
  def __init__(self, admin, cost):
    self.init(
      admin = admin, 
      identities = {},
      cost = cost
    )

  @sp.entry_point
  def setAdmin(self, new_admin):
    sp.if sp.sender != self.data.admin:
        sp.failwith("Only admin can set admin")
    self.data.admin = new_admin

  @sp.entry_point
  def setCost(self, new_cost):
    sp.if sp.sender != self.data.admin:
        sp.failwith("Only admin can set cost")
    self.data.cost = new_cost

  @sp.entry_point
  def registerAddress(self):
    sp.if sp.amount < self.data.cost:
      sp.failwith("Amount too low")
    sp.if self.data.identities.contains(sp.sender):
      sp.failwith("Address already registered")
    self.data.identities[sp.sender] = {}

  @sp.entry_point
  def removeAddress(self):
    sp.if sp.amount < self.data.cost:
      sp.failwith("Amount too low")
    sp.if self.data.identities.contains(sp.sender):
      del self.data.identities[sp.sender]
    sp.else:
      sp.failwith("Address not registered")

  @sp.entry_point
  def registerProof(self, proof):
    sp.set_type(proof.type, sp.TString)
    sp.if sp.amount < self.data.cost:
      sp.failwith("Amount too low")
    self.data.identities[sp.sender][proof.type] = sp.record(
      register_date = sp.now,
      verified = False
    )

  @sp.entry_point
  def verifyProof(self, proofVer):
    sp.set_type(proofVer.type, sp.TString)
    sp.if sp.sender != self.data.admin:
      sp.failwith("Only admin can verify")
    identity = self.data.identities[proofVer.tzaddr]
    identity[proofVer.type].verified = True
    
  @sp.entry_point
  def send(self, receiverAddress, amount):
    sp.if sp.sender != self.data.admin:
      sp.failwith("Only admin can send")
    sp.send(receiverAddress, amount)
    
  @sp.entry_point
  def getProofs(self, address, callback_address, callback_entrypoint):
    sp.set_type(address, sp.TAddress)
    sp.set_type(callback_address, sp.TAddress)
    sp.set_type(callback_entrypoint, sp.TString)
    proofs = sp.local("proofs", {})
    sp.if self.data.identities.contains(address):
        pr = self.data.identities[address]
        proofs.value = pr
    c = sp.contract(TGetProofsResponsePayload, sp.sender, entry_point="register").open_some()
    sp.transfer(sp.record(address=address, proofs=proofs.value), sp.mutez(0), c)
    
## Tests
#

@sp.add_test(name = "Register identity")
def test():
  admin = sp.test_account("admin")
  user = sp.test_account("User")
  cost = sp.tez(5)
  proof = sp.record(
    type = 'phone'
  )

  scenario = sp.test_scenario()
  c1 = TezID(admin.address, cost)
  scenario += c1

  ## A user can self-register a unverified proof
  #
  scenario += c1.registerAddress().run(sender = user, amount = sp.tez(5))
  scenario += c1.registerProof(proof).run(sender = user, amount = sp.tez(5))
  scenario.verify(c1.data.identities.contains(user.address))
  scenario.verify(c1.data.identities[user.address]['phone'].verified == False)

  ## Too low fee results in failure
  #
  scenario += c1.registerAddress().run(sender = user, amount = sp.tez(4), valid = False)

@sp.add_test(name = "Verify identity")
def test():
  admin = sp.test_account("admin")
  user = sp.test_account("User")
  cost = sp.tez(5)
  proof = sp.record(
    type = 'phone'
  )
  proofVer = sp.record(
    tzaddr = user.address,
    type = 'phone'
  )

  scenario = sp.test_scenario()
  c1 = TezID(admin.address, cost)
  scenario += c1
  scenario += c1.registerAddress().run(sender = user, amount = sp.tez(5))
  scenario += c1.registerProof(proof).run(sender = user, amount = sp.tez(5))

  ## admin can verify an identity
  #
  scenario += c1.verifyProof(proofVer).run(sender = admin)
  scenario.verify(c1.data.identities[user.address]['phone'].verified == True)

  ## User cannot verify identity
  #
  scenario += c1.verifyProof(proofVer).run(sender = user, valid = False)

@sp.add_test(name = "Remove identity")
def test():
  admin = sp.test_account("admin")
  user = sp.test_account("User")
  cost = sp.tez(5)
  proof = sp.record(
    type = 'phone'
  )

  scenario = sp.test_scenario()
  c1 = TezID(admin.address, cost)
  scenario += c1
  scenario += c1.registerAddress().run(sender = user, amount = sp.tez(5))
  scenario += c1.registerProof(proof).run(sender = user, amount = sp.tez(5))

  ## A user can remove self (and all proofs)
  #
  scenario.verify(c1.data.identities.contains(user.address))
  scenario += c1.removeAddress().run(sender = user, amount = sp.tez(5))
  scenario.verify(c1.data.identities.contains(user.address) == False)

@sp.add_test(name = "Set cost")
def test(): 
  admin = sp.test_account("admin")
  user = sp.test_account("User")
  cost = sp.tez(5)

  scenario = sp.test_scenario()
  c1 = TezID(admin.address, cost)
  scenario += c1
  
  ## admin can update cost
  #
  scenario += c1.setCost(sp.tez(10)).run(sender = admin)
  scenario.verify(c1.data.cost == sp.tez(10))

  ## User cannot update cost
  #
  scenario += c1.setCost(sp.tez(1000)).run(sender = user, valid = False)
  
  ## Need correct amount to register
  #
  scenario += c1.registerAddress().run(sender = user, amount = sp.tez(9), valid = False)
  scenario += c1.registerAddress().run(sender = user, amount = sp.tez(10))
  
@sp.add_test(name = "Send balance")
def test(): 
  admin = sp.test_account("admin")
  user = sp.test_account("User")
  receiver = sp.test_account("Receiver")
  cost = sp.tez(5)

  scenario = sp.test_scenario()
  c1 = TezID(admin.address, cost)
  scenario += c1
  scenario += c1.registerAddress().run(sender = user, amount = sp.tez(5))

  ## admin can send balance elsewhere
  #
  scenario += c1.send(sp.record(receiverAddress=receiver.address, amount=sp.tez(2))).run(sender = admin)
  scenario.verify(c1.balance == sp.tez(3))
  
  ## User cannot send
  #
  scenario += c1.send(sp.record(receiverAddress=receiver.address, amount=sp.tez(2))).run(sender = user, valid = False)

@sp.add_test(name = "Set admin")
def test(): 
  admin = sp.test_account("admin")
  admin2 = sp.test_account("admin2")
  cost = sp.tez(5)

  scenario = sp.test_scenario()
  c1 = TezID(admin.address, cost)
  scenario += c1
  
  ## admin can update admin
  #
  scenario += c1.setAdmin(admin2.address).run(sender = admin)
  scenario.verify(c1.data.admin == admin2.address)

  ## Non-admin cannot update admin
  #
  scenario += c1.setAdmin(admin.address).run(sender = admin, valid=False)
  
class ICO(sp.Contract):
    def __init__(self, tezid, requiredProofs):
      self.init(
        tezid = tezid,
        requiredProofs = requiredProofs,
        participants = {}
      )
      
    @sp.entry_point
    def register(self, ptr):
        sp.if sp.sender != self.data.tezid:
            sp.failwith('Only TezID can register')
        sp.set_type(ptr, TGetProofsResponsePayload)
        sp.set_type(ptr.address, sp.TAddress)
        validProofs = sp.local("validProofs", [])
        sp.for requiredProof in self.data.requiredProofs:
            sp.if ptr.proofs.contains(requiredProof):
                sp.if ptr.proofs[requiredProof].verified:
                    validProofs.value.push(requiredProof)
        sp.if sp.len(self.data.requiredProofs) == sp.len(validProofs.value):
            self.data.participants[ptr.address] = 1

    @sp.entry_point
    def signup(self):
        c = sp.contract(TGetProofsRequestPayload, self.data.tezid, entry_point="getProofs").open_some()
        sp.transfer(sp.record(address=sp.sender, callback_address=sp.self_address, callback_entrypoint="register"), sp.mutez(0), c)

@sp.add_test(name = "Call TezID from other contract")
def test():
  admin = sp.test_account("admin")
  user = sp.test_account("User")
  user2 = sp.test_account("User2")
  user3 = sp.test_account("User3")
  cost = sp.tez(5)
  proof1 = sp.record(
    type = 'email'
  )
  proof2 = sp.record(
    type = 'phone'
  )
  proofVer1 = sp.record(
    tzaddr = user.address,
    type = 'email'
  )
  proofVer2 = sp.record(
    tzaddr = user.address,
    type = 'phone'
  )

  scenario = sp.test_scenario()
  c1 = TezID(admin.address, cost)
  scenario += c1
  c2 = ICO(c1.address, ["email","phone"])
  scenario += c2
  
  ## A user with the correct valid proofs can register as participant
  #
  scenario += c1.registerAddress().run(sender = user, amount = sp.tez(5))
  scenario += c1.registerProof(proof1).run(sender = user, amount = sp.tez(5))
  scenario += c1.registerProof(proof2).run(sender = user, amount = sp.tez(5))
  scenario += c1.verifyProof(proofVer1).run(sender = admin)
  scenario += c1.verifyProof(proofVer2).run(sender = admin)
  scenario += c2.signup().run(sender = user)
  scenario.verify(c2.data.participants.contains(user.address))
  
  ## A user without the correct valid proofs cannot register as participant
  #
  scenario += c1.registerAddress().run(sender = user2, amount = sp.tez(5))
  scenario += c1.registerProof(proof1).run(sender = user2, amount = sp.tez(5))
  scenario += c1.registerProof(proof2).run(sender = user2, amount = sp.tez(5))
  scenario += c1.verifyProof(proofVer1).run(sender = admin)
  scenario += c2.signup().run(sender = user2)
  scenario.verify(c2.data.participants.contains(user2.address) == False)
  
  ## A user not registered on TezID cannot register as participant
  #
  scenario += c2.signup().run(sender = user3)
  scenario.verify(c2.data.participants.contains(user3.address) == False)
  
  ## Only TezID can call register endpoiint
  #
  emailProof = sp.record(
      register_date = sp.timestamp(0),
      verified = True
  )
  phoneProof = sp.record(
      register_date = sp.timestamp(0),
      verified = True
  )
  proofs = {}
  proofs['email'] = emailProof
  proofs['phone'] = phoneProof
  pr = sp.record(address = user3.address, proofs = proofs)
  scenario += c2.register(pr).run(sender = user3, valid=False)
