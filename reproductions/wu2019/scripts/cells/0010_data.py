# cell 10 | agent: data | original run: ok | artifacts created: none
import subprocess
print(os.listdir('jobs')); print([(x, os.listdir('jobs/'+x)) for x in os.listdir('jobs') if os.path.isdir('jobs/'+x)]); print('\n'.join(x for x in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines() if '/job' in x or 'stage1_grouped' in x)[:3500])
