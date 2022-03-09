import os
import smartpy as sp

cwd = os.getcwd()
Types = sp.io.import_script_from_url("file://%s/contracts/types.py" % cwd)

def bytes_of_string(s):
  b = sp.pack(s)
  return sp.slice(b, 6, sp.as_nat(sp.len(b) - 6)).open_some("Could not get bytes of string")

## TezID Forever Farm
#

class TezIDForeverFarm(sp.Contract):
  def __init__(self, admins, metadata):
    self.init(
      admins = admins, 
      metadata = metadata,
      paused = False,
      totalStaked = 0,
      rewardPool = 0,
      tokenValue = 0,
      tokens = sp.map({}),
      burnAddress = sp.none,
      xidzMetadata = sp.map({
        'name': bytes_of_string('TezIDAO xIDZ'),
        'symbol': bytes_of_string('xIDZ'),
        'decimals': bytes_of_string('6'),
        'description': bytes_of_string('TezID xFarm proof token'),
        'thumbnailUri': bytes_of_string('https://tezid.net/xidz.png'),
        'shouldPreferSymbol': bytes_of_string('true')
      })
    )

  ## Utility Functions
  #

  @sp.private_lambda(with_storage='read-only', with_operations=True, wrap_call=True)
  def TransferTokens(self, params):
      txs = sp.local('txs', [])
      sp.for _id in params.ids:
        txs.value.push(sp.record(
          to_      = params.receiver,
          token_id = _id,
          amount   = params.amount 
        )) 
      arg = [
        sp.record(
          from_ = params.sender,
          txs = txs.value
        )
      ]

      transferHandle = sp.contract(
          sp.TList(sp.TRecord(from_ = sp.TAddress, txs = sp.TList(sp.TRecord(amount = sp.TNat, to_ = sp.TAddress, token_id = sp.TNat).layout(("to_", ("token_id", "amount")))))), 
          params.token,
          entry_point='transfer').open_some()

      sp.transfer(arg, sp.mutez(0), transferHandle)

  @sp.private_lambda(with_storage='read-only', with_operations=True, wrap_call=True)
  def MintTokens(self, params):
    arg = sp.record(
      address = params.receiver,
      amount = params.amount,
      metadata = self.data.xidzMetadata,
      token_id = params.token_id
    )
    mintHandle = sp.contract(
      sp.TRecord(address=sp.TAddress, amount=sp.TNat, metadata=sp.TMap(sp.TString, sp.TBytes), token_id=sp.TNat),
      params.token_address,
      entry_point='mint').open_some('No such entrypoint')
    sp.transfer(arg, sp.mutez(0), mintHandle)

  ## Checks
  #

  @sp.private_lambda(with_storage='read-only', wrap_call=True)
  def checkAdmin(self):
    sp.verify(self.data.admins.contains(sp.sender), 'Only admin can call this entrypoint')    

  @sp.private_lambda(with_storage='read-only', wrap_call=True)
  def checkNotPaused(self):
    sp.verify(self.data.paused != True, 'Farm paused')

  ## Default
  #

  @sp.entry_point
  def default(self):
    pass

  ## Admin entrypoints
  #
   
  @sp.entry_point
  def addAdmin(self, admin):
    self.checkAdmin()
    self.data.admins.add(admin)

  @sp.entry_point
  def delAdmin(self, admin):
    self.checkAdmin()
    self.data.admins.remove(admin)

  @sp.entry_point
  def tooglePause(self, paused):
    self.checkAdmin()
    self.data.paused = paused

  @sp.entry_point
  def setBaker(self, new_delegate):
    self.checkAdmin()
    sp.set_delegate(new_delegate)
      
  @sp.entry_point
  def send(self, receiverAddress, amount):
    self.checkAdmin()
    sp.send(receiverAddress, amount)

  @sp.entry_point
  def adminTransferTokens(self, sender, receiver, tokenAddress, token_ids, amount):
    self.checkAdmin()
    self.TransferTokens(sp.record(
      sender=sender, 
      receiver=receiver, 
      token=tokenAddress, 
      ids=token_ids, 
      amount=amount
    ))

  @sp.entry_point
  def setToken(self, tokenType, tokenAddress, tokenId):
    self.checkAdmin()
    self.data.tokens[tokenType] = sp.record(
      address = tokenAddress,
      token_id = tokenId
    )

  @sp.entry_point
  def setBurnAddress(self, burnAddress):
    self.checkAdmin()
    sp.set_type(burnAddress, sp.TAddress)
    self.data.burnAddress = sp.some(burnAddress)

  @sp.entry_point
  def setRewardPool(self, rewardPool):
    self.checkAdmin()
    self.data.rewardPool = rewardPool

  @sp.entry_point
  def setTokenValue(self, tokenValue):
    self.checkAdmin()
    self.data.tokenValue = tokenValue 

  @sp.entry_point
  def setTotalStaked(self, totalStaked):
    self.checkAdmin()
    self.data.totalStaked = totalStaked

  @sp.entry_point
  def setTokenAdmin(self, tokenAddress, admin):
    self.checkAdmin()
    c = sp.contract(sp.TAddress, tokenAddress, entry_point="set_administrator").open_some()
    sp.transfer(admin, sp.mutez(0), c)

  ## Reward 
  #

  @sp.entry_point
  def addRewards(self, amount):
    self.checkAdmin()
    self.TransferTokens(sp.record(
      sender=sp.sender, 
      receiver=sp.self_address, 
      token=self.data.tokens['reward'].address,
      ids=[self.data.tokens['reward'].token_id],
      amount=amount
    ))
    self.data.rewardPool += amount
    sp.if self.data.totalStaked == 0:
      self.data.tokenValue = 0
    sp.else:
      self.data.tokenValue = self.data.rewardPool // self.data.totalStaked

  ## Stake
  #

  @sp.entry_point
  def stake(self, amount):
    self.checkNotPaused()

    rewards = self.data.tokenValue * amount
    self.data.totalStaked += amount 
    self.data.rewardPool += rewards

    #sp.trace('--stake--')
    #sp.trace(sp.sender)
    #sp.trace(amount)
    #sp.trace(rewards)
    #sp.trace(self.data.rewardPool)

    # stakeTokens - sender -> contract
    self.TransferTokens(sp.record(
      sender=sp.sender, 
      receiver=sp.self_address, 
      token=self.data.tokens['stake'].address,
      ids=[self.data.tokens['stake'].token_id],
      amount=amount
    ))
    # daoTokens - contract -> sender
    self.MintTokens(sp.record(
      amount=amount,
      receiver=sp.sender,
      token_id=self.data.tokens['dao'].token_id,
      token_address=self.data.tokens['dao'].address,
    ))
    # rewardTokens - sender -> contract
    sp.if rewards > 0:
      self.TransferTokens(sp.record(
        sender=sp.sender, 
        receiver=sp.self_address, 
        token=self.data.tokens['reward'].address,
        ids=[self.data.tokens['reward'].token_id],
        amount=rewards
      ))

  ## Exit
  #

  @sp.entry_point
  def exit(self, amount):
    self.checkNotPaused()

    rewards = self.data.tokenValue * amount
    self.data.totalStaked = sp.as_nat(self.data.totalStaked - amount, 'Negative totalStaked')
    self.data.rewardPool = sp.as_nat(self.data.rewardPool - rewards, 'Negative rewardPool')

    #sp.trace('--exit--')
    #sp.trace(sp.sender)
    #sp.trace(amount)
    #sp.trace(rewards)
    #sp.trace(self.data.rewardPool)

    # stakeToken - contract -> sender
    self.TransferTokens(sp.record(
      sender=sp.self_address, 
      receiver=sp.sender, 
      token=self.data.tokens['stake'].address,
      ids=[self.data.tokens['stake'].token_id],
      amount=amount
    ))
    # daoTokens - sender -> burn
    self.TransferTokens(sp.record(
      sender=sp.sender, 
      receiver=self.data.burnAddress.open_some('burnAddress not set'), 
      token=self.data.tokens['dao'].address,
      ids=[self.data.tokens['dao'].token_id],
      amount=amount
    ))
    # rewardTokens - contract -> sender
    self.TransferTokens(sp.record(
      sender=sp.self_address, 
      receiver=sp.sender, 
      token=self.data.tokens['reward'].address,
      ids=[self.data.tokens['reward'].token_id],
      amount=rewards
    ))

