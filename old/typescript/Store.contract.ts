import * as Types from './Types';

type TStoreStorage = TRecord<{
  admin: TAddress;
  identities: Types.TIdentities;
}> 

@Contract
export class TezIDStore {
  constructor(public storage: TStoreStorage) {}

  @EntryPoint
  default(): void {
    pass
  }

  @EntryPoint
  setAdmin(new_admin: TAddress): void {
    if (Sp.sender != this.storage.admin) {
      Sp.failWith("Only admin can setAdmin")
    }
    this.storage.admin = new_admin
  }

  @EntryPoint
  setBaker(new_delegate: TOption<TKey_hash>): void {
    if (Sp.sender != this.storage.admin) {
      Sp.failWith("Only admin can setBaker")
    }
    Sp.setDelegate(new_delegate)
  }
      
  @EntryPoint
  send(receiverAddress: TAddress, amount: TMutez): void {
    if (Sp.sender != this.storage.admin) {
      Sp.failWith("Only admin can send")
    }
    const contract: TContract<TUnit> = Sp.contract<TUnit>(receiverAddress, "").openSome("Invalid receiver");
    Sp.transfer(Sp.unit, amount, contract)
  }

  @EntryPoint
  setProof(address: TAddress, prooftype: TString, proof: Types.TProof): void {
    if (Sp.sender != this.storage.admin) {
      Sp.failWith("Only admin can setProof")
    }
    if (!this.storage.identities.contains(address)) {
      this.storage.identities.set(address, [] as Types.TProofs)
    }
    this.storage.identities.get(address).set(prooftype, proof)
  }
      
  @EntryPoint
  delProof(address: TAddress, prooftype: TString): void {
    if (Sp.sender != this.storage.admin) {
      Sp.failWith("Only admin can delProof")
    }
    this.storage.identities.get(address).remove(prooftype)
  }
      
  @EntryPoint
  removeIdentity(address: TAddress): void {
    if (Sp.sender != this.storage.admin) {
      Sp.failWith("Only admin can removeIdentity")
    }
    this.storage.identities.remove(address)
  }

  @EntryPoint
  getProofs(address: TAddress, callback_address: TContract): void {
    let proofs = {}
    if (this.storage.identities.contains(address)) {
      proofs = this.storage.identities.get(address)
    }
    const res: Types.TGetProofsResponsePayload = { address = address, proofs = proofs }
    const contract: TContract<Types.TGetProofsResponsePayload> = Sp.contract<Types.TGetProofsResponsePayload>(callback_address).openSome("Invalid Interface");
    Sp.transfer(res, 0 as TMutez, contract)
  }
}

Dev.test({ name: 'Store' }, () => {

  /*** Init ***/

  const admin1 = Scenario.testAccount("Admin1")
  const admin2 = Scenario.testAccount("Admin2")
  const user1  = Scenario.testAccount("User1")
  const user2  = Scenario.testAccount("User2")
  const store  = Scenario.originate(new TezIDStore({
    admin: admin1.address,
    identities: [] 
  }))

  /*** Set admin ***/

  Scenario.verify(store.storage.admin == admin1.address)
  Scenario.transfer(store.setAdmin(admin2.address), { sender: admin1.address })
  Scenario.verify(store.storage.admin == admin2.address)
  Scenario.transfer(store.setAdmin(admin1.address), { sender: admin2.address })
  Scenario.verify(store.storage.admin == admin1.address)

  /*** Set baker ***/

  const baker: TKey_hash = "tz1eWtg7YQb5iLX2HvrHPGbhiCQZ8n98aUh5"
  const votingPowers = [[baker: 0]]
  Scenario.verify(store.baker == Sp.none)
  // Admin can update baker
  Scenario.transfer(store.setBaker(Sp.some(baker)), { sender: admin1.address, votingPowers: votingPowers })
  Scenario.verify(store.baker == Sp.some(baker))
  // User cannot update baker 
  Scenario.transfer(store.setBaker(Sp.some(baker)), { sender: user1.address, votingPowers: votingPowers, valid: false })

  /*** Transfer funds ***/

  Scenario.transfer(store.default(), { sender: user1.address, amount: 10 as TMutez })
  Scenario.verify(store.balance == 10 as TMutez)
  // Admin can send
  Scenario.transfer(store.send(user2.address, 5 as TMutez), { sender: admin1.address })
  Scenario.verify(store.balance == 5 as TMutez)
  // User cannot send
  Scenario.transfer(store.send(user2.address, 5 as TMutez), { sender: user2.address, valid: false })

  /*** Set proof ***/

  const proof1: Types.TProof = {
    meta: [],
    verified: false,
    register_date: 1571761674 as TTimestamp
  }
  // Admin can set proof
  Scenario.transfer(store.setProof(user1.address, 'email', proof1), { sender: admin1.address })
  Scenario.verify(store.storage.identities.get(user1.address).get('email').verified == false)
  // User cannot set proof
  Scenario.transfer(store.setProof(user1.address, 'phone', proof1), { sender: user1.address, valid: false })

  /*** Del proof ***/

  Scenario.transfer(store.delProof(user1.address, 'email'), { sender: user1.address, valid: false })
  Scenario.transfer(store.delProof(user1.address, 'email'), { sender: admin1.address })
  Scenario.verify(store.storage.identities.get(user1.address).hasKey('email') == false)

  /*** Remove identity ***/

  Scenario.transfer(store.removeIdentity(user1.address), { sender: user1.address, valid: false })
  Scenario.transfer(store.removeIdentity(user1.address), { sender: admin1.address })
  Scenario.verify(store.storage.identities.hasKey(user1.address) == false)

})

