import * as Types from './Types';

type TStoreStorage = TRecord<{
  admin: TAddress;
  identities: Types.TIdentities
}> 

@Contract
export class TezIDStore {
  constructor(public storage: TStoreStorage) {
    admin = storage.admin
    identities = storage.identities
  }

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
  setBaker(new_delegate: TAddress): void {
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
    const contract: TContract<TUnit> = Sp.contract<TUnit>(receiverAddress, "").openSome("Invalid Interface");
    Sp.transfer(Sp.unit, amount, contract)
  }

  @EntryPoint
  setProof(address: TAddress, prooftype: TString, proof: Types.TProof): void {
    if (Sp.sender != this.storage.admin) {
      Sp.failWith("Only admin can setProof")
    }
    if (!this.storage.identities.contains(address)) {
      this.storage.identities.set(address, {})
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
    Sp.transfer(res, 0, contract)
  }
}
