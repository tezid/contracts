export type TStorage = TRecord<{
  root: TBytes;
  verified: TBool;
}>

export type TMerkleBranch = TRecord<{
  left: TBytes;
  right: TBytes;
  parent: TBytes;
}>

export type TMerkleProof = TList<TMerkleBranch>
