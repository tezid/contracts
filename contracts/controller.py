import os
import smartpy as sp

cwd = os.getcwd()
Types = sp.io.import_script_from_url("file://%s/contracts/types.py" % cwd)

# TODO:
# * checkAdmin function
# * use views
#

## TezID Controller
#

class TezIDController(sp.Contract):
  def __init__(self, admin, idstore, metadata):
    self.init_type(sp.TRecord(
      admin = sp.TAddress,
      idstore = sp.TAddress,
      cost = sp.TMutez,
      kycPlatforms = sp.TSet(sp.TString),
      updateProofCache = sp.TMap(sp.TAddress, sp.TMap(sp.TString, sp.TString)),
      metadata = sp.TBigMap(sp.TString, sp.TBytes)
    ))
    self.init(
      admin = admin, 
      idstore = idstore,
      cost = sp.tez(5),
      kycPlatforms = sp.set(),
      updateProofCache = {},
      metadata = metadata
    )

  ## Helpers
  #

  def checkAdmin(self):
    sp.verify(sp.sender == self.data.admin, 'Only admin can call this entrypoint')    

  def checkProofExistence(self, proofs, proofType):
    sp.verify(proofs.contains(proofType), 'Missing required proof for this entrypoint')

  def checkSupportedKycPlatform(self, platform):
    sp.verify(self.data.kycPlatforms.contains(platform), 'KYC platform not supported')
        
  ## Default 
  #

  @sp.entry_point
  def default(self):
    pass

  ## Basic admin functions
  #

  @sp.entry_point
  def setAdmin(self, new_admin):
    self.checkAdmin()
    self.data.admin = new_admin

  @sp.entry_point
  def setCost(self, new_cost):
    self.checkAdmin()
    self.data.cost = new_cost

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

  ## Store admin functions
  #
  
  @sp.entry_point
  def setStoreAdmin(self, new_admin):
    self.checkAdmin()
    c = sp.contract(sp.TAddress, self.data.idstore, entry_point="setAdmin").open_some()
    sp.transfer(new_admin, sp.mutez(0), c)

  @sp.entry_point
  def setStoreBaker(self, new_delegate):
    self.checkAdmin()
    c = sp.contract(sp.TOption(sp.TKeyHash), self.data.idstore, entry_point="setBaker").open_some()
    sp.transfer(new_delegate, sp.mutez(0), c)
      
  @sp.entry_point
  def storeSend(self, receiverAddress, amount):
    self.checkAdmin()
    c = sp.contract(Types.TSendPayload, self.data.idstore, entry_point="send").open_some()
    sp.transfer(sp.record(receiverAddress = receiverAddress, amount = amount), sp.mutez(0), c)

  ## Proof functions
  #

  def getOrCreateProof(self, proofs, proofType):
    localProof = sp.local('localProof', sp.record(
      register_date = sp.now,
      verified = False,
      meta = sp.map()
    ))
    sp.if proofs.contains(proofType):
      localProof.value =  proofs[proofType]
    return localProof.value


  @sp.entry_point
  def registerProof(self, proofType):
    sp.if sp.amount < self.data.cost:
      sp.failwith('Amount too low')
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

  @sp.entry_point
  def updateProofCallback(self, address, proofs):
      sp.if sp.sender != self.data.idstore:
          sp.failwith("Only idstore can call getProofsCallback")
      sp.if self.data.updateProofCache.contains(address) == False:
          sp.failwith("No cache entry for address")
      sp.set_type(address, sp.TAddress)
      sp.set_type(proofs, Types.TProofs)
      cacheEntry = sp.local('cacheEntry', self.data.updateProofCache[address])
      proofType = cacheEntry.value['prooftype']
      operation = cacheEntry.value['operation']

      supportedOperations = sp.set(["register","verify","kyc","kycplatform","meta","rename"])
      localProof = sp.local('localProof', sp.record(
          register_date = sp.now,
          verified = False,
          meta = sp.map()
      ))
      sp.if proofs.contains(proofType):
          localProof.value =  proofs[proofType]

      # Verifications
      sp.if supportedOperations.contains(operation) == False:
          sp.failwith("Unsupported updateProof operation")

      sp.if proofs.contains(proofType) == False:
          sp.if operation != "register":
              sp.failwith("Cannot update non-existing proof")

      sp.if operation == "register":
          localProof.value.verified = False
          localProof.value.register_date = sp.now
          # TODO: Should clear metadata for some prooftypes

      sp.if operation == "verify":
          localProof.value.verified = True
          
      sp.if operation == "kyc":
          localProof.value.meta["kyc"] = "true"
          localProof.value.verified = False

      sp.if operation == "kycplatform":
          platform = cacheEntry.value['platform']
          localProof.value.meta[platform] = "true"

      sp.if operation == "meta":
          metaKey = cacheEntry.value['key']
          metaValue = cacheEntry.value['value']
          localProof.value.meta[metaKey] = metaValue

      localProofType = sp.local('localProofType', proofType)

      sp.if operation == "rename":
          localProofType.value = cacheEntry.value['newtype']

      del self.data.updateProofCache[address]
      c = sp.contract(Types.TSetProofPayload, self.data.idstore, entry_point="setProof").open_some()
      sp.transfer(sp.record(address=address, prooftype=localProofType.value, proof=localProof.value), sp.mutez(0), c)

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
      sp.if sp.sender != self.data.admin:
          sp.failwith("Only admin can setProofMeta")
      self.data.updateProofCache[address] = {
          "prooftype": prooftype,
          "operation": "meta",
          "key": key,
          "value": value
      }
      callback_address = sp.self_entry_point_address(entry_point = 'updateProofCallback')
      c = sp.contract(Types.TGetProofsRequestPayload, self.data.idstore, entry_point="getProofs").open_some()
      sp.transfer(sp.record(address=address, callback_address=callback_address), sp.mutez(0), c)

  @sp.entry_point
  def renameProof(self, address, oldProofType, newProofType):
      sp.if sp.sender != self.data.admin:
          sp.failwith("Only admin can renameProof")
      self.data.updateProofCache[address] = {
          "prooftype": oldProofType,
          "newtype": newProofType,
          "operation": "rename"
      }
      callback_address = sp.self_entry_point_address(entry_point = 'updateProofCallback')
      c = sp.contract(Types.TGetProofsRequestPayload, self.data.idstore, entry_point="getProofs").open_some()
      sp.transfer(sp.record(address=address, callback_address=callback_address), sp.mutez(0), c)
      
  @sp.entry_point
  def removeProof(self, prooftype, address):
      sp.if sp.sender != self.data.admin:
          sp.failwith("Only admin can removeProof")
      c = sp.contract(Types.TDelProofPayload, self.data.idstore, entry_point="delProof").open_some()
      sp.transfer(sp.record(address = address, prooftype = prooftype), sp.mutez(0), c)
      
  @sp.entry_point
  def removeIdentity(self, address):
      sp.if sp.sender != self.data.admin:
          sp.failwith("Only admin can removeIdentity")
      c = sp.contract(sp.TAddress, self.data.idstore, entry_point="removeIdentity").open_some()
      sp.transfer(address, sp.mutez(0), c)
    
