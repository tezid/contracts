/* Store types */

export type TProof = TRecord<{
  meta: TMap<TString, TString>;
  verified: TBool;
  register_date: TTimestamp;
}>

export type TProofs = TMap<TString, TProof>

export type TIdentities = TBig_map<TAddress, TProofs>

export type TSendPayload = TRecord<{
  amount: TMutez;
  receiverAddress: TAddress;
}> 

export type TSetProofPayload = TRecord<{
  proof: TProof;
  address: TAddress;
  prooftype: TString;
}>

export type TDelProofPayload = TRecord<{
  address: TAddress;
  prooftype: TString;
}>

export type TGetProofsRequestPayload = TRecord<{
  address: TAddress, 
  callback_address: TAddress
}>

export type TGetProofsResponsePayload = TRecord<{
  proofs: TProofs;
  address: TAddress;
}>

/* MerkleProver */

export type TMerkleProverStorage = TRecord<{
  root: TBytes;
  verified: TBool;
}>

export type TMerkleBranch = TRecord<{
  left: TBytes;
  right: TBytes;
  parent: TBytes;
}>

export type TMerkleProof = TList<TMerkleBranch>
