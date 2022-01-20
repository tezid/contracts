import smartpy as sp

FA2 = sp.io.import_script_from_url("https://smartpy.io/dev/templates/FA2.py")
TTx = sp.TRecord(amount = sp.TNat, to_ = sp.TAddress, token_id = sp.TNat).layout(("to_", ("token_id", "amount")))
TTxs = sp.TList(TTx)
TTransferTokensParam = sp.TList(sp.TRecord(from_ = sp.TAddress, txs = TTxs)) 

def string_of_nat(params):
  c   = sp.map({x : str(x) for x in range(0, 10)})
  x   = sp.local('x', params)
  res = sp.local('res', [])
  sp.if x.value == 0:
      res.value.push('0')
  sp.while 0 < x.value:
      res.value.push(c[x.value % 10])
      x.value //= 10
  return sp.concat(res.value)

def bytes_of_string(s):
    b = sp.pack(s)
    return sp.slice(b, 6, sp.as_nat(sp.len(b) - 6)).open_some("Could not get bytes of string")

class FA2Token(FA2.FA2):
  pass

TOKEN_config = FA2.FA2_config(
  debug_mode                         = False,
  single_asset                       = True,
  non_fungible                       = False,
  add_mutez_transfer                 = False,
  readable                           = True,
  force_layouts                      = True,
  support_operator                   = True,
  assume_consecutive_token_ids       = False,
  store_total_supply                 = True,
  lazy_entry_points                  = False,
  allow_self_transfer                = False,
  use_token_metadata_offchain_view   = False
)
