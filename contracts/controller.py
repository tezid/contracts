import smartpy as sp

# TODO:
# * checkAdmin function
# * use views
#

## TezID Controller
#

class TezIDController(sp.Contract):
  def __init__(self, admin, idstore, cost):
    self.init_type(sp.TRecord(
      admin = sp.TAddress,
      idstore = sp.TAddress,
      cost = sp.TMutez,
      kycPlatforms = sp.TSet(sp.TString),
      updateProofCache = sp.TMap(sp.TAddress, sp.TMap(sp.TString, sp.TString))
    ))
    self.init(
      admin = admin, 
      idstore = idstore,
      cost = cost,
      kycPlatforms = sp.set(),
      updateProofCache = {}
    )
        
  ## Default (needed to receive stakiung rewards)
  #
  @sp.entry_point
  def default(self):
    pass

  ## Basic admin functions
  #

  @sp.entry_point
  def setAdmin(self, new_admin):
    sp.if sp.sender != self.data.admin:
      sp.failwith("Only admin can setAdmin")
    self.data.admin = new_admin

  @sp.entry_point
  def setCost(self, new_cost):
    sp.if sp.sender != self.data.admin:
      sp.failwith("Only admin can setCost")
    self.data.cost = new_cost

  @sp.entry_point
  def setStore(self, new_store):
    sp.if sp.sender != self.data.admin:
      sp.failwith("Only admin can setStore")
    self.data.idstore = new_store

  @sp.entry_point
  def send(self, receiverAddress, amount):
    sp.if sp.sender != self.data.admin:
      sp.failwith("Only admin can send")
    sp.send(receiverAddress, amount)
      
  @sp.entry_point
  def setBaker(self, new_delegate):
    sp.if sp.sender != self.data.admin:
      sp.failwith("Only admin can setBaker")
    sp.set_delegate(new_delegate)

  @sp.entry_point
  def setKycPlatforms(self, kycPlatforms):
    sp.if sp.sender != self.data.admin:
      sp.failwith("Only admin can setKycPlatforms")
    self.data.kycPlatforms = kycPlatforms

  ## Store admin functions
  #
  
  @sp.entry_point
  def setStoreAdmin(self, new_admin):
      sp.if sp.sender != self.data.admin:
          sp.failwith("Only admin can setStoreAdmin")
      c = sp.contract(sp.TAddress, self.data.idstore, entry_point="setAdmin").open_some()
      sp.transfer(new_admin, sp.mutez(0), c)

  @sp.entry_point
  def setStoreBaker(self, new_delegate):
      sp.if sp.sender != self.data.admin:
          sp.failwith("Only admin can setStoreBaker")
      c = sp.contract(sp.TOption(sp.TKeyHash), self.data.idstore, entry_point="setBaker").open_some()
      sp.transfer(new_delegate, sp.mutez(0), c)
      
  @sp.entry_point
  def storeSend(self, receiverAddress, amount):
      sp.if sp.sender != self.data.admin:
          sp.failwith("Only admin can storeSend")
      c = sp.contract(TSendPayload, self.data.idstore, entry_point="send").open_some()
      sp.transfer(sp.record(receiverAddress = receiverAddress, amount = amount), sp.mutez(0), c)

  ## Proof functions
  #

  @sp.entry_point
  def registerProof(self, prooftype):
      sp.if sp.amount < self.data.cost:
          sp.failwith("Amount too low")
      self.data.updateProofCache[sp.sender] = {
          "prooftype": prooftype,
          "operation": "register"
      }
      callback_address = sp.self_entry_point_address(entry_point = 'updateProofCallback')
      c = sp.contract(TGetProofsRequestPayload, self.data.idstore, entry_point="getProofs").open_some()
      sp.transfer(sp.record(address=sp.sender, callback_address=callback_address), sp.mutez(0), c)

  @sp.entry_point
  def enableKYC(self):
      self.data.updateProofCache[sp.sender] = {
          "prooftype": "gov",
          "operation": "kyc"
      }
      callback_address = sp.self_entry_point_address(entry_point = 'updateProofCallback')
      c = sp.contract(TGetProofsRequestPayload, self.data.idstore, entry_point="getProofs").open_some()
      sp.transfer(sp.record(address=sp.sender, callback_address=callback_address), sp.mutez(0), c)

  @sp.entry_point
  def enableKYCPlatform(self, platform):
      sp.if self.data.kycPlatforms.contains(platform) == False:
          sp.failwith("KYC platform not supported")
      self.data.updateProofCache[sp.sender] = {
          "prooftype": "gov",
          "operation": "kycplatform",
          "platform": platform
      }
      callback_address = sp.self_entry_point_address(entry_point = 'updateProofCallback')
      c = sp.contract(TGetProofsRequestPayload, self.data.idstore, entry_point="getProofs").open_some()
      sp.transfer(sp.record(address=sp.sender, callback_address=callback_address), sp.mutez(0), c)

  @sp.entry_point
  def updateProofCallback(self, address, proofs):
      sp.if sp.sender != self.data.idstore:
          sp.failwith("Only idstore can call getProofsCallback")
      sp.if self.data.updateProofCache.contains(address) == False:
          sp.failwith("No cache entry for address")
      sp.set_type(address, sp.TAddress)
      sp.set_type(proofs, TProofs)
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
      c = sp.contract(TSetProofPayload, self.data.idstore, entry_point="setProof").open_some()
      sp.transfer(sp.record(address=address, prooftype=localProofType.value, proof=localProof.value), sp.mutez(0), c)

  @sp.entry_point
  def verifyProof(self, address, prooftype):
      sp.if sp.sender != self.data.admin:
          sp.failwith("Only admin can verifyProof")
      self.data.updateProofCache[address] = {
          "prooftype": prooftype,
          "operation": "verify"
      }
      callback_address = sp.self_entry_point_address(entry_point = 'updateProofCallback')
      c = sp.contract(TGetProofsRequestPayload, self.data.idstore, entry_point="getProofs").open_some()
      sp.transfer(sp.record(address=address, callback_address=callback_address), sp.mutez(0), c)

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
      c = sp.contract(TGetProofsRequestPayload, self.data.idstore, entry_point="getProofs").open_some()
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
      c = sp.contract(TGetProofsRequestPayload, self.data.idstore, entry_point="getProofs").open_some()
      sp.transfer(sp.record(address=address, callback_address=callback_address), sp.mutez(0), c)
      
  @sp.entry_point
  def removeProof(self, prooftype, address):
      sp.if sp.sender != self.data.admin:
          sp.failwith("Only admin can removeProof")
      c = sp.contract(TDelProofPayload, self.data.idstore, entry_point="delProof").open_some()
      sp.transfer(sp.record(address = address, prooftype = prooftype), sp.mutez(0), c)
      
  @sp.entry_point
  def removeIdentity(self, address):
      sp.if sp.sender != self.data.admin:
          sp.failwith("Only admin can removeIdentity")
      c = sp.contract(sp.TAddress, self.data.idstore, entry_point="removeIdentity").open_some()
      sp.transfer(address, sp.mutez(0), c)
    
