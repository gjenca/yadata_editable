#!/usr/bin/env python3
import sys
import os
import tempfile
import shutil
import socket
import unicodemail
import glob
import io
import requests
import importlib.metadata
from pathlib import Path
from hashlib import sha256

import yaml
import flask
from flask_httpauth import HTTPBasicAuth


flask_version=int(importlib.metadata.version('flask').split('.')[0])


from flask import Flask,abort,request,redirect,flash,url_for,Response,send_file
from jinja2 import Environment,FileSystemLoader

app = Flask(__name__)
app.secret_key='pb3wuD31NCwnQ0CQP4rUAZ/x0OU'

with open('creds.txt') as f:
    creds=yaml.load(f,Loader=yaml.Loader)

USERNAME=creds['USERNAME']
PASSWORD=creds['PASSWORD']

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username,password):

    h=sha256()
    h.update(password.encode('utf-8'))
    return username==USERNAME and h.hexdigest()==PASSWORD

DEPLOYED=(socket.gethostname()=='www-kmadg')

if DEPLOYED:
    DATADIR_TALKS='/var/lib/ssaos_2026_abstracts'
    DATADIR_PARTICIPANTS='/var/lib/ssaos_2026_participants'
    TEMPLATE_DIR='/usr/local/lib/yadata_editable/template'
else:
    DATADIR_TALKS='./data'
    DATADIR_PARTICIPANTS='./data2'
    TEMPLATE_DIR='./template'

env=Environment(loader=FileSystemLoader(TEMPLATE_DIR),
    line_statement_prefix='#',
    extensions=['jinja2.ext.loopcontrols'],
)

def construct_yaml_str(self, node):
    return self.construct_scalar(node)


# Override the default string handling function
# to always return unicode objects
yaml.Loader.add_constructor('tag:yaml.org,2002:str', construct_yaml_str)
yaml.SafeLoader.add_constructor('tag:yaml.org,2002:str', construct_yaml_str)

def unicode_representer(dumper, uni):
    node = yaml.ScalarNode(tag='tag:yaml.org,2002:str', value=uni)
    return node

# This is necessary to dump ASCII string normally
yaml.add_representer(str, unicode_representer)

def yaml_talk_fnm(objid):

    return f'{DATADIR_TALKS}/{objid}/data.yaml'

def yaml_participant_fnm(objid):

    return f'{DATADIR_PARTICIPANTS}/{objid}/data.yaml'

def abstract_dir(objid):
    
    return f'{DATADIR_TALKS}/{objid}'

def abstract_fnm(objid):

    return f'{DATADIR_TALKS}/{objid}/abstract.tex'

def slides_fnm(objid):

    return f'{DATADIR_TALKS}/{objid}/slides.pdf'


@app.route('/test_login')
@auth.login_required
def test_login():

    return 'well done'

@app.route('/abstract/<objid>')
def abstract(objid):
    try:
        with open(abstract_fnm(objid)) as f:
            abstract=f.read()
    except FileNotFoundError:
        abort(404)
    return Response(abstract,content_type='text/plain; charset=utf-8')

@app.route('/slides/<objid>')
def slides(objid):
    try:
        with open(slides_fnm(objid),'rb') as f:
            slides=f.read()
    except FileNotFoundError:
        abort(404)
    try:
        with open(yaml_talk_fnm(objid)) as f:
            obj=yaml.load(f,Loader=yaml.Loader)
    except FileNotFoundError:
        abort(404)
    key_sanitized=obj['_key'].replace(':','_')
    filename_slides=f'{key_sanitized}.pdf'
    if flask_version==1:
        return send_file(io.BytesIO(slides),mimetype='application/pdf',
                         as_attachment=True,
                         attachment_filename=f'{filename_slides}',
                       )
    else:
        return send_file(io.BytesIO(slides),mimetype='application/pdf',
                         as_attachment=True,
                         download_name=f'{filename_slides}',
                       )
    #return Response(slides,content_type='application/pdf',
    #                headers={'content-disposition':f'attachment; filename={filename_slides}'}
    #                )


