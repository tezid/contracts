const { TezosToolkit } = require("@taquito/taquito");
const { InMemorySigner } = require("@taquito/signer");
const { get } = require("axios");

const config = {
  farm_address: "<INSERT_CONTRACT_ADDRESS>",
  rpc: "https://granadanet.smartpy.io/",
  PK: "<INSET_PK>",
  refillDetails: {
    amount: 200000000000,
    start: 676200,
    finish: 678200,
  },
};

const Tezos = new TezosToolkit(config.rpc);
const PK = config.PK;

async function main() {
  Tezos.setProvider({
    signer: await InMemorySigner.fromSecretKey(PK),
  });

  const farm = await Tezos.wallet.at(config.farm_address);

  let batch = Tezos.wallet.batch();

  const stakedAddresses = await fetchStakedAddresses();
  for (let a of stakedAddresses) {
    batch = batch.withContractCall(farm.methods.updateRewardsFor(a));
  }

  try {
    console.log("Sending refill")
    const refillOp = await farm.methods
      .refillPool(
        config.refillDetails.amount,
        config.refillDetails.finish,
        config.refillDetails.start
      )
      .send();
    await refillOp.confirmation(3);

    console.log("Sending updates");
    const op = await batch.send();
    console.log(op);
  } catch (err) {
    console.log(err);
  }
}

async function fetchStakedAddresses() {
  const resp = await get(
    `https://api.granadanet.tzkt.io/v1/contracts/${config.farm_address}/bigmaps/balances/keys?select=key`
  );
  return resp.data;
}

main();
