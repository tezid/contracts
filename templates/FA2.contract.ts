/**
 * Type Definitions
 */

type TokenMetadata = TRecord<
    {
        token_id: TNat;
        token_info: TMap<TString, TBytes>;
    },
    Layout.right_comb
>;

// Declare the storage type definition
interface FA2Storage {
    config: {
        admin: TAddress;
        paused: TBool;
    };
    assets: {
        ledger: TBig_map<TTuple<[TAddress, TNat]>, { balance: TNat }>;
        operators: TBig_map<{ operator: TAddress; owner: TAddress; token_id: TNat }, TUnit>;
        token_metadata: TBig_map<TNat, TokenMetadata>;
        token_total_supply: TBig_map<TNat, TNat>;
    };
    metadata: TBig_map<TString, TBytes>;
}

// transfer entrypoint
type TransferParams = TList<
    TRecord<
        {
            from_: TAddress;
            txs: TList<
                TRecord<
                    {
                        to_: TAddress;
                        token_id: TNat;
                        amount: TNat;
                    },
                    ['to_', ['token_id', 'amount']]
                >
            >;
        },
        ['from_', 'txs']
    >
>;

// update_operators entrypoint
type OperatorParam = TRecord<
    {
        owner: TAddress;
        operator: TAddress;
        token_id: TNat;
    },
    ['owner', ['operator', 'token_id']]
>;
type UpdateOperatorsParams = TList<
    TVariant<
        | {
              kind: 'add_operator';
              value: OperatorParam;
          }
        | {
              kind: 'remove_operator';
              value: OperatorParam;
          },
        ['add_operator', 'remove_operator']
    >
>;

// balance_of entrypoint
type BalanceOfRequest = TRecord<
    {
        owner: TAddress;
        token_id: TNat;
    },
    ['owner', 'token_id']
>;
type BalanceOfResponse = TRecord<
    {
        request: BalanceOfRequest;
        balance: TNat;
    },
    ['request', 'balance']
>;
type BalanceOfParams = TRecord<
    {
        callback: TContract<TList<BalanceOfResponse>>;
        requests: TList<BalanceOfRequest>;
    },
    ['requests', 'callback']
>;

// Off-Chain `get_balance` parameter type
type OffChain_GetBalanceRequest = TRecord<
    {
        owner: TAddress;
        token_id: TNat;
    },
    ['owner', 'token_id']
>;

enum ErrorCodes {
    FA2_TOKEN_UNDEFINED,
    FA2_NOT_ADMIN,
    FA2_PAUSED,
    FA2_NOT_OPERATOR,
    FA2_NOT_ADMIN_OR_OWNER,
    FA2_INSUFFICIENT_BALANCE,
}

// Declare the default initial storage
const default_initial_storage: FA2Storage = {
    config: {
        admin: 'tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU',
        paused: false,
    },
    assets: {
        ledger: [],
        operators: [],
        token_metadata: [],
        token_total_supply: [],
    },
    metadata: [],
};

/**
 * @description Class that defines the default storage
 */
class Storage {
    // The constructor allows the user to override the initial storage
    constructor(public storage: FA2Storage = default_initial_storage) {}
}

/**
 * @description Class that contains all off-chain views
 */
class OffChainViews extends Storage {
    @OffChainView({
        pure: true,
        description: 'This is the `get_balance` view defined in TZIP-12.',
    })
    get_balance = (request: OffChain_GetBalanceRequest): TNat => {
        const user: TTuple<[TAddress, TNat]> = [request.owner, request.token_id];
        Sp.verify(this.storage.assets.token_metadata.hasKey(request.token_id), ErrorCodes.FA2_TOKEN_UNDEFINED);
        return this.storage.assets.ledger.get(user).balance;
    };

    @OffChainView({
        pure: true,
        description: 'Return the token-metadata URI for the given token.',
    })
    token_metadata = (tokenId: TNat): TokenMetadata => {
        return this.storage.assets.token_metadata.get(tokenId);
    };

    @OffChainView({
        pure: true,
        description: 'Ask whether a token ID is exists.',
    })
    does_token_exist = (tokenId: TNat): TBool => {
        return this.storage.assets.token_metadata.hasKey(tokenId);
    };

