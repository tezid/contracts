import * as Types from './Types';

@Contract
export class Prover {
  constructor(public storage: Types.TMerkleProverStorage = { root: '', verified: false }) {}

  @EntryPoint
  hashTest(a: TBytes, b: TBytes, c: TBytes): void {
    const _c = Sp.sha256(Sp.concat([a,b]))
    if (c == _c) {
      this.storage.verified = true
    } 
  }

  @EntryPoint
  verify(leaf: TBytes, proof: Types.TMerkleProof): void {
    let verified = false
    if (proof.size() === 0) {
      Sp.failWith('Invalid proof')
    }
    if (leaf === this.storage.root) {
      verified = true 
    }

    let currentRoot = leaf
    for (let branch of proof) {
      if (branch.left !== currentRoot && branch.right !== currentRoot) {
        Sp.failWith('Current root is neither left nor right value')
      }

      const parentBytes = Sp.concat([branch.left, branch.right])
      const parentHash = Sp.sha256(parentBytes)

      if (branch.parent != parentHash) {
        Sp.failWith('Incorrect parent hash')
      }
      currentRoot = branch.parent
    }

    if (currentRoot == this.storage.root) {
      verified = true
    }

    this.storage.verified = verified
  }
}

Dev.test({ name: 'Prover' }, () => {

  const root: TBytes = '0xff9fcd7c0961396996e4e6db9fa04d1a3de61465e7ed6a4edd650e02c82c08b5'
  const leaf: TBytes = '0xa079fcef2a3e809005f55d0e10ecbe352e22d1dceeed9c70bd6b3692abb53ebe'
  const proof = [
    {
      left: '0x7d32da12c80c7ab09e7a407277f286fd13643319bb49d95d3b9e6b6936c5a784' as TBytes,
      parent: '0xb1d06f4340eec73c12989f3a7c59008b85541a3196b23263f64da839a4fe355a' as TBytes,
      right: '0xa079fcef2a3e809005f55d0e10ecbe352e22d1dceeed9c70bd6b3692abb53ebe' as TBytes
    },
    {
      left: '0xb1d06f4340eec73c12989f3a7c59008b85541a3196b23263f64da839a4fe355a' as TBytes,
      parent: '0xff9fcd7c0961396996e4e6db9fa04d1a3de61465e7ed6a4edd650e02c82c08b5' as TBytes,
      right: '0x9cd16040df67f24572b7d4b90c37b7dbaae5d630192f1da9123106e198b6fe7d' as TBytes
    }
  ]

  Scenario.h1('Originating Contract')
  const c1 = Scenario.originate(new Prover({ root: root, verified: false }))
  Scenario.p('Initial value for root must be root.')
  Scenario.verify(c1.storage.root == root)

  Scenario.h1('Verify valid proof')
  Scenario.transfer(c1.verify(leaf, proof))
  Scenario.verify(c1.storage.verified == true)
})

Dev.compileContract('prover', new Prover())
