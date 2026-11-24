# cell 49 | agent: analyst | original run: failed | artifacts created: none
import json
print({k:json.loads(Path('artifacts/P17/meta.json').read_text())[k] for k in ['parent','version','status','inputs']})
STAGE2_RUN=False
exec(compile(Path('analysis_stage2.py').read_text(),'analysis_stage2.py','exec'))
render_saved_stage2({'fig3-impact-stage2','ext-raw-disruption-stage2'})
