import os
import smartpy as sp

cwd = os.getcwd()
Types = sp.io.import_script_from_url("file://%s/contracts/types.py" % cwd)
# Types = sp.io.import_script_from_url("https://tezid.infura-ipfs.io/ipfs/QmcwUQmntR9sVvgv2MQRVgEGVM78bXF3Hif9yQop5cgaUo")

## TezID Controller
#

class TezIDController(sp.Contract):
  def __init__(self, admin, idstore, metadata):
    self.init_type(sp.TRecord(
      admins = sp.TSet(sp.TAddress),
      idstore = sp.TAddress,
      cost = sp.TMap(sp.TString, sp.TMutez),
      kycPlatforms = sp.TSet(sp.TString),
      metadata = sp.TBigMap(sp.TString, sp.TBytes)
    ))
    self.init(
      admins = sp.set([admin]), 
      idstore = idstore,
      cost = { 'default': sp.tez(5) },
      kycPlatforms = sp.set(),
      metadata = metadata
    )

  ## Helpers
  #

  @sp.private_lambda(with_storage='read-only', wrap_call=True)
  def checkAdmin(self):
    sp.verify(self.data.admins.contains(sp.sender), 'Only admin can call this entrypoint')    

  @sp.private_lambda(with_storage='read-only', wrap_call=True)
  def checkCost(self, proofType):
    cost = sp.local('cost', self.data.cost['default'])
    sp.if self.data.cost.contains(proofType):
      cost.value = self.data.cost[proofType]
    sp.verify(sp.amount >= cost.value, 'Amount too low')

  def checkProofExistence(self, proofs, proofType):
    sp.verify(proofs.contains(proofType), 'Missing required proof for this entrypoint')

  def checkSupportedKycPlatform(self, platform):
    sp.verify(self.data.kycPlatforms.contains(platform), 'KYC platform not supported')

  def getOrCreateProof(self, proofs, proofType):
    localProof = sp.local('localProof', sp.record(
      register_date = sp.now,
      verified = False,
      meta = sp.map()
    ))
    sp.if proofs.contains(proofType):
      localProof.value =  proofs[proofType]
    return localProof.value

  ## Default 
  #

  @sp.entry_point
  def default(self):
    pass

  ## Basic admin functions
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
  def setCost(self, proofType, cost):
    self.checkAdmin()
    self.data.cost[proofType] = cost

  @sp.entry_point
  def delCost(self, proofType):
    self.checkAdmin()
    del self.data.cost[proofType]

  @sp.entry_point
  def setStore(self, new_store):
    self.checkAdmin()
    self.data.idstore = new_store

  @sp.entry_point
  def send(self, receiverAddress, amount):
    self.checkAdmin()
    sp.send(receiverAddress, amount)
      
  @sp.entry_point
  def setBaker(self, new_delegate):
    self.checkAdmin()
    sp.set_delegate(new_delegate)

  @sp.entry_point
  def setKycPlatforms(self, kycPlatforms):
    self.checkAdmin()
    self.data.kycPlatforms = kycPlatforms

  ## User Proof Functions
  #

  @sp.entry_point
  def registerProof(self, proofType):
    self.checkCost(proofType)
    proofs = sp.view('getProofsForAddress', self.data.idstore, sp.sender, t = Types.TProofs).open_some('Invalid view')
    proof = self.getOrCreateProof(proofs, proofType)
    proof.verified = False
    proof.register_date = sp.now
    c = sp.contract(Types.TSetProofPayload, self.data.idstore, entry_point="setProof").open_some()
    sp.transfer(sp.record(address=sp.sender, prooftype=proofType, proof=proof), sp.mutez(0), c)

  @sp.entry_point
  def enableKYC(self):
    proofs = sp.view('getProofsForAddress', self.data.idstore, sp.sender, t = Types.TProofs).open_some('Invalid view')
    self.checkProofExistence(proofs, 'gov')
    proof = self.getOrCreateProof(proofs, 'gov') 
    proof.meta['kyc'] = 'true'
    proof.verified = False
    c = sp.contract(Types.TSetProofPayload, self.data.idstore, entry_point="setProof").open_some()
    sp.transfer(sp.record(address=sp.sender, prooftype='gov', proof=proof), sp.mutez(0), c)

  @sp.entry_point
  def enableKYCPlatform(self, platform):
    self.checkSupportedKycPlatform(platform)
    proofs = sp.view('getProofsForAddress', self.data.idstore, sp.sender, t = Types.TProofs).open_some('Invalid view')
    self.checkProofExistence(proofs, 'gov')
    proof = self.getOrCreateProof(proofs, 'gov') 
    proof.meta[platform] = "true"
    c = sp.contract(Types.TSetProofPayload, self.data.idstore, entry_point="setProof").open_some()
    sp.transfer(sp.record(address=sp.sender, prooftype='gov', proof=proof), sp.mutez(0), c)

  ## Admin Proof Functions
  #

  @sp.entry_point
  def registerProofAdmin(self, address, proofType):
    self.checkAdmin()
    proofs = sp.view('getProofsForAddress', self.data.idstore, sp.sender, t = Types.TProofs).open_some('Invalid view')
    proof = self.getOrCreateProof(proofs, proofType)
    proof.verified = False
    proof.register_date = sp.now
    c = sp.contract(Types.TSetProofPayload, self.data.idstore, entry_point="setProof").open_some()
    sp.transfer(sp.record(address=address, prooftype=proofType, proof=proof), sp.mutez(0), c)

  @sp.entry_point
  def verifyProof(self, address, prooftype):
    self.checkAdmin()
    proofs = sp.view('getProofsForAddress', self.data.idstore, address, t = Types.TProofs).open_some('Invalid view')
    self.checkProofExistence(proofs, prooftype)
    proof = self.getOrCreateProof(proofs, prooftype)
    proof.verified = True
    c = sp.contract(Types.TSetProofPayload, self.data.idstore, entry_point="setProof").open_some()
    sp.transfer(sp.record(address=address, prooftype=prooftype, proof=proof), sp.mutez(0), c)

  @sp.entry_point
  def setProofMeta(self, address, prooftype, key, value):
    self.checkAdmin()
    proofs = sp.view('getProofsForAddress', self.data.idstore, address, t = Types.TProofs).open_some('Invalid view')
    self.checkProofExistence(proofs, prooftype)
    proof = self.getOrCreateProof(proofs, prooftype)
    proof.meta[key] = value
    c = sp.contract(Types.TSetProofPayload, self.data.idstore, entry_point="setProof").open_some()
    sp.transfer(sp.record(address=address, prooftype=prooftype, proof=proof), sp.mutez(0), c)

  @sp.entry_point
  def removeProof(self, prooftype, address):
    self.checkAdmin()
    c = sp.contract(Types.TDelProofPayload, self.data.idstore, entry_point="delProof").open_some()
    sp.transfer(sp.record(address = address, prooftype = prooftype), sp.mutez(0), c)
      
  @sp.entry_point
  def removeIdentity(self, address):
    self.checkAdmin()
    c = sp.contract(sp.TAddress, self.data.idstore, entry_point="removeIdentity").open_some()
    sp.transfer(address, sp.mutez(0), c)
    
