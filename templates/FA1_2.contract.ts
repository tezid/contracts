enum ErrorCodes {
    NotAdmin = 'FA1.2_NotAdmin',
    InsufficientBalance = 'FA1.2_InsufficientBalance',
    UnsafeAllowanceChange = 'FA1.2_UnsafeAllowanceChange',
    Paused = 'FA1.2_Paused',
    NotAllowed = 'FA1.2_NotAllowed',
}

type TBalance = TRecord<
    {
        approvals: TMap<TAddress, TNat>;
        balance: TNat;
    },
    Layout.right_comb
>;

type TToken_Metadata = TRecord<
    {
        token_id: TNat;
        token_info: TMap<TString, TBytes>;
    },
    Layout.right_comb
>;

interface TStorage {
    config: {
        admin: TAddress;
        paused: TBool;
    };
    balances: TBig_map<TAddress, TBalance>;
    totalSupply: TNat;
    metadata: TBig_map<TString, TBytes>;
    token_metadata: TBig_map<TNat, TToken_Metadata>;
}

type ApproveParams = TRecord<
    {
        spender: TAddress;
        value: TNat;
    },
    ['spender', 'value']
>;

type BurnParams = TRecord<
    {
        address: TAddress;
        value: TNat;
    },
    ['address', 'value']
>;

type MintParams = TRecord<
    {
        address: TAddress;
        value: TNat;
    },
    ['address', 'value']
>;

type TransferParams = TRecord<
    {
        from: TAddress;
        to: TAddress;
        value: TNat;
    },
    ['from', ['to', 'value']]
>;

/**
 * @description Class that defines the default storage
 */
class Storage {
    // Declare the initial storage
    storage: TStorage = {
        config: {
            admin: 'tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU',
            paused: false,
        },
        balances: [],
        totalSupply: 0,
        metadata: [],
        token_metadata: [],
    };
}

/**
 * @description Class that contains all off-chain views
 */
class OffChainViews extends Storage {
    @OffChainView({
        pure: true,
        description: 'Return the token-metadata URI for the given token.',
    })
    token_metadata = (tokenId: TNat): TToken_Metadata => {
        return this.storage.token_metadata.get(tokenId);
    };
}

/**
 * @description Class that contains the contract metadata builder
 */
class Metadata extends OffChainViews {
    @MetadataBuilder
    metadata = {
        name: 'SmartPy FA1.2 Token Template',
        description: 'Example Template for an FA1.2 Contract from SmartPy',
        authors: ['SmartPy Dev Team <email@domain.com>'],
        homepage: 'https://smartpy.io',
        interfaces: ['TZIP-007-2021-04-17', 'TZIP-016-2021-04-17'],
        views: [this.token_metadata],
    };
}

/**
 * @description Class with inline functions, which are common to multiple entry_points
 */
class Helpers extends Metadata {
    /**
     * @description Fail if the contract is paused
     */
    @Inline
    failIfPaused() {
        Sp.verify(!this.storage.config.paused, ErrorCodes.Paused);
    }

    /**
     * @description Fail if the contract is paused
     */
    @Inline
    failIfSenderNotAdmin() {
        Sp.verify(Sp.sender === this.storage.config.admin, ErrorCodes.NotAdmin);
    }

    /**
     * @description Checks if address exists in balances
     */
    @Inline
    addressExists = (address: TAddress) => this.storage.balances.hasKey(address);
}

@Contract
export class FA1_2 extends Helpers {
    @EntryPoint
    approve(params: ApproveParams): void {
        // The contract must not be paused
        this.failIfPaused();
        if (!this.addressExists(Sp.sender)) {
            const value: TBalance = { approvals: [], balance: 0 };
            this.storage.balances.set(Sp.sender, value);
        }
        Sp.verify(
            this.storage.balances.get(Sp.sender).approvals.get(params.spender, 0) == 0 || params.value == 0,
            ErrorCodes.UnsafeAllowanceChange,
        );

        this.storage.balances.get(Sp.sender).approvals.set(params.spender, params.value);
    }

    @EntryPoint
    burn(params: BurnParams): void {
        // Sender must be the admin
        this.failIfSenderNotAdmin();
        Sp.verify(this.storage.balances.get(params.address).balance >= params.value, ErrorCodes.InsufficientBalance);
        this.storage.balances.get(params.address).balance = (this.storage.balances.get(params.address).balance -
            params.value) as TNat;
        this.storage.totalSupply = (this.storage.totalSupply - params.value) as TNat;
    }

