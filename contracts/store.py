import os
import smartpy as sp

cwd = os.getcwd()
Types = sp.io.import_script_from_url("file://%s/contracts/types.py" % cwd)

# TODO:
# * metadata
# * checkAdmin function
# * use views
#

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
      
  @sp.entry_point
  def default(self):
    pass
      
  @sp.entry_point
  def setAdmin(self, new_admin):
    sp.if sp.sender != self.data.admin:
      sp.failwith("Only admin can setAdmin")
    self.data.admin = new_admin
      
  @sp.entry_point
  def setBaker(self, new_delegate):
    sp.if sp.sender != self.data.admin:
      sp.failwith("Only admin can setBaker")
    sp.set_delegate(new_delegate)
      
  @sp.entry_point
  def send(self, receiverAddress, amount):
    sp.if sp.sender != self.data.admin:
      sp.failwith("Only admin can send")
    sp.send(receiverAddress, amount)

  @sp.entry_point
  def setProof(self, address, prooftype, proof):
    sp.if sp.sender != self.data.admin:
      sp.failwith("Only admin can setProof")
    sp.if self.data.identities.contains(address) == False:
      self.data.identities[address] = {}
    self.data.identities[address][prooftype] = proof
      
  @sp.entry_point
  def delProof(self, address, prooftype):
    sp.if sp.sender != self.data.admin:
      sp.failwith("Only admin can delProof")
    del self.data.identities[address][prooftype]
      
  @sp.entry_point
  def removeIdentity(self, address):
    sp.if sp.sender != self.data.admin:
      sp.failwith("Only admin can removeIdentity")
    del self.data.identities[address]

  @sp.entry_point
  def getProofs(self, address, callback_address):
    proofs = sp.local('proofs', sp.map())
    sp.if self.data.identities.contains(address):
      proofs.value = self.data.identities[address]
    c = sp.contract(Types.TGetProofsResponsePayload, callback_address).open_some()
    sp.transfer(sp.record(address=address, proofs=proofs.value), sp.mutez(0), c)

