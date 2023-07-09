#!/usr/bin/env python3
import sys
import os
import tempfile
import shutil
import socket

import yaml
from flask import Flask,abort,request,redirect,flash,url_for,Response
from jinja2 import Environment,FileSystemLoader
app = Flask(__name__)
app.secret_key='pb3wuD31NCwnQ0CQP4rUAZ/x0OU'

if socket.gethostname()=='www-kmadg':
    DATADIR='/var/lib/ssaos_abstracts'
    TEMPLATE_DIR='/usr/local/lib/yadata_editable/template'
    def my_url_for(*args,**kwargs):

        catch=url_for(*args,**kwargs)
        hlist=catch.split('/')
        hlist[0:0]=['ssaos_abstracts']
        return '/'.join(hlist)
else:
    DATADIR='./data'
    TEMPLATE_DIR='./template'
    my_url_for=url_for

env=Environment(loader=FileSystemLoader(TEMPLATE_DIR),
    line_statement_prefix='#',
    extensions=['jinja2.ext.loopcontrols'],
)

@app.route('/abstract/<objid>')
def abstract(objid):
    abstract_filename=f'{DATADIR}/{objid}/abstract.tex'
    try:
        with open(abstract_filename) as f:
            abstract=f.read()
    except FileNotFoundError:
        abort(404)
    return Response(abstract,content_type='text/plain')

@app.route('/thanks/<objid>')
def thanks(objid):

    yaml_fnm=f'{DATADIR}/{objid}/data.yaml'

    abstract_filename=f'{DATADIR}/{objid}/abstract.tex'
    try:
        with open(yaml_fnm) as f:
            obj=yaml.load(f,Loader=yaml.Loader)
    except FileNotFoundError:
        abort(404)
    try:
        st=os.stat(abstract_filename)
        have_abstract=True
        abstract_length=st.st_size
    except FileNotFoundError:
        have_abstract=False
        abstract_length=-1
    t=env.get_template('thanks.html')
    return t.render(obj=obj,have_abstract=have_abstract,abstract_length=abstract_length,
                    correct_url=my_url_for('editable_dict',objid=objid),
                    abstract_url=my_url_for('abstract',objid=objid),
                    )

@app.route('/data/<objid>',methods=["GET","POST"])
def editable_dict(objid):

    error=None
    yaml_fnm=f'{DATADIR}/{objid}/data.yaml'
    abstract_filename=f'{DATADIR}/{objid}/abstract.tex'
    t=env.get_template('form.html')
    try:
        with open(yaml_fnm) as f:
            obj=yaml.load(f,Loader=yaml.Loader)
    except FileNotFoundError:
        abort(404)
    obj['abstract_uploaded']=False
    if request.method=='POST':
        print(request.form,file=sys.stderr)
        for name in request.form:
            if name in obj:
                obj[name]=request.form[name]
        if 'abstract_tex' in request.files:
            file=request.files['abstract_tex']
            if not file.filename=='':
                if not file.filename.lower().endswith('.tex'):
                    error=f'{file.filename} does not appear to be a LaTeX file'
                    return t.render(obj=obj,action=request.url,error=error)
                else:
                    obj['abstract_uploaded']=True
                    file.save(abstract_filename)
        f=tempfile.NamedTemporaryFile(delete=False,mode='w')
        f.write(yaml.dump(obj))
        f.close()
        shutil.move(f.name,yaml_fnm)
        return redirect(my_url_for('thanks',objid=objid))
    return t.render(obj=obj,action=request.url,error=error)
#app.run()