    @EntryPoint
    mint(params: MintParams): void {
        // Sender must be the admin
        this.failIfSenderNotAdmin();
        if (!this.addressExists(params.address)) {
            const value: TBalance = { approvals: [], balance: 0 };
            this.storage.balances.set(params.address, value);
        }
        this.storage.balances.get(params.address).balance += params.value;
        this.storage.totalSupply += params.value;
    }

    @EntryPoint
    setAdministrator(newAdmin: TAddress): void {
        // Sender must be the admin
        this.failIfSenderNotAdmin();
        this.storage.config.admin = newAdmin;
    }

    @EntryPoint
    setPause(paused: TBool): void {
        // Sender must be the admin
        this.failIfSenderNotAdmin();
        this.storage.config.paused = paused;
    }

    @EntryPoint
    transfer(params: TransferParams): void {
        // The contract must not be paused
        this.failIfPaused();

        // Conditions:
        // 1 - When called with "from" account equal to the transaction sender, we assume that the user transfers their own money and this does not require approval.
        // 2 - Otherwise, the transaction sender must be previously authorized to transfer at least the requested number of tokens from the "from" account using the approve entrypoint.
        Sp.verify(
            params.from === Sp.sender ||
                this.storage.balances.get(params.from).approvals.get(Sp.sender) >= params.value,
            ErrorCodes.NotAllowed,
        );

        // Add balance entry for (from) address if it doesn't exist.
        if (!this.addressExists(params.from)) {
            const value: TBalance = { approvals: [], balance: 0 };
            this.storage.balances.set(params.from, value);
        }

        // Add balance entry for (to) address if it doesn't exist.
        if (!this.addressExists(params.to)) {
            const value: TBalance = { approvals: [], balance: 0 };
            this.storage.balances.set(params.to, value);
        }

        Sp.verify(this.storage.balances.get(params.from).balance >= params.value, ErrorCodes.InsufficientBalance);

        this.storage.balances.get(params.from).balance = (this.storage.balances.get(params.from).balance -
            params.value) as TNat;
        this.storage.balances.get(params.to).balance += params.value;

        // Transfering own balance doesn't require approval (sender is the owner)
        if (params.from !== Sp.sender) {
            const approval = (this.storage.balances.get(params.from).approvals.get(Sp.sender) - params.value) as TNat;
            this.storage.balances.get(params.from).approvals.set(Sp.sender, approval);
        }
    }

    @EntryPoint
    updateMetadata(metadata: TBig_map<TString, TBytes>): void {
        // Sender must be the admin
        this.failIfSenderNotAdmin();
        this.storage.metadata = metadata;
    }

    @EntryPoint
    getAdministrator(request: TTuple<[TUnit, TContract<TAddress>]>): void {
        Sp.transfer(this.storage.config.admin, 0, request.snd());
    }

    @EntryPoint
    getAllowance(request: TTuple<[{ owner: TAddress; spender: TAddress }, TContract<TNat>]>): void {
        let allowance = 0;
        if (this.addressExists(request.fst().owner)) {
            allowance = this.storage.balances.get(request.fst().owner).approvals.get(request.fst().spender, 0);
        }
        Sp.transfer(allowance, 0, request.snd());
    }

    @EntryPoint
    getBalance(request: TTuple<[TAddress, TContract<TNat>]>): void {
        let balance = 0;
        if (this.addressExists(request.fst())) {
            balance = this.storage.balances.get(request.fst()).balance;
        }
        Sp.transfer(balance, 0, request.snd());
    }

    @EntryPoint
    getTotalSupply(request: TTuple<[TUnit, TContract<TNat>]>): void {
        Sp.transfer(this.storage.totalSupply, 0, request.snd());
    }
}

Dev.test({ name: 'FA1_2' }, () => {
    const c1 = Scenario.originate(new FA1_2());
    Scenario.transfer(c1.mint({ address: 'KT18amZmM5W7qDWVt2pH6uj7sCEd3kbzLrHT', value: 1000000 }), {
        sender: 'tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU',
    });
});

Dev.compileContract('version_1', new FA1_2());
