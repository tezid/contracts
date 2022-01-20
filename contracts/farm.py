import os
import smartpy as sp

cwd = os.getcwd()
Types = sp.io.import_script_from_url("file://%s/contracts/types.py" % cwd)

## TODO: proofToken

## TezID Forever Farm
#

class TezIDForeverFarm(sp.Contract):
  def __init__(self, admins, metadata):
    self.init(
      admins = admins, 
      metadata = metadata,
      stakers = sp.big_map({}),
      rewards = sp.map({}),
      paused = False,
      totalStaked = 0,
      stakeToken = sp.record(
        address  = sp.none,
        token_id = 0
      ),
      rewardToken = sp.record(
        address  = sp.none,
        token_id = 0
      ),
      daoToken = sp.record(
        address  = sp.none,
        token_id = 0
      )
      burnAddress = sp.none
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
  def getTokenValue(self):
    tokenValue = self.data.rewardPool / self.data.totalStaked  
    sp.result(tokenValue)


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

  ## Reward 
  #

  @sp.entry_point
  def addRewards(self, amount):
    self.checkAdmin()
    self.TransferTokens(sp.record(
      sender=sp.sender, 
      receiver=sp.self_address, 
      token=self.data.rewardToken.address.open_some('rewardToken address not set'),
      ids=[self.data.rewardToken.token_id],
      amount=amount
    ))
    self.data.rewardPool += amount

  ## Stake
  #

  @sp.entry_point
  def stake(self, amount):
    self.checkNotPaused()
    self.data.totalStaked += amount
    tokenValue = self.getTokenValue()
    rewardTokenPaymentRequired = tokenValue * amount
    self.data.rewardPool += rewardTokenPaymentRequired 

    # Claim stakeTokens
    self.TransferTokens(sp.record(
      sender=sp.sender, 
      receiver=sp.self_address, 
      token=self.data.stakeToken.address.open_some('stakeToken address not set'),
      ids=[self.data.stakeToken.token_id],
      amount=amount
    ))
    # Return daoTokens
    self.TransferTokens(sp.record(
      sender=sp.self_address, 
      receiver=sp.sender, 
      token=self.data.daoToken.address.open_some('daoToken address not set'),
      ids=[self.data.daoToken.token_id],
      amount=amount
    ))
    # Claim rewardTokens
    self.TransferTokens(sp.record(
      sender=sp.sender, 
      receiver=sp.self_address, 
      token=self.data.rewardToken.address.open_some('rewardToken address not set'),
      ids=[self.data.rewardToken.token_id],
      amount=rewardTokenPaymentRequired
    ))

  ## Exit
  #

  @sp.entry_point
  def exit(self, amount):
    self.checkNotPaused()
    self.data.totalStaked -= amount
    tokenValue = self.getTokenValue()
    rewardTokenPayment = tokenValue * amount
    self.data.rewardPool -= rewardTokenPayment

    # Return stakeToken
    self.TransferTokens(sp.record(
      sender=sp.self_address, 
      receiver=sp.sender, 
      token=self.data.stakeToken.address.open_some('stakeToken address not set'),
      ids=[self.data.stakeToken.token_id],
      amount=amount
    ))
    # Burn daoTokens
    self.TransferTokens(sp.record(
      sender=sp.sender, 
      receiver=self.data.burnAddress.open_some('brunAddress not set'), 
      token=self.data.daoToken.address.open_some('daoToken address not set'),
      ids=[self.data.daoToken.token_id],
      amount=amount
    ))
    # Return rewardTokens
    self.TransferTokens(sp.record(
      sender=sp.self_address, 
      receiver=sp.sender, 
      token=self.data.rewardToken.address.open_some('rewardToken address not set'),
      ids=[self.data.rewardToken.token_id],
      amount=rewardTokenPayment
    ))

