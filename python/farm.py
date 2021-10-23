import smartpy as sp

FA2 = sp.io.import_script_from_url("https://smartpy.io/dev/templates/FA2.py")


class TestToken(FA2.FA2):
    pass


DECIMALS = 10 ** 9


class Error:
    def make(s):
        return "FARM_" + s

    NotAdmin = make("NOT_ADMIN")
    NotStaked = make("NOT_STAKED")
    WrongStatus = make("WRONG_STATUS")

    ZeroAmount = make("ZERO_AMOUNT")
    UnstakeMoreThanStake = make("UNSTAKE_AMOUNT_GREATER_THAN_STAKE")

    WrongIndex = make("WRONG_INDEX_FOR_MAP")
    Paused = make("CONTRACT_PAUSED")


_balanceMap = sp.big_map(
    tkey=sp.TAddress,
    tvalue=sp.TRecord(balance=sp.TNat, rewards=sp.TNat, userRewardPerTokenPaid=sp.TNat),
)


def buildFarmDetails(amount, rpb):
    return sp.record(
        rewardPerBlock=rpb,
        rewardPerTokenStored=sp.nat(0),
        lastUpdated=sp.nat(0),
        totalStaked=sp.nat(0),
        rewardsDistributed=sp.nat(0),
        rewards=amount,
    )


def buildTokenDetails(_stakeToken, _stakeId, _stakeDecimals, _rewardToken, _rewardId, _rewardDecimals):
    return sp.record(
        stake=sp.record(address=_stakeToken, _id=_stakeId, decimals = _stakeDecimals),
        reward=sp.record(address=_rewardToken, _id=_rewardId, decimals = _rewardDecimals),
    )

def buildTokenDetailsV1(_stakeToken, _stakeId, _rewardToken, _rewardId):
    return sp.record(
        stake=sp.record(address=_stakeToken, _id=_stakeId),
        reward=sp.record(address=_rewardToken, _id=_rewardId),
    )


class Staking(sp.Contract):
    def __init__(
        self,
        _admin,
        _stakeToken,
        _stakeId,
        _stakeDecimals,
        _rewardToken,
        _rewardId,
        _rewardDecimals,
        _rewardAmount,
        _rewardPerBlock,
    ):
        self.init(
            admin=_admin,
            balances=_balanceMap,
            details=buildFarmDetails(_rewardAmount, _rewardPerBlock),
            tokens=buildTokenDetails(_stakeToken, _stakeId, _stakeDecimals, _rewardToken, _rewardId, _rewardDecimals),
            paused=False,
            started=False
        )

        

    @sp.entry_point
    def startPool(self):
        self.checkPaused()
        self.checkAdmin()

        sp.verify(self.data.details.rewards > 0, Error.ZeroAmount) 
        rewardsToTransfer = self.data.details.rewards * self.data.tokens.reward.decimals
        
        self.TransferTokens(sp.sender, sp.self_address,
                            self.data.details.rewards,
                            self.data.tokens.stake.address, 
                            self.data.tokens.stake._id)
    
        
        self.updateRewards(sp.self_address)

        self.data.started = True

    @sp.entry_point
    def refillFarm(self, _rewards, _rewardPerBlock):
        sp.verify(self.data.started == True)

        self.checkAdmin()

        farmDetails = self.data.details
        farmDetails.rewards += _rewards
        farmDetails.rewardPerBlock = _rewardPerBlock

        self.TransferTokens(sp.sender, sp.self_address, _rewards, 
                            self.data.tokens.reward.address, self.data.tokens.reward._id)


        self.updateRewards(sp.self_address)


    @sp.entry_point
    def stake(self, amount):
        sp.set_type(amount, sp.TNat)
        sp.verify(self.data.started == True)
        self.checkPaused()

        sp.verify(amount > 0, Error.ZeroAmount)

        sp.if ~self.data.balances.contains(sp.sender):
            self.data.balances[sp.sender] = sp.record(
                balance = 0,
                rewards = 0,
                userRewardPerTokenPaid = 0
            )
        
        self.updateRewards(sp.sender)
        
        self.TransferTokens(sp.sender, sp.self_address, amount, 
                            self.data.tokens.stake.address, self.data.tokens.stake._id)

        self.data.details.totalStaked += amount
        self.data.balances[sp.sender].balance += amount

    @sp.entry_point
    def unstake(self, amount):
        sp.verify(self.data.started == True)
        sp.set_type(amount, sp.TNat)
        self.checkPaused()
        sp.verify(self.data.balances.contains(sp.sender), Error.NotStaked)
        
        senderBalance = self.data.balances[sp.sender]
        sp.verify(senderBalance.balance >= amount)

        self.updateRewards(sp.sender)

        self.data.details.totalStaked = sp.as_nat(self.data.details.totalStaked - amount)
        senderBalance.balance = sp.as_nat(senderBalance.balance - amount)

        self.TransferTokens(sp.self_address, sp.sender, amount,
                            self.data.tokens.stake.address, self.data.tokens.stake._id)


    @sp.entry_point
    def claim(self):
        sp.verify(self.data.started == True)
        self.checkPaused()
        sp.verify(self.data.balances.contains(sp.sender), Error.NotStaked)
        self.updateRewards(sp.sender)

        senderBalance = self.data.balances[sp.sender]
        sp.verify(senderBalance.rewards > 0, Error.ZeroAmount)

        self.data.details.rewardsDistributed += senderBalance.rewards
        self.TransferTokens(sp.self_address, sp.sender, senderBalance.rewards,
                            self.data.tokens.reward.address, self.data.tokens.reward._id)

        senderBalance.rewards = 0


    @sp.entry_point
    def togglePause(self):
        self.checkAdmin()
        self.data.paused = ~self.data.paused

    @sp.sub_entry_point
    def updateRewards(self, address):
      last = sp.level

      rewardPerToken = sp.local("rpt", sp.nat(0))

      sp.if self.data.details.rewards == 0:
        self.data.details.rewardPerBlock = 0

      sp.if self.data.details.totalStaked > 0:
        rewardPerToken.value = (sp.as_nat(last - self.data.details.lastUpdated) * self.data.details.rewardPerBlock * DECIMALS)
        rewardPerToken.value = rewardPerToken.value / self.data.details.totalStaked
        self.data.details.rewardPerTokenStored += rewardPerToken.value
      
      self.data.details.lastUpdated = last

      sp.if address != sp.self_address:
        rewardToUser = self.data.balances[address].balance * (sp.as_nat(self.data.details.rewardPerTokenStored  - self.data.balances[address].userRewardPerTokenPaid)) / DECIMALS 
        self.data.balances[address].rewards += rewardToUser
        self.data.balances[address].userRewardPerTokenPaid = self.data.details.rewardPerTokenStored

        self.data.details.rewards = sp.as_nat(self.data.details.rewards - rewardToUser)

    @sp.sub_entry_point
    def checkAdmin(self):
        sp.verify(sp.sender == self.data.admin, Error.NotAdmin)

    @sp.sub_entry_point
    def checkPaused(self):
        sp.verify(~self.data.paused, Error.Paused)


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


