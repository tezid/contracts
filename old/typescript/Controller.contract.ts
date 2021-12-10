import * as Types from './Types';

type TControllerStorage = TRecord<{
  cost: TMutez;
  admin: TAddress;
  idstore: TAddress;
  updateProofCache: TMap<TAddress, TMap<TString, TString>>;
}> 

@Contract
export class TezIDController {
  constructor(public storage: TControllerStorage) {}

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
}

Dev.test({ name: 'Controller' }, () => {

  /*** Init ***/

  const admin1 = Scenario.testAccount("Admin1")
  const admin2 = Scenario.testAccount("Admin2")
  const user1  = Scenario.testAccount("User1")
  const user2  = Scenario.testAccount("User2")
//  const store  = Scenario.originate(new Store.TezIDStore({
//    admin: admin1.address,
//    identities: [] 
//  }))
  const controller = Scenario.originate(new TezIDController({
    cost: 5,
    admin: admin1.address,
    idstore: admin1.address,
    updateProofCache: [] 
  }))

  /*** Set admin ***/

  Scenario.verify(controller.storage.admin == admin1.address)
  Scenario.transfer(controller.setAdmin(admin2.address), { sender: admin1.address })
  Scenario.verify(controller.storage.admin == admin2.address)
  Scenario.transfer(controller.setAdmin(admin1.address), { sender: admin2.address })
  Scenario.verify(controller.storage.admin == admin1.address)
})