    @OffChainView({
        pure: true,
        description: 'Get the total supply of a specific token.',
    })
    total_supply = (tokenId: TNat): TNat => {
        return this.storage.assets.token_total_supply.get(tokenId);
    };

    @OffChainView({
        pure: true,
        description: 'Verify if a operator is allowed to transfer tokens owned by other address.',
    })
    is_operator = (operator: OperatorParam): TBool => {
        return this.storage.assets.operators.hasKey(operator);
    };
}

/**
 * @description Class that contains the contract metadata builder
 */
class Metadata extends OffChainViews {
    @MetadataBuilder
    metadata = {
        name: 'A FA2 Template',
        version: 'FA2',
        description:
            'This is a didactic reference implementation of FA2, a.k.a. TZIP-012, using SmartPy.\n\nThis particular contract uses the configuration named: FA2.',
        interfaces: ['TZIP-012', 'TZIP-016'],
        views: [this.get_balance, this.token_metadata, this.does_token_exist, this.total_supply, this.is_operator],
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
        Sp.verify(!this.storage.config.paused, ErrorCodes.FA2_PAUSED);
    }

    /**
     * @description Fail if the contract is paused
     */
    @Inline
    failIfSenderNotAdmin() {
        Sp.verify(Sp.sender === this.storage.config.admin, ErrorCodes.FA2_NOT_ADMIN);
    }

    /**
     * @description Fail if the token is undefined
     */
    @Inline
    failIfTokenIsUndefined(tokenId: TNat) {
        Sp.verify(this.storage.assets.token_metadata.hasKey(tokenId), ErrorCodes.FA2_TOKEN_UNDEFINED);
    }
}

/**
 * @description Contract class that contains the entry_point implementations
 */
@Contract
export class FA2 extends Helpers {
    /**
     * @description transfer token ownership
     * @param {TransferParams} transfer - A list that can contain multiple transactions
     */
    @EntryPoint
    transfer(transfer: TransferParams): void {
        // The contract must not be paused
        this.failIfPaused();
        for (const transaction of transfer) {
            for (const tx of transaction.txs) {
                this.failIfTokenIsUndefined(tx.token_id);
                Sp.verify(
                    transaction.from_ === Sp.sender ||
                        this.storage.assets.operators.hasKey({
                            owner: transaction.from_,
                            operator: Sp.sender,
                            token_id: tx.token_id,
                        }),
                    ErrorCodes.FA2_NOT_OPERATOR,
                );
                if (tx.amount > 0) {
                    const sourceLedger: TTuple<[TAddress, TNat]> = [transaction.from_, tx.token_id];
                    const recipientLedger: TTuple<[TAddress, TNat]> = [tx.to_, tx.token_id];
                    Sp.verify(
                        this.storage.assets.ledger.get(sourceLedger).balance >= tx.amount,
                        ErrorCodes.FA2_INSUFFICIENT_BALANCE,
                    );

                    // Decrement balance from source
                    const newBalance: TNat = this.storage.assets.ledger.get(sourceLedger).balance - tx.amount;
                    this.storage.assets.ledger.get(sourceLedger).balance = newBalance as TNat;

                    if (this.storage.assets.ledger.hasKey(recipientLedger)) {
                        this.storage.assets.ledger.get(recipientLedger).balance += tx.amount;
                    } else {
                        this.storage.assets.ledger.set(recipientLedger, { balance: tx.amount });
                    }
                }
            }
        }
    }

    /**
     * @description mint tokens
     * @param {TNat} tokenId - Token identifier
     * @param {TAddress} address - Recipient address
     * @param {TNat} amount - Amount to mint
     * @param {TMap<TString, TBytes>} metadata - Token metadata
     */
    @EntryPoint
    mint(tokenId: TNat, address: TAddress, amount: TNat, metadata: TMap<TString, TBytes>): void {
        // Sender must be the admin
        this.failIfSenderNotAdmin();
        // We don't check for pauseness because we're the admin.
        const user: TTuple<[TAddress, TNat]> = [address, tokenId];
        if (this.storage.assets.ledger.hasKey(user)) {
            this.storage.assets.ledger.get(user).balance += amount;
        } else {
            this.storage.assets.ledger.set(user, { balance: amount });
        }
        if (!this.storage.assets.token_metadata.hasKey(tokenId)) {
            this.storage.assets.token_metadata.set(tokenId, {
                token_id: tokenId,
                token_info: metadata,
            });
        }

        this.storage.assets.token_total_supply.set(tokenId, this.storage.assets.token_total_supply.get(tokenId, 0) + amount);
    }

