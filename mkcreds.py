#!/usr/bin/env python3
from getpass import getpass
from hashlib import sha256
import yaml

d={'USERNAME':input('Username:')}
pas=getpass()

h=sha256()
h.update(pas.encode('utf-8'))

d['PASSWORD']=h.hexdigest()
f=open('creds.txt','w')
f.write(yaml.dump(d))
f.close()

