# cell 23 | agent: data | original run: ok | artifacts created: T32, T33, T34, T35, T36, T37
print(load('T29').status.value_counts().to_dict()); print(load('T30').status.value_counts().to_dict()); print(load('T29').query("status!='ok'").to_string(index=False)); print(load('T31').groupby('kind').sum(numeric_only=True).to_string())
exec(compile(Path('stage1_derive.py').read_text(),'stage1_derive.py','exec')); D,meta,coverage,refworks=derive('T29','T30','T26','T27')
