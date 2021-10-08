import smartpy as sp

## Types
#

TProof = sp.TRecord(
    register_date = sp.TTimestamp,
    verified = sp.TBool,
    meta = sp.TMap(sp.TString, sp.TString)
)
TProofs = sp.TMap(sp.TString, TProof)
TIdentities = sp.TBigMap(sp.TAddress, TProofs)
TSendPayload = sp.TRecord(receiverAddress = sp.TAddress, amount = sp.TMutez)
TSetProofPayload = sp.TRecord(
    address=sp.TAddress,
    prooftype=sp.TString,
    proof=TProof
)
TDelProofPayload = sp.TRecord(
    address=sp.TAddress,
    prooftype=sp.TString
)
TGetProofsRequestPayload = sp.TRecord(
    address=sp.TAddress, 
    callback_address=sp.TAddress
)
TGetProofsResponsePayload = sp.TRecord(
  address = sp.TAddress,
  proofs = TProofs
)

## TezIDStorage
#

class TezIDStore(sp.Contract):
    def __init__(self, admin, initialIdentities):
        self.init_type(sp.TRecord(
            admin = sp.TAddress,
            identities = TIdentities
        ))
        self.init(
            admin = admin,
            identities = initialIdentities
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
        c = sp.contract(TGetProofsResponsePayload, callback_address).open_some()
        sp.transfer(sp.record(address=address, proofs=proofs.value), sp.mutez(0), c)

## TezID
#

class TezIDController(sp.Contract):
    def __init__(self, admin, idstore, cost):
        self.init_type(sp.TRecord(
            admin = sp.TAddress,
            idstore = sp.TAddress,
            cost = sp.TMutez,
            updateProofCache = sp.TMap(sp.TAddress, sp.TMap(sp.TString, sp.TString))
        ))
        self.init(
            admin = admin, 
            idstore = idstore,
            cost = cost,
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

#    @sp.entry_point
#    def registerProof(self, prooftype):
#        sp.if sp.amount < self.data.cost:
#            sp.failwith("Amount too low")
#        proofdata = sp.record(
#            register_date = sp.now,
#            verified = False,
#            meta = sp.map()
#        )
#        c = sp.contract(TSetProofPayload, self.data.idstore, entry_point="setProof").open_some()
#        sp.transfer(sp.record(address=sp.sender, prooftype=prooftype, proof=proofdata), sp.mutez(0), c)

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

        supportedOperations = sp.local('supportedOperations', sp.set(["register","verify","kyc","meta"]))
        localProof = sp.local('localProof', sp.record(
            register_date = sp.now,
            verified = False,
            meta = sp.map()
        ))
        sp.if proofs.contains(proofType):
            localProof.value =  proofs[proofType]

        # Verifications
        sp.if supportedOperations.value.contains(operation) == False:
            sp.failwith("Unsupported updateProof operation")

        sp.if proofs.contains(proofType) == False:
            sp.if operation != "register":
                sp.failwith("Cannot update non-existing proof")

        sp.if operation == "register":
            localProof.value.verified = False
            localProof.register_date = sp.now

        sp.if operation == "verify":
            localProof.value.verified = True
            
        sp.if operation == "kyc":
            localProof.value.meta["kyc"] = "true"

        sp.if operation == "meta":
            metaKey = cacheEntry.value['key']
            metaValue = cacheEntry.value['value']
            localProof.value.meta[metaKey] = metaValue

        del self.data.updateProofCache[address]
        c = sp.contract(TSetProofPayload, self.data.idstore, entry_point="setProof").open_some()
        sp.transfer(sp.record(address=address, prooftype=proofType, proof=localProof.value), sp.mutez(0), c)

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
    def removeProof(self, prooftype):
        sp.if sp.amount < self.data.cost:
            sp.failwith("Amount too low")
        c = sp.contract(TDelProofPayload, self.data.idstore, entry_point="delProof").open_some()
        sp.transfer(sp.record(address = sp.sender, prooftype = prooftype), sp.mutez(0), c)
        
    @sp.entry_point
    def removeIdentity(self):
        sp.if sp.amount < self.data.cost:
            sp.failwith("Amount too low")
        c = sp.contract(sp.TAddress, self.data.idstore, entry_point="removeIdentity").open_some()
        sp.transfer(sp.sender, sp.mutez(0), c)
    
## Tests
#

runAll = False

def initTests(admin, scenario, cost=sp.tez(5)):
    store = TezIDStore(admin.address, sp.big_map())
    scenario += store
    ctrl = TezIDController(admin.address, store.address, cost)
    scenario += ctrl
    scenario += store.setAdmin(ctrl.address).run(sender = admin)
    return store, ctrl

@sp.add_test(name = "Register proof", is_default=runAll)
def test():
    admin = sp.test_account("admin")
    user = sp.test_account("User")

    scenario = sp.test_scenario()
    store, ctrl = initTests(admin, scenario)

    ## A user can self-register a unverified proof
    #
    scenario += ctrl.registerProof('phone').run(sender = user, amount = sp.tez(5))
    scenario.verify(store.data.identities.contains(user.address))
    scenario.verify(store.data.identities[user.address]['phone'].verified == False)

    ## Too low fee results in failure
    #
    scenario += ctrl.registerProof('phone').run(sender = user, amount = sp.tez(4), valid = False)
  
@sp.add_test(name = "Verify proof", is_default=runAll)
def test():
    admin = sp.test_account("admin")
    user = sp.test_account("User")
    cost = sp.tez(5)

    scenario = sp.test_scenario()
    store, ctrl = initTests(admin, scenario)
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
    
    ## You cannot get a proof verified by attempting to trigger TezIDStore
    #
    callback_address = sp.to_address(ctrl.typed.updateProofCallback)
    scenario += store.getProofs(sp.record(address=user.address, callback_address=callback_address)).run(valid = False)
    scenario.verify(store.data.identities[user.address]['phone'].verified == False)
    
    ## Admin cannot verif a proof that is not added by a user first
    #
    scenario += ctrl.verifyProof(sp.record(address=user.address,prooftype='twitter')).run(sender = admin, valid = False)
    
@sp.add_test(name = "Remove proof", is_default=runAll)
def test():
    admin = sp.test_account("admin")
    user = sp.test_account("User")

    scenario = sp.test_scenario()
    store, ctrl = initTests(admin, scenario)
    scenario += ctrl.registerProof('email').run(sender = user, amount = sp.tez(5))
    scenario += ctrl.registerProof('phone').run(sender = user, amount = sp.tez(5))
    scenario += ctrl.verifyProof(sp.record(address=user.address,prooftype='email')).run(sender = admin)
    scenario += ctrl.verifyProof(sp.record(address=user.address,prooftype='phone')).run(sender = admin)

    ## A user can remove a proof
    #
    scenario.verify(store.data.identities[user.address].contains('email') == True)
    scenario.verify(store.data.identities[user.address].contains('phone') == True)
    scenario += ctrl.removeProof('email').run(sender = user, amount = sp.tez(5))
    scenario.verify(store.data.identities[user.address].contains('email') == False)
    scenario.verify(store.data.identities[user.address].contains('phone') == True)
    
@sp.add_test(name = "Remove identity", is_default=runAll)
def test():
    admin = sp.test_account("admin")
    user = sp.test_account("User")

    scenario = sp.test_scenario()
    store, ctrl = initTests(admin, scenario)
    scenario += ctrl.registerProof('email').run(sender = user, amount = sp.tez(5))
    scenario += ctrl.verifyProof(sp.record(address=user.address,prooftype='email')).run(sender = admin)

    ## A user can remove self (and all proofs)
    #
    scenario.verify(store.data.identities.contains(user.address))
    scenario += ctrl.removeIdentity().run(sender = user, amount = sp.tez(5))
    scenario.verify(store.data.identities.contains(user.address) == False)

@sp.add_test(name = "Set cost", is_default=runAll)
def test():
    admin = sp.test_account("admin")
    user = sp.test_account("User")

    scenario = sp.test_scenario()
    store, ctrl = initTests(admin, scenario)

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
  
@sp.add_test(name = "Send", is_default=runAll)
def test():
    admin = sp.test_account("admin")
    user = sp.test_account("User")
    receiver = sp.test_account("Receiver")

    scenario = sp.test_scenario()
    store, ctrl = initTests(admin, scenario)
    scenario += ctrl.registerProof('email').run(sender = user, amount = sp.tez(5))

    ## Admin can send balance elsewhere
    #
    scenario += ctrl.send(sp.record(receiverAddress=receiver.address, amount=sp.tez(2))).run(sender = admin)
    scenario.verify(ctrl.balance == sp.tez(3))

    ## User cannot send
    #
    scenario += ctrl.send(sp.record(receiverAddress=receiver.address, amount=sp.tez(2))).run(sender = user, valid = False)
    
@sp.add_test(name = "Store send", is_default=runAll)
def test():
    admin = sp.test_account("admin")
    user = sp.test_account("User")
    receiver = sp.test_account("Receiver")

    scenario = sp.test_scenario()
    store, ctrl = initTests(admin, scenario)
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
    
@sp.add_test(name = "Set admin", is_default=runAll)
def test():
    admin = sp.test_account("admin")
    admin2 = sp.test_account("admin2")
    user = sp.test_account("user")

    scenario = sp.test_scenario()
    store, ctrl = initTests(admin, scenario)

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
    ctrl2 = TezIDController(admin.address, store.address, sp.tez(10))
    scenario += ctrl2
    scenario += ctrl.setStoreAdmin(ctrl2.address).run(sender = admin2)
    scenario.verify(store.data.admin == ctrl2.address)
    
    ## Users cannot set store admin via setStoreAdmin
    #
    scenario += ctrl.setStoreAdmin(user.address).run(sender = user, valid=False)
    scenario += ctrl.setStoreAdmin(admin.address).run(sender = admin, valid=False)
    
@sp.add_test(name = "Set store", is_default=runAll)
def test():
    admin = sp.test_account("admin")
    user = sp.test_account("User")

    scenario = sp.test_scenario()
    store, ctrl = initTests(admin, scenario)
    store2 = TezIDStore(admin.address, sp.big_map())
    scenario += store2

    ## Admin can update store
    #
    scenario.verify(ctrl.data.idstore == store.address)
    scenario += ctrl.setStore(store2.address).run(sender = admin)
    scenario.verify(ctrl.data.idstore == store2.address)

    ## User cannot update store
    #
    scenario += ctrl.setStore(store.address).run(sender = user, valid = False)
    
@sp.add_test(name = "Set baker", is_default=runAll)
def test():
    admin = sp.test_account("admin")
    user = sp.test_account("User")
    baker = sp.key_hash("tz1YB12JHVHw9GbN66wyfakGYgdTBvokmXQk")
    voting_powers = {
        baker: 0,
    }

    scenario = sp.test_scenario()
    store, ctrl = initTests(admin, scenario)

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
    
@sp.add_test(name = "Set proof metadata", is_default=runAll)
def test():
    admin = sp.test_account("admin")
    user = sp.test_account("User")

    scenario = sp.test_scenario()
    store, ctrl = initTests(admin, scenario)

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

@sp.add_test(name = "Enable KYC metadata", is_default=True)
def test():
    admin = sp.test_account("admin")
    user = sp.test_account("User")

    scenario = sp.test_scenario()
    store, ctrl = initTests(admin, scenario)

    ## Owner of gov proof can set metadata kyc: true
    #
    scenario += ctrl.registerProof('gov').run(sender = user, amount = sp.tez(5))
    scenario += ctrl.enableKYC().run(sender = user)
    scenario.verify_equal(store.data.identities[user.address]['gov'].meta['kyc'], "true")
    
    ## Updating proof should keep metadata
    #
    scenario += ctrl.verifyProof(sp.record(address=user.address, prooftype="gov")).run(sender = admin)
    scenario.verify_equal(store.data.identities[user.address]['gov'].verified, True)
    scenario.verify_equal(store.data.identities[user.address]['gov'].meta['kyc'], "true")


