# cell 66 | agent: analyst | original run: ok | artifacts created: none
script=script.replace('import FixedFormatter','import FuncFormatter').replace("if parent=='P16':\n                            formatter.func", "if parent=='P16' and isinstance(formatter,FuncFormatter):\n                            formatter.func"); rel=test_relabel()
