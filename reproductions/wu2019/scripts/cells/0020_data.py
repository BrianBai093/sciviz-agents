# cell 20 | agent: data | original run: ok | artifacts created: none
print(Path('stage1_derive.py').is_file()); print(openalex_usage()); print([(x['created'],x['code'][:35]) for x in [json.loads(l) for l in Path('kernel_log.jsonl').read_text().splitlines()][-5:]])
