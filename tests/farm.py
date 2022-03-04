import os
import smartpy as sp

cwd = os.getcwd()
Types = sp.io.import_script_from_url("file://%s/contracts/types.py" % cwd)
Tokens = sp.io.import_script_from_url("file://%s/contracts/tokens.py" % cwd)
Farm = sp.io.import_script_from_url("file://%s/contracts/farm.py" % cwd)

## Tests
#

allKind = 'all'

def mint(scene, admin, token, token_id, owner, amount, decimals=8, name='TestToken', symbol='TST'):
  scene += token.mint(
    address = owner,
    amount = amount,
    metadata = Tokens.FA2Token.make_metadata(
      decimals = decimals,
      name = name,
      symbol = symbol
    ),
    token_id = token_id
  ).run(sender = admin)

def transfer(scene, token, sender, receiver, amount, token_id=0):
  txs = [sp.record(amount=amount, to_=receiver, token_id=token_id)]
  arg = [sp.record(from_=sender, txs=txs)]
  scene += token.transfer(arg).run(sender=sender)

def operator(scene, token, owner, operator, token_id=0, operation='add_operator'):
  scene += token.update_operators([
    sp.variant(operation, sp.record(
      owner = owner,
      operator = operator,
      token_id = token_id
    ))
  ]).run(sender = owner)

def init(admin, scene):
  farm = Farm.TezIDForeverFarm(
    sp.set([admin]), 
    sp.big_map(
      {
        "": sp.utils.bytes_of_string("tezos-storage:content"),
        "content": sp.utils.bytes_of_string('{"name": "TezID Farm"}')
      }
    )
  )
  scene += farm 

  stakeToken = Tokens.FA2Token(
    Tokens.TOKEN_config,
    admin = admin, 
    metadata = sp.big_map(
      {
        "": sp.utils.bytes_of_string("tezos-storage:content"),
        "content": sp.utils.bytes_of_string("""{"name" : "StakeToken"}""")
      }
    )
  )
  scene += stakeToken

  daoToken = Tokens.FA2Token(
    Tokens.TOKEN_config,
    admin = farm.address, 
    metadata = sp.big_map(
      {
        "": sp.utils.bytes_of_string("tezos-storage:content"),
        "content": sp.utils.bytes_of_string("""{"name" : "daoToken"}""")
      }
    )
  )
  scene += daoToken

  rewardToken = Tokens.FA2Token(
    Tokens.TOKEN_config,
    admin = admin, 
    metadata = sp.big_map(
      {
        "": sp.utils.bytes_of_string("tezos-storage:content"),
        "content": sp.utils.bytes_of_string("""{"name" : "rewardToken"}""")
      }
    )
  )
  scene += rewardToken

  mint(scene, admin, stakeToken, 0, admin, 1000000, decimals=8, name='IDZ/XTZ LP', symbol='IDZLP')
  mint(scene, admin, rewardToken, 0, admin, 1000000, decimals=8, name='TezID Token', symbol='IDZ')

  scene += farm.setToken(sp.record(tokenType="stake", tokenAddress=stakeToken.address, tokenId=0)).run(sender=admin)
  scene += farm.setToken(sp.record(tokenType="dao", tokenAddress=daoToken.address, tokenId=0)).run(sender=admin)
  scene += farm.setToken(sp.record(tokenType="reward", tokenAddress=rewardToken.address, tokenId=0)).run(sender=admin)
  scene += farm.setBurnAddress(sp.address('tz1-burn')).run(sender=admin)

  return farm, stakeToken, daoToken, rewardToken

@sp.add_target(name = "Admin", kind=allKind)
def test():
  admin = sp.address("tz1-admin")
  user1 = sp.address("tz1-user-1")
  user2 = sp.address("tz1-user-2")

  scene = sp.test_scenario()
  farm, stakeToken, daoToken, rewardToken = init(admin, scene)

  # Farm admin can set daoToken admin

  scene.verify(daoToken.data.administrator == farm.address)
  scene += farm.setTokenAdmin(sp.record(tokenAddress=daoToken.address, admin=admin)).run(sender=admin)
  scene.verify(daoToken.data.administrator == admin)

