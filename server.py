import string
from typing import List
import flask
import json
from flask import Flask, send_file
import os
import argparse
import openai
import time
import os
from flask_sqlalchemy import SQLAlchemy
from psycopg2 import Timestamp
from sqlalchemy.engine import Connection
from dataclasses import dataclass
import dataclasses
from sqlalchemy import ForeignKey, orm
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()


app = Flask(__name__, static_url_path="", static_folder="frontend/build")

database_url = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url.replace(
    "postgres://", "postgresql://"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db: SQLAlchemy = SQLAlchemy(app)
session = db.session




@dataclass
class Completion(db.Model):
    __tablename__ = "dataset"
    time_id: int
    time_id = db.Column(db.Integer, primary_key=True)

    setting: string
    setting = db.Column(db.String)

    prompt: string
    prompt = db.Column(db.String)

    completion: string
    completion = db.Column(db.String)

    engine: string
    engine = db.Column(db.String)

    temp: float
    temp = db.Column(db.Float)

    n_tokens: int
    n_tokens = db.Column(db.Integer)

    logprobs: string
    logprobs = db.Column(db.String)

    notes: string
    notes = db.Column(db.String)
@dataclass
class Test(db.Model):
    id: int
    id = db.Column(db.Integer, primary_key=True)
    text: string
    text = db.Column(db.String)
@dataclass
class NewOption(db.Model):
    id: string
    id = db.Column(db.String, primary_key=True)

    text: string
    text = db.Column(db.String)
    
    position: int
    position = db.Column(db.Integer)
    
    author: string
    author = db.Column(db.String)
    
    logprob: float
    logprob = db.Column(db.Float)
    
    correct: bool
    correct = db.Column(db.Boolean)
    
    step_id: string
    step_id = db.Column(db.String, db.ForeignKey("step.id"))
    step = db.relationship("Step", back_populates="options_list",lazy=False)
    
    reasoning: string
    reasoning = db.Column(db.String)
    
    rating: string
    rating = db.Column(db.String)
    
    selected: bool
    selected = db.Column(db.Boolean)
    
    sequence_id: string
    sequence_id = db.Column(db.String, db.ForeignKey("sequence.id"))
    
    timestamp:string
    timestamp = db.Column(db.String)
    
    engine: string
    engine = db.Column(db.String)

@dataclass
class Tag(db.Model):
    text: string
    text = db.Column(db.String, primary_key=True)


    
# tags = db.Table('tags',
#     db.Column('tag_id', db.String, db.ForeignKey('tag.text'), primary_key=True),
#     db.Column('sequence_id', db.String, db.ForeignKey('sequence.id'), primary_key=True)
# )
@dataclass
class Sequence(db.Model):
    __tablename__ = "sequence"
    setting: string
    setting = db.Column(db.String)
    
    # step_ids = db.Column(db.ARRAY(db.String, db.ForeignKey("step.id"))
    steps = db.relationship("Step", back_populates="sequence", uselist=True, lazy=False)
    
    id: string
    id = db.Column(db.String, primary_key=True)
    
    author: string
    author = db.Column(db.String)
    
    notes: string
    notes = db.Column(db.String)
    
    show: bool
    show = db.Column(db.Boolean)
    
    starred : bool
    starred = db.Column(db.Boolean)
    
    success:string
    success = db.Column(db.String)
    
    timestamp:string
    timestamp = db.Column(db.String)
    
    name:string
    name = db.Column(db.String)

    parent_ids: string
    parent_ids = db.Column(db.String)

    # tags = db.relationship("Tag", secondary=tags, lazy='False', back_populates="sequences")
    tags: string
    tags = db.Column(db.String)

@dataclass
class Step(db.Model):
    __tablename__ = "step"
    id: string
    id = db.Column(db.String, primary_key=True)

    sequence_id: string
    sequence_id = db.Column(db.String, db.ForeignKey("sequence.id"))
    sequence = db.relationship("Sequence",  foreign_keys=[sequence_id])
    
    position: int
    position = db.Column(db.Integer)
    
    environment: string
    environment = db.Column(db.String)
    
    options_list = db.relationship("NewOption", back_populates="step", lazy="joined", uselist=True)
    
    notes: string
    notes = db.Column(db.String)
    
    children_ids: string
    children_ids = db.Column(db.String)

    logprob_engine: string
    logprob_engine = db.Column(db.String)
    
    author: string
    author = db.Column(db.String)
    
    timestamp:string
    timestamp = db.Column(db.String)




def get_database_connection() -> Connection:
    return db.session.connection()


@app.route("/submit_prompt", methods=["POST"])
def submit_prompt():
    print("submit_prompt")
    # get json from request
    data = flask.request.get_json()
    print(data)
    prompt = data["text"]
    data["temp"] = float(data["temp"])
    data["n_tokens"] = int(data["n_tokens"])
    engine = data["engine"]
    # send prompt to openai
    response = openai.Completion.create(
        engine=engine,
        prompt=prompt,
        max_tokens=data["n_tokens"],
        temperature=data["temp"],
        logprobs=1,
    )
    print("getting completion from openai, engine: " + engine)
    completion = response.choices[0].text

    return flask.jsonify({'completion':completion})


@app.route("/get_options", methods=["POST"])
def get_action_options():
    print("get_action_options")
    # get json from request
    data = flask.request.get_json()
    print(data)
    prompt = data["prompt"]
    data["temp"] = float(data["temp"])
    n = int(data["n"])
    engine = data["engine"]
    # send prompt to openai
    response = openai.Completion.create(
        engine=engine,
        prompt=prompt,
        temperature=data["temp"],
        n=n,
        stop="\n",
        max_tokens=100,
    )
    print("getting completion from openai, engine: " + engine)
    print('prompt: ' + prompt)

    completions = [choice.text for choice in response.choices]
    # remove duplicates
    completions = list(set(completions))
    #remove blank
    completions = [c for c in completions if c != ""]
    print("completion: ", completions)
    return json.dumps({"option_texts": completions})

users = {
    'user': 'alignment'
}
@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username

@app.route("/")
@auth.login_required
def model_poking():
    return send_file(__file__[:-9] + "frontend/build/index.html")




@app.route("/get_logprobs", methods=["POST"])
def get_logprobs():
    print("get_logprobs")
    # get json from request
    data = flask.request.get_json()
    print(data)
    prompt = data["prompt"]
    engine = data["engine"]
    # send prompt to openai
    response = openai.Completion.create(
        engine=engine,
        prompt=prompt,
        max_tokens=1,
        temperature=0,
        logprobs=5,
    )
    print(response.choices[0])
    logprobs = response.choices[0].logprobs.top_logprobs
    answer_logprobs = logprobs[0]


    return json.dumps(
        {"answer_logprobs": answer_logprobs} 
    )


@app.route("/save_seq", methods=["POST"])
def save_seq():
    print("save_seq")
    data = flask.request.get_json()
    step_objs = []
    for step in data["steps"]:
        step_objs.append(update_step(step))
        print("added steps " + step['id'])
    data['steps'] = step_objs
    sequence = Sequence(**data)
    print("made sequence ", sequence)
    db.session.add(sequence)
    db.session.commit()
    return 'saved'

@app.route("/delete_step", methods=["POST"])
def delete_step():
    print("delete_step")
    data = flask.request.get_json()
    id = data["id"]
    step = Step.query.filter_by(id=id).first()
    db.session.delete(step)
    db.session.commit()
    return 'deleted'

@app.route("/delete_sequence", methods=["POST"])
def delete_sequence():
    print("delete_sequence")
    data = flask.request.get_json()
    id = data["id"]
    sequence = Sequence.query.filter_by(id=id).first()
    db.session.delete(sequence)
    db.session.commit()
    return 'deleted'


@app.route("/get_step", methods=["POST"])
def get_step():
    data = flask.request.get_json()
    id = data
    step = Step.query.options(orm.joinedload(Step.options_list)).filter_by(id=id).first()
    return json.dumps(dataclasses.asdict(step))

@app.route("/get_sequence", methods=["POST"])
def get_sequence():
    print("get_sequence")
    data = flask.request.get_json()
    id = data
    sequence = Sequence.query.options(orm.joinedload(Sequence.steps)).filter_by(id=id).first()
    return json.dumps(seq_to_dict(sequence))

def update_option(option:NewOption):
    option_obj = db.session.query(NewOption).filter_by(id=option['id']).first()
    if option_obj is None:
        option_obj = NewOption(**option)
        db.session.add(option_obj)
    else:
        #update option
        for key, value in option.items():
            setattr(option_obj, key, value)
    return option_obj

def update_step(step:Step):
    options_list = []
    for option in step['options_list']:
        option_obj = update_option(option)
        options_list.append(option_obj)
    step['options_list'] = options_list

    step_obj = db.session.query(Step).filter_by(id=step['id']).first()
    if step_obj is None:
        step_obj = Step(**step)
        db.session.add(step_obj)
    else:
        #update step
        for key, value in step.items():
            setattr(step_obj, key, value)
    return step_obj

def update_seq_field(object, field):
    print("update_seq")
    seq = db.session.query(Sequence).filter_by(id=object['id']).first()
    value = object[field]
    if field == 'steps':
        steps=[]
        for step in value:
            step_obj = update_step(step)
            steps.append(step_obj)
        value=steps
    #update fields
    print("updating seq", object, field,)
    print(object[field])
    setattr(seq, field, value)
    db.session.commit()

def update_step_field(object, field):
    step = db.session.query(Step).filter_by(id=object['id']).first()
    value = object[field]
    if field == 'options_list':
        new_options = []
        for option in value:
            option_obj = update_option(option)
            new_options.append(option_obj)
        value = new_options
        #delete old options
        for option in step.options_list:
            if option not in new_options:
                print("deleting option", option)
                db.session.delete(option)

    print("updating step", object, field,)
    print(type(value))
    print(step)
    setattr(step, field, value)
    db.session.commit()

def update_option_field(object, field):
    print("update_option", object['id'])
    option = update_option(object)
    print("updating option", object, field, option)
    print(option)
    if field == 'text' and object['text'] == '':
        print("deleting option"+'\n\n*******')
        db.session.delete(option)
    else:
        value = object[field]
        setattr(option, field, value)
    db.session.commit()
    return


@app.route("/update", methods=["POST"])
def update():
    print("update")
    # get id from request
    data = flask.request.get_json()
    print(data)
    if data['which'] == "seq":
        update_seq_field(data['object'], data['field'])
    elif data['which'] == "step":
        update_step_field(data['object'], data['field'])
    else:
        update_option_field(data['object'], data['field'])
    return "saved"



@app.route("/get_sequence_logs")
def get_sequence_logs():
    print("get_sequence_logs")
    start_time = time.time()
    n = flask.request.args.get("n", 15)
    stmt = (
        db.session.query(Sequence)
        .options(orm.joinedload(Sequence.steps))
        .filter(Sequence.show == True)
        .all()
    )
    print("finished db query, took time: ", time.time() - start_time)
    start_time = time.time()
    dict_list = [seq_to_dict(x) for x in stmt]
    dict_list = sorted(dict_list, key=lambda x: x["id"])
    dict_list = dict_list[-int(n) :]

    print("finished get_sequence_logs, took: ", time.time() - start_time)

    # print(f'dict_list: {dict_list}')
    return json.dumps(dict_list)

@app.route("/get_step_logs")
def get_step_logs():
    print("get_step_logs")
    start_time = time.time()
    n = flask.request.args.get("n", 15)
    stmt = (
        db.session.query(Step)
        .options(orm.joinedload(Step.options_list))
        .filter()
        .all()
    )
    print("finished db query, took time: ", time.time() - start_time)
    start_time = time.time()
    dict_list = [step_to_dict(x) for x in stmt]
    dict_list = dict_list[-int(n) :]

    print("finished get_step_logs, took: ", time.time() - start_time)

    # print(f'dict_list: {dict_list}')
    return json.dumps(dict_list)


@app.route("/get_tags")
def get_tags():
    print("get_tags")
    start_time = time.time()
    stmt = (
        db.session.query(Tag)
        .filter()
        .all()
    )
    tags = [x.text for x in stmt]
    tags.sort()
    print("finished db query, took time: ", time.time() - start_time)
    start_time = time.time()
    print("finished get_tags, took: ", time.time() - start_time)
    print(tags)
    # print(f'dict_list: {dict_list}')
    return json.dumps(tags)

#add tag
@app.route("/add_tag", methods=["POST"])
def add_tag():
    print("add_tag")
    data = flask.request.get_json()
    tag = Tag(text=data['tag'])
    db.session.add(tag)
    db.session.commit()
    return "saved"



def step_to_dict(step):
    d = dataclasses.asdict(step)
    d["options_list"] = [ dataclasses.asdict(option) for option in step.options_list
    ]
    return d

def seq_to_dict(example):
    d = dataclasses.asdict(example)
    d['steps'] = [step_to_dict(x) for x in example.steps]
    return d


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--file_to_db", action="store_true")
    parser.add_argument("--update_all_show", action="store_true")
    # add argument for port
    parser.add_argument("--port", type=int, default=5003)
    args = parser.parse_args()
    port = args.port
    if args.debug:
        app.debug = True

    # app.config["SERVER_NAME"] = "flask-api"
    openai.api_key = os.getenv("OPENAI_API_KEY")

    app.run(
        host="0.0.0.0" if args.public else "127.0.0.1",
        port=int(os.getenv("PORT", "5000")),
    )