    /**
     * @description update operators
     * @param {UpdateOperatorsParams} params
     */
    @EntryPoint
    update_operators(params: UpdateOperatorsParams): void {
        // The contract must not be paused
        this.failIfPaused();
        for (const update of params) {
            switch (update.kind) {
                case 'add_operator': {
                    Sp.verify(update.value.owner === Sp.sender, ErrorCodes.FA2_NOT_ADMIN_OR_OWNER);
                    this.storage.assets.operators.set(update.value, Sp.unit);
                }
                case 'remove_operator': {
                    Sp.verify(update.value.owner === Sp.sender, ErrorCodes.FA2_NOT_ADMIN_OR_OWNER);
                    this.storage.assets.operators.remove(update.value);
                }
            }
        }
    }

    /**
     * @description entrypoint used as view for other contracts to inspect the balance of a given address
     * @param {BalanceOfParams} params Request
     */
    @EntryPoint
    balance_of(params: BalanceOfParams): void {
        // The contract must not be paused
        this.failIfPaused();
        const responses: TList<BalanceOfResponse> = [];
        for (const request of params.requests) {
            this.failIfTokenIsUndefined(request.token_id);
            if (this.storage.assets.ledger.hasKey([request.owner, request.token_id])) {
                responses.push({
                    balance: this.storage.assets.ledger.get([request.owner, request.token_id]).balance,
                    request,
                });
            } else {
                responses.push({
                    balance: 0,
                    request,
                });
            }
        }
        Sp.transfer(responses, 0, params.callback);
    }

    /**
     * @description Pause the contract
     * @param {TBool} paused
     */
    @EntryPoint
    pause(paused: TBool): void {
        this.storage.config.paused = paused;
    }

    /**
     * @description Update the administrator address
     * @param {TAddress} address - New admin address
     */
    @EntryPoint
    set_admin(address: TAddress): void {
        this.storage.config.admin = address;
    }

    /**
     * @description Update contract metadata
     * @param {TAddress} address - New admin address
     */
    @EntryPoint
    update_metadata(metadata: TMap<TString, TBytes>): void {
        for (const entry of metadata.entries()) {
            this.storage.metadata.set(entry.key, entry.value);
        }
    }
}

class SimpleConsumer {
    storage: TNat = 0;

    @EntryPoint
    request_balance(fa2Address: TAddress) {
        const request: BalanceOfParams = {
            callback: Sp.selfEntryPoint('receive_balance'),
            requests: [
                {
                    owner: Sp.selfAddress,
                    token_id: 0,
                },
            ],
        };
        const contact = Sp.contract<BalanceOfParams>(fa2Address, 'balance_of').openSome('Invalid Interface');
        Sp.transfer(request, 0, contact);
    }

    @EntryPoint
    receive_balance(responses: TList<BalanceOfResponse>) {
        for (const response of responses) {
            if (response.request.owner === Sp.selfAddress) {
                this.storage = response.balance;
            }
        }
    }
}