@app.route('/thanks_slides/<objid>')
def thanks_slides(objid):

    try:
        with open(yaml_talk_fnm(objid)) as f:
            obj=yaml.load(f,Loader=yaml.Loader)
    except FileNotFoundError:
        abort(404)
    try:
        st=os.stat(slides_fnm(objid))
        have_slides=True
        slides_length=st.st_size
    except FileNotFoundError:
        have_slides=False
        slides_length=-1
    t_html=env.get_template('thanks_slides.html')
    t_txt=env.get_template('thanks_slides.txt')
    thanks_html=t_html.render(obj=obj,have_slides=have_slides,slides_length=slides_length,
                    correct_url=url_for('slides_form',objid=objid),
                    slides_url=url_for('slides',objid=objid),
                    program_url=url_for('program'),
                    )
    if DEPLOYED:
        thanks_txt=t_txt.render(obj=obj,have_slides=have_slides,slides_length=slides_length,
                        correct_url=url_for('slides_form',objid=objid),
                        slides_url=url_for('slides',objid=objid),
                        )
        unicodemail.send(
            from_='noreply@math.sk',
            to='gejza.jenca@gmail.com',
            cc='',
            subject=f'SSAOS 2026 -- {obj["participant"]} uploaded the slides',
            message=thanks_txt,
            html=thanks_html
        )
    return thanks_html

@app.route('/thanks_arrival_departure/<objid>')
def thanks_arrival_departure(objid):

    try:
        with open(yaml_participant_fnm(objid)) as f:
            obj=yaml.load(f,Loader=yaml.Loader)
    except FileNotFoundError:
        abort(404)
    t_html=env.get_template('thanks_arrival_departure.html')
    t_txt=env.get_template('thanks_arrival_departure.txt')
    thanks_html=t_html.render(
                        obj=obj,
                        correct_url=url_for('arrival_departure_form',objid=objid)
                        )
    if DEPLOYED:
        thanks_txt=t_txt.render(obj=obj)
        unicodemail.send(
            from_='noreply@math.sk',
            to='ssaos2026@math.sk',
            cc='',
            subject=f'SSAOS 2026 -- {obj["_key"]} submitted arrival/departure info',
            message=thanks_txt,
            html=thanks_html
        )
    return thanks_html

#@app.route('/arrival_departure_form/<objid>',methods=["GET","POST"])
def arrival_departure_form(objid):

    error=None
    t=env.get_template('arrival_departure_form.html')
    try:
        with open(yaml_participant_fnm(objid)) as f:
            obj=yaml.load(f,Loader=yaml.Loader)
    except FileNotFoundError:
        abort(404)
    if request.method=='POST':
        for name in request.form:
            if name in obj:
                obj[name]=request.form[name]
        f=tempfile.NamedTemporaryFile(delete=False,mode='w')
        f.write(yaml.dump(obj,allow_unicode=True))
        f.close()
        shutil.move(f.name,yaml_participant_fnm(objid))
        return redirect(url_for('thanks_arrival_departure',objid=objid))
    return t.render(obj=obj,
                    error=error,
                    )

@app.route('/thanks/<objid>')
def thanks(objid):

    try:
        with open(yaml_talk_fnm(objid)) as f:
            obj=yaml.load(f,Loader=yaml.Loader)
    except FileNotFoundError:
        abort(404)
    try:
        st=os.stat(abstract_fnm(objid))
        have_abstract=True
        abstract_length=st.st_size
    except FileNotFoundError:
        have_abstract=False
        abstract_length=-1
    t_html=env.get_template('thanks_abstract.html')
    t_txt=env.get_template('thanks_abstract.txt')
    thanks_html=t_html.render(obj=obj,have_abstract=have_abstract,abstract_length=abstract_length,
                    correct_url=url_for('abstract_form',objid=objid),
                    abstract_url=url_for('abstract',objid=objid),
                    )
    if DEPLOYED:
        thanks_txt=t_txt.render(obj=obj,have_abstract=have_abstract,abstract_length=abstract_length,
                        correct_url=url_for('abstract_form',objid=objid),
                        abstract_url=url_for('abstract',objid=objid),
                        )
        unicodemail.send(
            from_='noreply@math.sk',
            to='gejza.jenca@gmail.com',
            cc='',
            subject=f'SSAOS 2026 -- {obj["participant"]} updated the talk information',
            message=thanks_txt,
            html=thanks_html
        )
    return thanks_html

