# cell 11 | agent: data | original run: ok | artifacts created: none
import signal
for line in subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines():
 spl=line.strip().split(maxsplit=1)
 if len(spl)==2 and any(spl[1].endswith(os.path.join(os.getcwd(),f'jobs/{i}/run.py')) for i in ('job1','job2')):
  os.kill(int(spl[0]),signal.SIGINT);print('interrupted',spl[0])
print(openalex_usage())
