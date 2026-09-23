import json, math
# Resident 12-month model. All inputs labeled: F=fact(source) G=guess(Hadi/Claude)
A = dict(
  price=595,            # G subscription $/unit/mo
  onboard_fee=1800,     # G Hadi's "value" figure, charged upfront
  hw_cost=1299,         # G Mac mini M6 base $899 retail (F Macworld 25 Aug 2026) + 32GB step-up est.
  install_cost=250,     # G field install + data hookup labor
  sub_cogs=45,          # G RMM tooling, support, warranty reserve per unit/mo
  churn=0.02,           # G monthly
  partner_share=0.20,   # G blended partner share across tiers 15/20/30%, paid on every unit
  free_units=100,       # Hadi 23 Sep 2026: first 100 Mac minis given away (no onboarding fee)
)
def run(name, adds, opex, price=None, paid_share=1.0):   # paid_share: fraction of units via cash rev-share channels (0 for first MSP-only)
  p = price or A['price']; act=0.0; rows=[]; cum=0; shipped=0
  for m in range(1,13):
    a = adds(m); act = act*(1-A['churn']) + a
    mrr = act*p; sub_gp = act*(p-A['sub_cogs'])
    free = max(0, min(a, A['free_units']-shipped)); shipped += a
    onb_gp = a*(-A['hw_cost']-A['install_cost']) + (a-free)*A['onboard_fee']
    partner = paid_share*mrr*A['partner_share']   # G share of units via paying channel partners
    support = (act/100)*7000   # G 1 support FTE per 100 units
    ebitda = sub_gp+onb_gp-partner-opex(m)-support; cum+=ebitda
    rec = sub_gp-partner-opex(m)-support
    rows.append(dict(m=m,adds=round(a),active=round(act),mrr=round(mrr),ebitda=round(ebitda),rec=round(rec),cum=round(cum)))
  rr = rows[-1]['rec']*12
  return dict(name=name,price=p,rows=rows,runrate=round(rr),cum=round(cum),active=rows[-1]['active'],
              min_cum=min(r['cum'] for r in rows))
opex_base=lambda m: 45000+ (m-1)*5000            # $45k -> $100k/mo (team 2 -> 7)
opex_push=lambda m: 55000+ (m-1)*7500            # $55k -> $137k/mo (team 3 -> 10)
S=[]
S.append(run("First MSP only", lambda m: [4,6,8,10,12,12,12,12,12,12,10,10][m-1], opex_base))
S.append(run("Base (4 channels)", lambda m: [4,6,10,16,24,32,40,46,52,56,60,64][m-1], opex_base))
S.append(run("$2M path", lambda m: [4,8,16,28,48,68,88,104,124,136,144,152][m-1], opex_push))
S.append(run("$2M path @ $795", lambda m: [4,8,16,28,48,68,88,104,124,136,144,152][m-1], opex_push, 795))
S.append(run("$2M path @ $495", lambda m: [4,8,16,28,48,68,88,104,124,136,144,152][m-1], opex_push, 495))
# solver: active units needed at M12 for $2M run-rate at given price & opex
def need(p,opex):
  return math.ceil((2_000_000/12 + opex) / ((p-A['sub_cogs']) - p*A['partner_share'] - 7000/100))   # 7000/100 = $70 support per unit
solve={f"${p}":dict(base=need(p,100000),push=need(p,137500)) for p in (495,595,795,995)}
json.dump(dict(assump=A,scen=S,solve=solve),open(__import__('os').path.join(__import__('os').path.dirname(__file__),'model.json'),'w'),indent=1)
for s in S: print(f"{s['name']:20} act M12 {s['active']:4}  MRR ${s['rows'][-1]['mrr']:>8,}  RR EBITDA ${s['runrate']:>10,}  cum12 ${s['cum']:>10,}  trough ${s['min_cum']:>9,}")
print(solve)
for sc in S: print(sc['name'], 'M12 margin', round(sc['rows'][-1]['rec']/max(sc['rows'][-1]['mrr'],1)*100),'%')
