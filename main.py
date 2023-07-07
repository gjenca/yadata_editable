#!/usr/bin/env python3
import sys
from flask import Flask,abort,request,redirect
from jinja2 import Environment,FileSystemLoader
import yaml
app = Flask(__name__)


DATADIR='./data'
env=Environment(loader=FileSystemLoader('./template'),
    line_statement_prefix='#',
    extensions=['jinja2.ext.loopcontrols'],
)

@app.route('/thanks')
def thanks():
        t=env.get_template('thanks.html')
        return t.render()

@app.route('/data/<objid>',methods=["GET","POST"])
def editable_dict(objid):

    yaml_fnm=f'{DATADIR}/{objid}/data.yaml'
    abstract_filename=f'{DATADIR}/{objid}/abstract.pdf'
    try:
        with open(yaml_fnm) as f:
            obj=yaml.load(f,Loader=yaml.Loader)
    except FileNotFoundError:
        abort(404)
    if request.method=='GET':
        t=env.get_template('form.html')
        return t.render(obj=obj,action=request.url)
    else:
        if request.method=='POST':
            print(request.form,file=sys.stderr)
            for name in request.form:
                if name in obj:
                    obj[name]=request.form[name]
            with open(yaml_fnm,mode='w') as f:
                f.write(yaml.dump(obj))
            if 'abstract' in request.files:
                file=request.files['abstract']
                if not file.filename=='':
                    file.save(abstract_filename)
            return redirect('/thanks')


app.run()

