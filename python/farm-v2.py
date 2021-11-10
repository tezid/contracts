import smartpy as sp

FA2 = sp.io.import_script_from_url("https://smartpy.io/dev/templates/FA2.py")

class TestToken(FA2.FA2):
    pass

class Error:
    def make(s):
        return s
    
    NotAdmin = "NOT_ADMIN"
    NotStaked = "NOT_STAKED"
    WrongStatus = "WRONG_STATUS"
    
    ZeroAmount = "ZERO_AMOUNT"
    UnstakeMoreThanStake = "UNSTAKE_AMOUNT_GREATER_THAN_STAKE"

    WrongIndex = "WRONG_INDEX_FOR_MAP"
    Paused = "CONTRACT_PAUSED"


def buildDetails(amount, start, finish):
    return sp.record(
                rewardPerBlock = sp.nat(0),
                rewardPerTokenStored = sp.nat(0),
                lastUpdated = sp.nat(0),
                totalStaked = sp.nat(0),
                rewardsDistributed = sp.nat(0),
                finishLevel = finish,
                startLevel = start,
                tokensToReward = amount
            )

class IDZStaking(sp.Contract):
    def __init__(self, 
                admin,
                stake_address,
                stake_id,
                stake_decimal,
                reward_address, 
                reward_id,
                reward_decimal,
                amountToReward,
                start,
                finish):
        
        self.init(
            admin = admin,
            tokens = sp.record(
                stake = sp.record(address = stake_address, _id = stake_id, decimals = stake_decimal),
                reward = sp.record(address = reward_address, _id = reward_id, decimals = reward_decimal),
            ),
            details = buildDetails(amountToReward, start, finish),
            paused = False,
            balances = sp.big_map(
                tkey = sp.TAddress,
                tvalue = sp.TRecord(
                    staked = sp.TNat,
                    rewards = sp.TNat,
                    userRewardPerTokenPaid = sp.TNat
                )
            ),
        )
            
    @sp.entry_point
    def default(self):
        pass

    @sp.entry_point
    def startPool(self):
        self.checkAdmin()
        self.checkPaused()
        sp.verify(self.data.details.tokensToReward > 0, Error.ZeroAmount)
        
        self.TransferTokens(sp.sender, sp.self_address,
                            self.data.details.tokensToReward,
                            self.data.tokens.stake.address, self.data.tokens.stake._id)

        self.updateRewardPerBlock()
        self.updateRewards(sp.self_address)

    @sp.entry_point
    def refillPool(self, amount, start, finish):
        self.checkAdmin()
        self.checkFarmEnded()

        self.updateRewards(sp.self_address)
        self.data.details.tokensToReward = amount
        self.data.details.startLevel = start
        self.data.details.finishLevel = finish

        self.TransferTokens(sp.sender, sp.self_address,
                            self.data.details.tokensToReward,
                            self.data.tokens.stake.address, self.data.tokens.stake._id)

        self.updateRewardPerBlock()
        self.updateRewards(sp.self_address)                 
        

    @sp.entry_point
    def stake(self, amount):
        sp.set_type(amount, sp.TNat)
        self.checkPaused()

        sp.verify(sp.level < self.data.details.finishLevel)
        sp.verify(amount > 0, Error.ZeroAmount)

        sp.if ~self.data.balances.contains(sp.sender):
            self.data.balances[sp.sender] = sp.record(
                                                staked = 0, 
                                                rewards = 0, 
                                                userRewardPerTokenPaid = 0
                                            )

        self.updateRewards(sp.sender)
        self.TransferTokens(sp.sender, sp.self_address, 
                            amount, 
                            self.data.tokens.stake.address, self.data.tokens.stake._id)
        
        self.data.details.totalStaked += amount
        self.data.balances[sp.sender].staked += amount

    @sp.entry_point
    def unstake(self, amount):
        sp.set_type(amount, sp.TNat)
        
        self.checkPaused()
        sp.verify(self.data.balances.contains(sp.sender), Error.NotStaked)
        
        self.updateRewards(sp.sender)

        senderBalance = self.data.balances[sp.sender]

        sp.verify(senderBalance.staked >= amount, Error.UnstakeMoreThanStake)

        self.data.details.totalStaked = sp.as_nat(self.data.details.totalStaked - amount)
        senderBalance.staked = sp.as_nat(senderBalance.staked - amount)

        self.TransferTokens(sp.self_address, sp.sender, 
                            amount, 
                            self.data.tokens.stake.address, self.data.tokens.stake._id)

        


    @sp.entry_point
    def claim(self):
        self.checkPaused()
        sp.verify(self.data.balances.contains(sp.sender), Error.NotStaked)
        self.updateRewards(sp.sender)
        
        rewardsToSend = self.data.balances[sp.sender].rewards
        sp.verify(rewardsToSend > 0, Error.ZeroAmount)
        
        self.TransferTokens(sp.self_address, sp.sender, rewardsToSend,
                            self.data.tokens.reward.address, self.data.tokens.reward._id)
        self.data.balances[sp.sender].rewards = 0

    @sp.entry_point
    def updateRewardsFor(self, address):
        self.checkAdmin()
        self.updateRewards(address)

    @sp.sub_entry_point
    def updateRewards(self, address):
        lastUpdate = sp.local("lastUpd", sp.level)
        sp.if lastUpdate.value > self.data.details.finishLevel:
            lastUpdate.value = self.data.details.finishLevel

        rewardPerToken = sp.local("rpt", sp.nat(0))
        sp.if (self.data.details.totalStaked > 0) & (sp.level > self.data.details.startLevel):
            
            sp.if self.data.details.lastUpdated < self.data.details.startLevel:
                self.data.details.lastUpdated = self.data.details.startLevel

            rewardPerToken.value = (sp.as_nat(lastUpdate.value - self.data.details.lastUpdated) * self.data.details.rewardPerBlock * self.data.tokens.reward.decimals)
            rewardPerToken.value = rewardPerToken.value / self.data.details.totalStaked
            self.data.details.rewardPerTokenStored += rewardPerToken.value

        self.data.details.lastUpdated = lastUpdate.value
        
        sp.if address != sp.self_address:
            self.data.balances[address].rewards += self.data.balances[address].staked * (sp.as_nat(self.data.details.rewardPerTokenStored  - self.data.balances[address].userRewardPerTokenPaid)) / self.data.tokens.reward.decimals
            self.data.balances[address].userRewardPerTokenPaid = self.data.details.rewardPerTokenStored

    @sp.sub_entry_point
    def updateRewardPerBlock(self):
        self.data.details.rewardPerBlock = (self.data.details.tokensToReward / sp.as_nat(self.data.details.finishLevel - sp.level))

    """
    UTILITY FUNCTIONS
    """

    def TransferTokens(self, sender, reciever, amount, token, _id):
        arg = [
            sp.record(
                from_ = sender,
                txs = [
                    sp.record(
                        to_      = reciever,
                        token_id = _id,
                        amount   = amount 
                    )
                ]
            )
        ]

        transferHandle = sp.contract(
            sp.TList(sp.TRecord(from_ = sp.TAddress, txs = sp.TList(sp.TRecord(amount = sp.TNat, to_ = sp.TAddress, token_id = sp.TNat).layout(("to_", ("token_id", "amount")))))), 
            token,
            entry_point='transfer').open_some()

        sp.transfer(arg, sp.mutez(0), transferHandle)
    
    def checkPaused(self):
        sp.verify(~self.data.paused, Error.Paused)

    def checkAdmin(self):
        sp.verify(sp.sender == self.data.admin, Error.NotAdmin)

    def checkFarmEnded(self):
        sp.verify(sp.level > self.data.details.finishLevel)


