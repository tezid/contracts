import os
import smartpy as sp

cwd = os.getcwd()
Types = sp.io.import_script_from_url("file://%s/contracts/types.py" % cwd)

## TezID Forever Farm
#

class TezIDForeverFarm(sp.Contract):
  def __init__(self, admins, metadata):
    self.init(
      admins = admins, 
      metadata = metadata,
      paused = False,
      bootstrapping = False,
      totalStaked = 0,
      rewardPool = 0,
      tokens = sp.map({}),
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
    res = sp.local('res', 0)
    sp.if self.data.totalStaked > 0:
      sp.if self.data.rewardPool >= self.data.totalStaked:
        res.value = self.data.rewardPool // self.data.totalStaked
    sp.result(res.value)

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
  def toggleBootstrap(self, bootstrapping):
    self.checkAdmin()
    self.data.bootstrapping = bootstrapping 
      
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
  def setTotalStaked(self, totalStaked):
    self.checkAdmin()
    self.data.totalStaked = totalStaked

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

  ## Stake
  #

  @sp.entry_point
  def stake(self, amount):
    self.checkNotPaused()

    ## In case we have started adding rewards:
    #  --
    #  We cannot allow more stake than rewards since this will mess up arithmetic.
    #  This will never happen in a real world use-case, but we protect against it.
    #  However, when we are bootstrapping we want to allow staking while rewardPool = 0
    sp.if self.data.bootstrapping == False:
      sp.if self.data.rewardPool < (self.data.totalStaked + amount):
        sp.failwith('RewardPool too small')

    tokenValue = self.getTokenValue()
    rewardTokenPaymentRequired = tokenValue * amount
    self.data.totalStaked += amount 
    self.data.rewardPool += rewardTokenPaymentRequired 

#    sp.trace('--stake--')
#    sp.trace(sp.sender)
#    sp.trace(self.data.totalStaked)
#    sp.trace(self.data.rewardPool)
#    sp.trace(tokenValue)
#    sp.trace(rewardTokenPaymentRequired)

    # Claim stakeTokens
    self.TransferTokens(sp.record(
      sender=sp.sender, 
      receiver=sp.self_address, 
      token=self.data.tokens['stake'].address,
      ids=[self.data.tokens['stake'].token_id],
      amount=amount
    ))
    # Return daoTokens
    self.TransferTokens(sp.record(
      sender=sp.self_address, 
      receiver=sp.sender, 
      token=self.data.tokens['dao'].address,
      ids=[self.data.tokens['dao'].token_id],
      amount=amount
    ))
    # Claim rewardTokens
    sp.if rewardTokenPaymentRequired > 0:
      self.TransferTokens(sp.record(
        sender=sp.sender, 
        receiver=sp.self_address, 
        token=self.data.tokens['reward'].address,
        ids=[self.data.tokens['reward'].token_id],
        amount=rewardTokenPaymentRequired
      ))

  ## Exit
  #

  @sp.entry_point
  def exit(self, amount):
    self.checkNotPaused()

    tokenValue = self.getTokenValue()
    rewardTokenPayment = tokenValue * amount
    self.data.totalStaked = sp.as_nat(self.data.totalStaked - amount, 'Negative totalStaked')
    self.data.rewardPool = sp.as_nat(self.data.rewardPool - rewardTokenPayment, 'Negative rewardPool')

#    sp.trace('--exit--')
#    sp.trace(sp.sender)
#    sp.trace(self.data.totalStaked)
#    sp.trace(self.data.rewardPool)
#    sp.trace(tokenValue)
#    sp.trace(rewardTokenPayment)

    # Return stakeToken
    self.TransferTokens(sp.record(
      sender=sp.self_address, 
      receiver=sp.sender, 
      token=self.data.tokens['stake'].address,
      ids=[self.data.tokens['stake'].token_id],
      amount=amount
    ))
    # Burn daoTokens
    self.TransferTokens(sp.record(
      sender=sp.sender, 
      receiver=self.data.burnAddress.open_some('burnAddress not set'), 
      token=self.data.tokens['dao'].address,
      ids=[self.data.tokens['dao'].token_id],
      amount=amount
    ))
    # Return rewardTokens
    self.TransferTokens(sp.record(
      sender=sp.self_address, 
      receiver=sp.sender, 
      token=self.data.tokens['reward'].address,
      ids=[self.data.tokens['reward'].token_id],
      amount=rewardTokenPayment
    ))