@app.route('/slides_form/<objid>',methods=["GET","POST"])
def slides_form(objid):

    error=None
    t=env.get_template('talk_slides_form.html')
    try:
        with open(yaml_talk_fnm(objid)) as f:
            obj=yaml.load(f,Loader=yaml.Loader)
    except FileNotFoundError:
        abort(404)
    try:
        st=os.stat(slides_fnm(objid))
        have_slides=True
        slides_length=st.st_size
    except FileNotFoundError:
        have_slides=False
        slides_length=-1
    obj['slides_uploaded']=False
    if request.method=='POST':
        print(request.form,file=sys.stderr)
        for name in request.form:
            if name in obj:
                obj[name]=request.form[name]
        if 'slides_pdf' in request.files:
            file=request.files['slides_pdf']
            if not file.filename=='':
                if not file.filename.lower().endswith('.pdf'):
                    error=f'{file.filename} does not appear to be a PDF file'
                    return t.render(obj=obj,action=request.url,error=error)
                else:
                    obj['slides_uploaded']=True
                    file.save(slides_fnm(objid))
        f=tempfile.NamedTemporaryFile(delete=False,mode='w')
        f.write(yaml.dump(obj,allow_unicode=True))
        f.close()
        shutil.move(f.name,yaml_talk_fnm(objid))
        return redirect(url_for('thanks_slides',objid=objid))
    return t.render(obj=obj,
                    error=error,
                    have_slides=have_slides,
                    slides_length=slides_length,
                    slides_url=url_for('slides',objid=objid)
                    )

@app.route('/data/<objid>',methods=["GET","POST"])
def abstract_form(objid):

    error=None
    t=env.get_template('talk_abstract_form.html')
    try:
        with open(yaml_talk_fnm(objid)) as f:
            obj=yaml.load(f,Loader=yaml.Loader)
    except FileNotFoundError:
        abort(404)
    try:
        st=os.stat(abstract_fnm(objid))
        have_abstract=True
        abstract_length=st.st_size
    except FileNotFoundError:
        have_abstract=False
        abstract_length=-1
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
                    file.save(abstract_fnm(objid))
        f=tempfile.NamedTemporaryFile(delete=False,mode='w')
        f.write(yaml.dump(obj,allow_unicode=True))
        f.close()
        shutil.move(f.name,yaml_talk_fnm(objid))
        return redirect(url_for('thanks',objid=objid))
    return t.render(obj=obj,
                    error=error,
                    have_abstract=have_abstract,
                    abstract_length=abstract_length,
                    abstract_url=url_for('abstract',objid=objid)
                    )

@app.route('/data_yaml',methods=['GET','POST'])
@auth.login_required
def all_data():

    data=[]
    for objid in os.listdir(DATADIR_TALKS):
        with open(yaml_talk_fnm(objid)) as f:
            obj=yaml.load(f,Loader=yaml.Loader)
        try:
            with open(abstract_fnm(objid)) as f:
                abstract=f.read()
        except FileNotFoundError:
            abstract=None
        obj['abstract']=abstract
        data.append(obj)
    if request.method=='GET':
        yaml_data=yaml.dump_all(data,allow_unicode=True)
        return Response(yaml_data,
                        mimetype='application/yaml',
                        headers={'Content-disposition': 'attachment; filename=talks.yaml'}
                        )
    else: # POST
        uploaded=request.stream.read().decode('utf-8')
        text_stream=io.StringIO(uploaded)
        data_uploaded=yaml.safe_load_all(text_stream)
        for datum in data_uploaded:
            dirpath=abstract_dir(datum['code'])
            if os.path.isdir(dirpath):
                continue
            sys.stderr.write(f'{dirpath}\n')
            os.mkdir(dirpath)
            with open(yaml_talk_fnm(datum['code']),'w') as f:
                f.write(yaml.dump(datum,allow_unicode=True))
        return Response('201 Created',status=201)


days = ('Sunday','Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday')
#@app.route('/program')
def program():

        daylist=[]
        for i in range(1,len(days)):
            if days[i]=='Wednesday':
                continue
            daylist.append((i,days[i]))
        t=env.get_template('days.html')
        return t.render(daylist=daylist,url_for=url_for)
        


#app.run()