@sp.add_target(name = "Farm", kind=allKind)
def test():
  admin = sp.address("tz1-admin")
  user1 = sp.address("tz1-user-1")
  user2 = sp.address("tz1-user-2")

  scene = sp.test_scenario()
  farm, stakeToken, daoToken, rewardToken = init(admin, scene)

  # User1 and User2 gets some stakeTokens

  transfer(scene, stakeToken, admin, user1, 100)
  transfer(scene, stakeToken, admin, user2, 50)
  scene.verify(stakeToken.data.ledger[user1].balance == 100)
  scene.verify(stakeToken.data.ledger[user2].balance == 50)

  # User 1 and User 2 both set farm as operator
  operator(scene, daoToken, user1, farm.address)
  operator(scene, stakeToken, user1, farm.address)
  operator(scene, rewardToken, user1, farm.address)
  operator(scene, daoToken, user2, farm.address)
  operator(scene, stakeToken, user2, farm.address)
  operator(scene, rewardToken, user2, farm.address)

  # Admin set farm as operator for rewardTokens
  operator(scene, rewardToken, admin, farm.address) 

  # User1 stakes (since no rewards yet, only stakeToken required)
  scene += farm.stake(100).run(sender=user1)
  scene.verify(farm.data.totalStaked == 100)
  scene.verify(daoToken.data.ledger[user1].balance == 100)
  scene.verify(stakeToken.data.ledger[user1].balance == 0)

  # Admin adds some rewards
  scene += farm.addRewards(1000).run(sender=admin)
  scene.verify(farm.data.rewardPool == 1000)

  # User2 stakes (reward tokens are now required)
  transfer(scene, rewardToken, admin, user2, 50)
  scene += farm.stake(50).run(sender=user2, valid=False, exception='FA2_INSUFFICIENT_BALANCE')
  transfer(scene, rewardToken, admin, user2, 450)
  scene += farm.stake(50).run(sender=user2)
  scene.verify(farm.data.totalStaked == 150)
  scene.verify(farm.data.rewardPool == 1500)

  # User 2 exits half
  scene += farm.exit(25).run(sender=user2)
  scene.verify(stakeToken.data.ledger[user2].balance == 25)
  scene.verify(daoToken.data.ledger[user2].balance == 25)
  scene.verify(rewardToken.data.ledger[user2].balance == 250)
  scene.verify(farm.data.totalStaked == 125)
  scene.verify(farm.data.rewardPool == 1250)

  # User 2 cannot exit more than stake
  scene += farm.exit(30).run(sender=user2, valid=False, exception='FA2_INSUFFICIENT_BALANCE')

  # Admin adds some more rewards
  scene += farm.addRewards(1000).run(sender=admin)
  scene.verify(farm.data.rewardPool == 2250)

  # User 1 exits
  scene += farm.exit(100).run(sender=user1)
  scene.verify(daoToken.data.ledger[user1].balance == 0)
  scene.verify(stakeToken.data.ledger[user1].balance == 100)
  scene.verify(rewardToken.data.ledger[user1].balance == 1800) # Total rewards for user1 = 1800

  # User 2 exits rest
  scene += farm.exit(25).run(sender=user2)
  scene.verify(daoToken.data.ledger[user2].balance == 0)
  scene.verify(stakeToken.data.ledger[user2].balance == 50)
  scene.verify(rewardToken.data.ledger[user2].balance == 700) # Total rewards for user2 = 700-500 = 200

  # Farm is reset
  scene.verify(farm.data.rewardPool == 0)
  scene.verify(farm.data.totalStaked == 0)

@sp.add_target(name = "Farm Complex", kind=allKind)
def test():
  admin = sp.address("tz1-admin")
  user1 = sp.address("tz1-user-1")
  user2 = sp.address("tz1-user-2")
  user3 = sp.address("tz1-user-3")
  user1Amount = 1333
  user2Amount = 44
  user3Amount = 27

  scene = sp.test_scenario()
  farm, stakeToken, daoToken, rewardToken = init(admin, scene)

  # Users gets some stakeTokens

  transfer(scene, stakeToken, admin, user1, user1Amount)
  transfer(scene, stakeToken, admin, user2, user2Amount)
  transfer(scene, stakeToken, admin, user3, user3Amount)

  # Users set farm as operator
  operator(scene, daoToken, user1, farm.address)
  operator(scene, stakeToken, user1, farm.address)
  operator(scene, rewardToken, user1, farm.address)
  operator(scene, daoToken, user2, farm.address)
  operator(scene, stakeToken, user2, farm.address)
  operator(scene, rewardToken, user2, farm.address)
  operator(scene, daoToken, user3, farm.address)
  operator(scene, stakeToken, user3, farm.address)
  operator(scene, rewardToken, user3, farm.address)
  # Admin set farm as operator for rewardTokens
  operator(scene, rewardToken, admin, farm.address) 
  # Admin transfers some rewardTokens to user3 (required for their staking)
  transfer(scene, rewardToken, admin, user3, 500)

  # User1 stakes (since no rewards yet, only stakeToken required)
  scene += farm.stake(user1Amount).run(sender=user1)
  scene += farm.stake(user2Amount).run(sender=user2)
  scene.verify(farm.data.totalStaked == (user1Amount + user2Amount))

  # Admin adds some rewards
  scene += farm.addRewards(10000).run(sender=admin)
  scene.verify(farm.data.rewardPool == 10000)

  # User2 exits half 
  scene += farm.exit(int(user2Amount/2)).run(sender=user2)
  # User3 stakes all
  scene += farm.stake(user3Amount).run(sender=user3)

  # Admin adds some more rewards
  scene += farm.addRewards(1371).run(sender=admin)

  # Users exits 
  scene += farm.exit(user1Amount).run(sender=user1)
  scene += farm.exit(int(user2Amount/2)).run(sender=user2)
  scene += farm.exit(user3Amount).run(sender=user3)

  # Farm is reset
  scene.verify(farm.data.rewardPool >= 0) # Because of eucludian division we might have a small remainder in the rewardPool
  scene.verify(farm.data.totalStaked == 0)

  # Admin can send remainig rewards and reset pool
  scene.verify(farm.data.rewardPool == 350)
  scene += farm.adminTransferTokens(sp.record(
    sender=farm.address, 
    receiver=admin, 
    tokenAddress=rewardToken.address, 
    token_ids=[0], 
    amount=351
  )).run(sender=admin, valid=False, exception='FA2_INSUFFICIENT_BALANCE')
  scene += farm.adminTransferTokens(sp.record(
    sender=farm.address, 
    receiver=admin, 
    tokenAddress=rewardToken.address, 
    token_ids=[0], 
    amount=350
  )).run(sender=admin)
  scene += farm.setRewardPool(0).run(sender=admin)
  scene.verify(farm.data.rewardPool == 0)
