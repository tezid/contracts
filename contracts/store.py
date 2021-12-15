import os
import smartpy as sp

cwd = os.getcwd()
Types = sp.io.import_script_from_url("file://%s/contracts/types.py" % cwd)

## TezID Store
#

class TezIDStore(sp.Contract):
  def __init__(self, admin, initialIdentities, metadata):
    self.init_type(sp.TRecord(
      admin = sp.TAddress,
      identities = Types.TIdentities,
      metadata = sp.TBigMap(sp.TString, sp.TBytes)
    ))
    self.init(
      admin = admin,
      identities = initialIdentities,
      metadata = metadata
    )

  ## Helpers
  #

  @sp.private_lambda(with_storage='read-only', wrap_call=True)
  def checkAdmin(self):
    sp.verify(sp.sender == self.data.admin, 'Only admin can call this entrypoint')    

  ## Default
  #

  @sp.entry_point
  def default(self):
    pass

  ## Admin entrypoints
  #
   
  @sp.entry_point
  def setAdmin(self, new_admin):
    self.checkAdmin()
    self.data.admin = new_admin
      
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
  def setFailsafeLogic(self, logic):
    self.checkAdmin()
    sp.set_entry_point('failsafe', logic)

  @sp.entry_point(lazify=True, lazy_no_code=True)
  def failsafe(self, params):
    self.checkAdmin()
    sp.set_type(params, sp.TBytes)
    pass

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

