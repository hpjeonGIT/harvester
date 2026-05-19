import json
import sys
from pathlib import Path
import random
N = 100
 
def sow_seed():
    template = { "walltime":0.0, "value":0.0, "timestep":0}
    for i in range(N):
        new_folder = 't' + f'{i:03d}'
        Path(new_folder).mkdir(exist_ok = True)
        k = random.randint(0,10)
        if k > 1 :
            template["walltime"] = random.random()*1000.
            template["value"] = random.random()*10000.
            template["timestep"] = random.randint(10,1000)
            with open(new_folder+"/summary.json",'w') as f:
                json.dump(template,f,indent=4)
        elif k == 1:
            # empty file
            with open(new_folder+"/summary.json",'w') as f:
                json.dump('',f,indent=4)
        else:
            pass # no file
 
if __name__ == "__main__":
    if sys.version_info < (3,10):
        print("Requires Python 3.10 or newer. We exit now")
        sys.exit()
    sow_seed()
