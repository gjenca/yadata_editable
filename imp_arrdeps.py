#!/usr/bin/env python3
from yadata.utils import sane_yaml
import os

f=open('arrdeps.yaml')
for arrdep in sane_yaml.load_all(f):
    dirname=f'data2/{arrdep["code"]}'
    os.mkdir(dirname)
    dump=sane_yaml.dump(arrdep)
    fw=open(f'{dirname}/data.yaml','w')
    fw.write(dump)
    fw.close()

