# cell 75 | agent: analyst | original run: ok | artifacts created: none
prior=load('J16'); print(prior.keys()); print({k:v for k,v in prior.items() if k not in ['script','figures']});
for r in prior['figures']: print({k:v for k,v in r.items() if k not in ['caption','parity']})
