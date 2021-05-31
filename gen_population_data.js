import fetch from 'node-fetch'

// v1 -> v2

const CONTRACT = 'KT18ju2Pk6YvNqhD8tsRXGGMRfDVfFkqfhYA'
const TZSTATS_API = 'https://api.tzstats.com'

const gen = async () => {
  const res = await fetch(`${TZSTATS_API}/explorer/contract/${CONTRACT}/storage`)
  const storage = await res.json()
  const identities = Object.keys(storage.value.identities).map(address => {
    const proofs = Object.keys(storage.value.identities[address]).map(proofType => {
      return `  "${proofType}": sp.record(
    register_date = sp.timestamp_from_utc(),
    verified = False,
    meta = {}
  ),`
    })
    return `sp.address("${address}"): {
${proofs.join('\n')}
},`
  })
  console.log(identities.join('\n'))
}

gen()