Dev.test({ name: 'FA2' }, () => {
    // List contents
    Scenario.tableOfContents();
    // Test Accounts
    const admin = Scenario.testAccount('Administrator');
    const bob = Scenario.testAccount('Bob');
    // Originare a simple consumer
    const consumer = Scenario.originate(new SimpleConsumer(), { show: false });
    Scenario.h2('Test Accounts');
    Scenario.show([admin, bob]);
    Scenario.h2('Consumer Address');
    Scenario.show([consumer.address]);
    // Originate contract
    const c1 = Scenario.originate(
        new FA2({
            // Initial storage
            config: {
                admin: admin.address,
                paused: false,
            },
            assets: {
                ledger: [],
                operators: [],
                token_metadata: [],
                token_total_supply: [],
            },
            metadata: [['name', '0x54686520546f6b656e205a65726f']],
        }),
    );
    // Pause
    Scenario.h2('Pause and unpause contract');
    Scenario.verify(!c1.storage.config.paused);
    Scenario.transfer(c1.pause(true), { sender: admin });
    Scenario.verify(c1.storage.config.paused);
    // Transfer while paused must fail
    Scenario.transfer(
        c1.transfer([
            {
                from_: consumer.address,
                txs: [
                    {
                        amount: 10,
                        to_: bob.address,
                        token_id: 0,
                    },
                ],
            },
        ]),
        { sender: consumer.address, valid: false },
    );
    Scenario.transfer(c1.pause(false), { sender: admin });
    Scenario.verify(!c1.storage.config.paused);
    // Set admin
    Scenario.h2('Update Admin');
    Scenario.verify(c1.storage.config.admin === admin.address);
    Scenario.transfer(c1.set_admin(consumer.address), { sender: admin });
    Scenario.verify(c1.storage.config.admin === consumer.address);
    Scenario.transfer(c1.set_admin(admin.address), { sender: consumer.address });
    Scenario.verify(c1.storage.config.admin === admin.address);
    // Update_metadata
    Scenario.h2('Update Metatada');
    Scenario.verify(c1.storage.metadata.get('name') === ('0x54686520546f6b656e205a65726f' as TBytes));
    Scenario.transfer(c1.update_metadata([['name', '0x00']]), { sender: admin });
    Scenario.verify(c1.storage.metadata.get('name') === ('0x00' as TBytes));
    Scenario.transfer(c1.update_metadata([['name', '0x54686520546f6b656e205a65726f']]), { sender: admin });
    Scenario.verify(c1.storage.metadata.get('name') === ('0x54686520546f6b656e205a65726f' as TBytes));
    // Mint token
    Scenario.h2('Initial Minting');
    Scenario.transfer(
        c1.mint(
            // Token ID
            0,
            // Destination address
            consumer.address,
            // Amount being minted
            100,
            // Token metadata
            [
                ['name', '0x54686520546f6b656e205a65726f'],
                ['decimals', '0x32'],
                ['symbol', '0x544b30'],
            ],
        ),
        { sender: admin },
    );
    // Transfer some amount from alice to bob
    Scenario.h2('Transfers Alice -> Bob');
    Scenario.transfer(
        c1.transfer([
            {
                from_: consumer.address,
                txs: [
                    {
                        amount: 10,
                        to_: bob.address,
                        token_id: 0,
                    },
                ],
            },
        ]),
        { sender: consumer.address },
    );
    // Verify if the amount was correctly transfered
    Scenario.verify(c1.storage.assets.ledger.get([consumer.address, 0]).balance === 90);
    Scenario.verify(c1.storage.assets.ledger.get([bob.address, 0]).balance === 10);
    // Add alice as bob operator
    Scenario.p('Add alice as bob operator');
    Scenario.transfer(
        c1.update_operators([
            Sp.variant('add_operator', {
                operator: consumer.address,
                owner: bob.address,
                token_id: 0,
            }),
        ]),
        { sender: bob },
    );
    // Transfer multiple amounts back from bob to alice (using alice as operator)
    Scenario.transfer(
        c1.transfer([
            {
                from_: bob.address,
                txs: [
                    {
                        amount: 5,
                        to_: consumer.address,
                        token_id: 0,
                    },
                    {
                        amount: 5,
                        to_: consumer.address,
                        token_id: 0,
                    },
                ],
            },
        ]),
        { sender: consumer.address },
    );
    // Verify if the amount was correctly transfered
    Scenario.verify(c1.storage.assets.ledger.get([consumer.address, 0]).balance === 100);
    Scenario.verify(c1.storage.assets.ledger.get([bob.address, 0]).balance === 0);
    // Call balance of
    Scenario.h2('Request balance of consumer');
    Scenario.verify(consumer.storage === 0);
    Scenario.transfer(consumer.request_balance(c1.address));
    Scenario.verify(consumer.storage === 100);
});

Dev.compileContract(
    'compile_contract',
    new FA2({
        config: {
            admin: '<admin address>',
            paused: false,
        },
        assets: {
            ledger: [],
            operators: [],
            token_metadata: [],
            token_total_supply: [],
        },
        metadata: [
            // You must change the contract metadata
            // The line below is a big_map entry
            // @documentation https://gitlab.com/tezos/tzip/-/blob/master/proposals/tzip-16/tzip-16.md#metadata-uris
            [
                '',
                '0x697066733a2f2f516d616941556a3146464e4759547538724c426a633365654e3963534b7761463845474d424e446d687a504e4664',
            ],
        ],
    }),
);