@sp.add_test(name="Staking")
def test():
    

    scenario = sp.test_scenario()
    scenario.h1("Staking contract PoC")

    admin = sp.address("tz1-admin")
    u1 = sp.address("tz1-user-1")
    u2 = sp.address("tz1-user-2")

    testToken = TestToken(FA2.FA2_config(single_asset=True), admin = admin, 
        metadata = sp.big_map(
            {
            "": sp.utils.bytes_of_string("tezos-storage:content"),
            "content": sp.utils.bytes_of_string("""{"name" : "TestToken"}""")
                
            }
        )
    )

    scenario += testToken

    tokenId = 0

    testToken.mint(
        address = admin,
        amount = 120_000 * DECIMALS,
        metadata = TestToken.make_metadata(
            decimals = 9,
            name = "TestToken",
            symbol = "TST"
        ),
        token_id = tokenId
    ).run(sender = admin)

    testToken.transfer([
        testToken.batch_transfer.item(from_ = admin,
            txs = [
                    sp.record(to_ = u1,
                                      amount = 10_000 * DECIMALS,
                                      token_id = 0),
                    sp.record(to_ = u2,
                                      amount = 10_000 * DECIMALS,
                                      token_id = 0)
                                    

            ]
        )
    ]).run(sender = admin)

    """
    _admin,
    _stakeToken,
    _stakeId,
    _stakeDecimals,
    _rewardToken,
    _rewardId,
    _rewardDecimals,
    _rewardAmount,
    _rewardPerBlock,
    """
    staking = Staking(admin,
        testToken.address,
        sp.nat(0),
        sp.nat(10 ** 9),
        testToken.address,
        sp.nat(0),
        sp.nat(10 ** 9),
        sp.nat(100000 * DECIMALS),
        sp.nat(100))

    scenario += staking

    testToken.update_operators([
            sp.variant("add_operator",
                testToken.operator_param.make(
                    owner = admin,
                    operator = staking.address,
                    token_id = 0)),

            sp.variant("add_operator",
                testToken.operator_param.make(
                    owner = u1,
                    operator = staking.address,
                    token_id = 0)),

            sp.variant("add_operator",
                testToken.operator_param.make(
                    owner = u2,
                    operator = staking.address,
                    token_id = 0))
    ]).run(sender = admin)

    staking.startPool().run(sender = admin)

