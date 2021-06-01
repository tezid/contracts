import fetch from 'node-fetch'

// v1 -> v2

const CONTRACT = 'KT18ju2Pk6YvNqhD8tsRXGGMRfDVfFkqfhYA'
const TZSTATS_API = 'https://api.tzstats.com'

const gen = async () => {
  const res = await fetch(`${TZSTATS_API}/explorer/contract/${CONTRACT}/storage`)
  const storage = await res.json()
  const identities = Object.keys(storage.value.identities).map(address => {
    const proofs = Object.keys(storage.value.identities[address]).map(proofType => {
      const pt = storage.value.identities[address][proofType]
      const verified = pt.verified === 'true' ? 'True' : 'False'
      const rd = new Date(pt.register_date)
      return `            "${proofType}": sp.record(
                register_date = sp.timestamp_from_utc(${rd.getUTCFullYear()},${rd.getUTCMonth()+1},${rd.getUTCDate()},${rd.getUTCHours()},${rd.getUTCMinutes()},${rd.getUTCSeconds()}),
                verified = ${verified},
                meta = {}
            ),`
    })
    if (proofs == '') return null
    return `        sp.address("${address}"): {
${proofs.join('\n')}
        },`
  })
  console.log(identities.filter(i => i != null).join('\n'))
}

gen()