@sp.add_test(name="Staking")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Staking contract PoC")

    admin = sp.address("tz1-admin")
    a1 = sp.address("tz1-staker-1")
    a2 = sp.address("tz1-staker-2")

    token = TestToken(FA2.FA2_config(single_asset=True), admin = admin, 
        metadata = sp.big_map(
            {
            "": sp.utils.bytes_of_string("tezos-storage:content"),
            "content": sp.utils.bytes_of_string("""{"name" : "TestToken"}""")
                
            }
        )
    )

    tokenDecimals = 10 ** 9
    tokenId = 0

    scenario += token
    
    token.mint(
        address = admin,
        amount = 100000 * tokenDecimals,
        metadata = TestToken.make_metadata(
            decimals = 9,
            name = "TestToken",
            symbol = "TST"
        ),
        token_id = tokenId
    ).run(sender = admin)

    

    scenario += token.transfer([
        token.batch_transfer.item(from_ = admin,
            txs = [
                    sp.record(to_ = a1,
                              amount = 1000 * tokenDecimals,
                              token_id = 0),
                    sp.record(to_ = a2,
                              amount = 1000 * tokenDecimals,
                              token_id = 0)
                                    

            ]
        )
    ]).run(sender = admin)

    
    staking = IDZStaking(admin, token.address, tokenId, tokenDecimals, token.address, tokenId, tokenDecimals, 1000 * tokenDecimals, 0, 1000)
    scenario += staking

    token.update_operators([
            sp.variant("add_operator",
                token.operator_param.make(
                    owner = admin,
                    operator = staking.address,
                    token_id = tokenId)),
            sp.variant("add_operator",
                token.operator_param.make(
                    owner = a1,
                    operator = staking.address,
                    token_id = tokenId)),
            sp.variant("add_operator",
                token.operator_param.make(
                    owner = a2,
                    operator = staking.address,
                    token_id = tokenId))
    ]).run(sender = admin)

    staking.startPool().run(sender = admin)

    staking.stake(100 * tokenDecimals).run(sender = a1, level = 0)
    staking.stake(300 * tokenDecimals).run(sender = a2, level = 0)

    staking.claim().run(sender = a1, level = 400)
    staking.claim().run(sender = a2, level = 800)


    staking.refillPool(amount = sp.nat(1000 * tokenDecimals), start = sp.nat(1100), finish = sp.nat(2100)).run(sender = admin, level = 1100)
    staking.updateRewardsFor(a1).run(sender = admin)
    staking.updateRewardsFor(a2).run(sender = admin)



    staking.claim().run(sender = a1, level = 1800)
    staking.claim().run(sender = a1, level = 2400)

    staking.claim().run(sender = a2, level = 2400)
