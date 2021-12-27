import os
import smartpy as sp

cwd = os.getcwd()
Types = sp.io.import_script_from_url("file://%s/contracts/types.py" % cwd)

## TezID Store
#

class TezIDStore(sp.Contract):
  def __init__(self, admins, initialIdentities, metadata):
    self.init_type(Types.TStoreStorage)
    self.init(
      admins = admins, 
      identities = initialIdentities,
      metadata = metadata
    )

  ## Helpers
  #

  @sp.private_lambda(with_storage='read-only', wrap_call=True)
  def checkAdmin(self):
    sp.verify(self.data.admins.contains(sp.sender), 'Only admin can call this entrypoint')    

  ## Default
  #

  @sp.entry_point
  def default(self):
    pass

  ## Admin entrypoints
  #
   
  @sp.entry_point
  def addAdmin(self, admin):
    self.checkAdmin()
    self.data.admins.add(admin)

  @sp.entry_point
  def delAdmin(self, admin):
    self.checkAdmin()
    self.data.admins.remove(admin)
      
  @sp.entry_point
  def setBaker(self, new_delegate):
    self.checkAdmin()
    sp.set_delegate(new_delegate)
      
  @sp.entry_point
  def send(self, receiverAddress, amount):
    self.checkAdmin()
    sp.send(receiverAddress, amount)

  @sp.entry_point
  def setProof(self, address, prooftype, proof):
    self.checkAdmin()
    sp.if self.data.identities.contains(address) == False:
      self.data.identities[address] = sp.map({})
    self.data.identities[address][prooftype] = proof
      
  @sp.entry_point
  def delProof(self, address, prooftype):
    self.checkAdmin()
    del self.data.identities[address][prooftype]
      
  @sp.entry_point
  def removeIdentity(self, address):
    self.checkAdmin()
    del self.data.identities[address]

  @sp.entry_point
  def setProofs(self, proofs):
    self.checkAdmin()
    sp.set_type(proofs, Types.TSetProofs)
    sp.for proof in proofs.items():
      self.data.identities[proof.key] = proof.value

  ## Failsafe updateable entrypoint
  #

  @sp.entry_point
  def triggerLambda(self, logic, params):
    self.checkAdmin()
    sp.set_type(logic, sp.TLambda(Types.TStoreLambdaParams, Types.TStoreStorage))
    sp.set_type(params, sp.TBytes)
    lp = sp.record(
      storage = self.data,
      params = params
    )
    storage = logic(lp)
    self.data = storage

  ## Get Proofs
  #

  @sp.entry_point
  def getProofs(self, address, callback_address):
    proofs = sp.local('proofs', sp.map())
    sp.if self.data.identities.contains(address):
      proofs.value = self.data.identities[address]
    c = sp.contract(Types.TGetProofsResponsePayload, callback_address).open_some()
    sp.transfer(sp.record(address=address, proofs=proofs.value), sp.mutez(0), c)

  @sp.onchain_view()
  def getProofsForAddress(self, address):
    proofs = sp.local('proofs', sp.map({}))
    sp.if self.data.identities.contains(address):
      proofs.value = self.data.identities[address]
    sp.result(proofs.value)

