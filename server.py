import string
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
from sqlalchemy import orm


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
    step = db.relationship("Step", back_populates="options_list")
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
@dataclass
class Step(db.Model):
    id: string
    id = db.Column(db.String, primary_key=True)
    sequence_id: string
    sequence_id = db.Column(db.String, db.ForeignKey("sequence.id"))
    sequence = db.relationship("Sequence", back_populates="steps")
    position: int
    position = db.Column(db.Integer)
    environment: string
    environment = db.Column(db.String)
    options_list = db.relationship("NewOption", back_populates="step")
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
@dataclass
class Sequence(db.Model):
    setting: string
    setting = db.Column(db.String)
    steps = db.relationship("Step", back_populates="sequence")
    id: string
    id = db.Column(db.String, primary_key=True)
    parent_ids: string
    parent_ids = db.Column(db.String)
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


@app.route("/get_action_options", methods=["POST"])
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

    completions = [choice.text for choice in response.choices]
    # remove duplicates
    completions = list(set(completions))
    print("completion: ", completions)
    return json.dumps({"option_texts": completions})


@app.route("/")
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
    db.session.add(Sequence(**data))
    for step in data["steps"]:
        db.session.add(Step(**step))
        for option in step["options_list"].values():
            db.session.add(NewOption(**option))
    db.session.commit()
    return 'saved'

def update_seq(object, field):
    print("update_seq")
    seq = db.session.query(Sequence).filter_by(id=object['id']).first()
    value = object[field]
    if field == 'steps':
        steps=[]
        for step in value:
            step_obj = db.session.query(Step).filter_by(id=step['id']).first()
            if step_obj is None:
                new_options = []
                for option in step['options_list']:
                    new_option = NewOption(**option)    
                    new_options.append(new_option)
                    db.session.add(new_option)


                step['options_list'] = new_options
                step_obj = Step(**step)
                db.session.add(step_obj)
            steps.append(step_obj)
        value=steps
    #update fields
    print("updating seq", object, field,)
    print(object[field])
    setattr(seq, field, value)
    db.session.commit()

def update_step(object, field):
    step = db.session.query(Step).filter_by(id=object['id']).first()
    value = object[field]
    if field == 'options_list':
        new_options = []
        for option in value:
            option_obj = db.session.query(NewOption).filter_by(id=option['id']).first()
            if option_obj is None:
                option_obj = NewOption(**option)
                db.session.add(option_obj)
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

def update_option(object, field):
    option = db.session.query(NewOption).filter_by(id=object['id']).first()
    print("updating option", object, field,)
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
        update_seq(data['object'], data['field'])
    elif data['which'] == "step":
        update_step(data['object'], data['field'])
    else:
        update_option(data['object'], data['field'])
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

    print(f'dict_list: {dict_list}')
    return json.dumps(dict_list)


def step_to_dict(step):
    print("step_to_dict")
    d = dataclasses.asdict(step)
    d["options_list"] = [ dataclasses.asdict(option) for option in step.options_list
    ]
    return d

def seq_to_dict(example):
    print("seq_to_dict")
    print(example)
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
        threaded=True,
    )
