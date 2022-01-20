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
    admin = admin, 
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
  mint(scene, admin, daoToken, 0, admin, 1000000, decimals=8, name='TezIDAO Token', symbol='xIDZ')

  scene += farm.setToken(sp.record(tokenType="stake", tokenAddress=stakeToken.address, tokenId=0)).run(sender=admin)
  scene += farm.setToken(sp.record(tokenType="dao", tokenAddress=daoToken.address, tokenId=0)).run(sender=admin)
  scene += farm.setToken(sp.record(tokenType="reward", tokenAddress=rewardToken.address, tokenId=0)).run(sender=admin)

  return farm, stakeToken, daoToken, rewardToken


@sp.add_target(name = "Farm", kind=allKind)
def test():
  admin = sp.address("tz1-admin")
  user1 = sp.address("tz1-user-1")
  user2 = sp.address("tz1-user-2")

  scene = sp.test_scenario()
  farm, stakeToken, daoToken, rewardToken = init(admin, scene)

  
