import smartpy as sp

## Other Types
#

TProof = sp.TRecord(
    register_date = sp.TTimestamp,
    verified = sp.TBool,
    meta = sp.TMap(sp.TString, sp.TString)
)
TProofs = sp.TMap(sp.TString, TProof)
TSetProofs = sp.TMap(sp.TAddress, TProofs)
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

## Storage Types
#

TStoreStorage = sp.TRecord(
  admins = sp.TSet(sp.TAddress),
  identities = TIdentities,
  metadata = sp.TBigMap(sp.TString, sp.TBytes)
)

## Labmda Types
#

TStoreLambdaParams = sp.TRecord(
  storage = TStoreStorage,
  params = sp.TBytes
)
