# cell 57 | agent: analyst | original run: ok | artifacts created: none
print(fc[len(fc)//2:]); print([(i,Path(f'artifacts/{i}/figure.png').is_file()) for i in ['P15','P16','P17','P18','P19']]); import importlib.util;print([(x,importlib.util.find_spec(x) is not None) for x in ('fitz','pypdf','PIL')])
