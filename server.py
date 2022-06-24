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
from sqlalchemy.engine import Connection
from dataclasses import dataclass
import dataclasses
from sqlalchemy import orm


app = Flask(__name__, static_url_path="", static_folder="frontend/build")

# database_url = os.getenv("DATABASE_URL")
# if database_url:
#     app.config["SQLALCHEMY_DATABASE_URI"] = database_url.replace(
#         "postgres://", "postgresql://"
#     )
# app.config["SECRET_KEY"] = os.getenv("SECRET_KEY") or "DEVELOPMENT SECRET KEY"
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # get rid of warning
database_url = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url.replace(
    "postgres://", "postgresql://"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db: SQLAlchemy = SQLAlchemy(app)
session = db.session


@dataclass
class Option(db.Model):
    __tablename__ = "option"
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
    example_id: int
    example_id = db.Column(db.Integer, db.ForeignKey("dataset_example.time_id"))
    dataset_example = db.relationship("DatasetExample", back_populates="options_dict")
    reasoning: string
    reasoning = db.Column(db.String)
    rating: string
    rating = db.Column(db.String)


@dataclass
class DatasetExample(db.Model):
    __tablename__ = "dataset_example"
    time_id: int
    time_id = db.Column(db.Integer, primary_key=True)

    setting: string
    setting = db.Column(db.String)

    prompt: string
    prompt = db.Column(db.String)

    interaction: string
    interaction = db.Column(db.String)

    answer_logprobs: dict
    answer_logprobs = db.Column(db.JSON)

    options_dict = db.relationship("Option", back_populates="dataset_example")

    engine: string
    engine = db.Column(db.String)

    author: string
    author = db.Column(db.String)

    show: bool
    show = db.Column(db.Boolean)

    star: bool
    star = db.Column(db.Boolean)

    notes: string
    notes = db.Column(db.String)

    completion: string
    completion = db.Column(db.String)

    main: bool
    main = db.Column(db.Boolean)


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


def get_database_connection() -> Connection:
    return db.session.connection()


def make_options_dict(item):
    for _, v in item["options_dict"].items():
        v["id"] = v["text"] + str(item["time_id"])
        v["example_id"] = item["time_id"]
        v["logprob"] = -100


def add_logprobs(item):
    for _, v in item["options_dict"].items():
        logprob = item["answer_logprobs"].get(f" {v['position']+1}", "None")
        v["logprob"] = -100.0 if logprob == "None" else float(logprob)


# def update_options_dict(item):
#     current = item["options_dict"]
#     item["options_dict"] = []
#     for i, text in enumerate(current.keys()):
#         d = current.get(text)
#         d["position"] = i
#         d["example_id"] = item["time_id"]
#         d["text"] = text
#         d["logprob"] = -100.0 if d["logprob"] == "None" else float(d["logprob"])
#         d["id"] = text + str(item["time_id"])
#         # print(d["author"])
#         # d["author"] = d["author"]
#         item["options_dict"].append(Option(**d))


def file_to_db(filename):
    with open(filename, "r") as f:
        data = f.readlines()
    for line in data:
        item = json.loads(line)
        update_options_dict(item)
        if filename[-11:] == "dataset.txt":
            item["show"] = True
        item.pop("options")
        if item.get("correct_options"):
            item.pop("correct_options")

        # check if already in db
        if not DatasetExample.query.filter_by(time_id=item["time_id"]).first():
            db.session.add(DatasetExample(**item))
            db.session.commit()


def update_all_show():
    for example in DatasetExample.query.all():
        example.show = True
        db.session.commit()


def update_all_main():
    for example in DatasetExample.query.all():
        example.main = True
        db.session.commit()


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
    logprobs = response.choices[0].logprobs
    print("completion: " + completion)

    data["prompt"] = prompt
    data["completion"] = completion
    data["logprobs"] = json.dumps(logprobs)
    data["time_id"] = int(time.time())
    data.pop("text")

    db.session.add(Completion(**data))
    db.session.commit()

    return flask.jsonify(data)


@app.route("/get_action_options", methods=["POST"])
def get_action_options():
    print("get_action_options")
    # get json from request
    data = flask.request.get_json()
    print(data)
    prompt = data["text"] + "\n> Action:"
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
    text = data["text"] + "\nOptions:"
    for i, completion in enumerate(completions):
        text += f"\n{i+1}){completion}"
    print(len(text))
    return json.dumps({"text": text})


@app.route("/")
def model_poking():
    return send_file(__file__[:-9] + "frontend/build/index.html")


@app.route("/submit_options", methods=["POST"])
def get_answer():
    print("submit_options")
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
    data["answer_logprobs"] = answer_logprobs
    data["completion"] = str(response.choices[0].text)
    add_logprobs(data)
    print(data["options_dict"])

    stmt = (
        db.session.query(DatasetExample)
        .filter(DatasetExample.time_id == data["time_id"])
        .first()
    )
    stmt.answer_logprobs = data["answer_logprobs"]
    stmt.completion = data["completion"]

    db.session.commit()

    for option in data["options_dict"].values():
        print(option)
        stmt = db.session.query(Option).filter(Option.id == option["id"]).first()
        stmt.logprob = option["logprob"]
        # print(stmt)
        db.session.commit()

    return json.dumps(
        {
            "options_dict": data["options_dict"],
            "answer_logprobs": data["answer_logprobs"],
            "completion": data["completion"],
        }
    )


@app.route("/save_example", methods=["POST"])
def save_example():
    print("save_example")
    # get json from request
    data = flask.request.get_json()
    data["time_id"] = str(int(time.time()))
    data["show"] = True
    data["main"] = True
    data["notes"] = ""
    make_options_dict(data)
    print(data["options_dict"])
    tmp_options_dict = data["options_dict"]
    data["options_dict"] = [Option(**d) for d in tmp_options_dict.values()]

    print(db.session)
    db.session.add(DatasetExample(**data))
    db.session.commit()

    # convert options_dict (now list of type Option) back to dict
    data["options_dict"] = {
        option.id: dataclasses.asdict(option) for option in data["options_dict"]
    }

    return json.dumps(data)


@app.route("/update_dataset_log", methods=["POST"])
def update_dataset_log():
    print("update_dataset_log")
    # get id from request
    data = flask.request.get_json()
    print(data)

    stmt = (
        db.session.query(DatasetExample)
        .filter(DatasetExample.time_id == data["time_id"])
        .first()
    )
    stmt.options = data["options_dict"]
    stmt.notes = data.get("notes")
    stmt.show = data.get("show", True)
    stmt.star = data.get("star", False)
    stmt.main = data.get("main", True)
    stmt.author = data["author"]
    stmt.interaction = data["interaction"]

    db.session.commit()

    # update options table also
    for option in data["options_dict"].values():
        print(option)
        stmt = db.session.query(Option).filter(Option.id == option["id"]).first()

        stmt.correct = option["correct"]
        stmt.logprob = option["logprob"]
        stmt.author = option.get("author", "")
        stmt.reasoning = option.get("reasoning", "")
        stmt.rating = option.get("rating", "")
        stmt.text = option["text"]
        # print(stmt)
        db.session.commit()

    return "saved"


@app.route("/get_dataset_logs")
def get_dataset_logs():
    print("get_dataset_logs")
    start_time = time.time()
    n = flask.request.args.get("n", 15)
    stmt = (
        db.session.query(DatasetExample)
        .options(orm.joinedload(DatasetExample.options_dict))
        .filter(DatasetExample.show == True)
        .all()
    )
    print("finished db query, took time: ", time.time() - start_time)
    start_time = time.time()
    print(stmt[0].options_dict)
    print(stmt[-1].options_dict)
    print(stmt[1].options_dict)

    dict_list = [to_dict(x) for x in stmt]
    dict_list = sorted(dict_list, key=lambda x: x["time_id"])
    dict_list = dict_list[-int(n) :]
    # if app.debug:
    #     dict_list = dict_list[-3:]

    print("finished get_dataset_logs, took: ", time.time() - start_time)

    # print(dict_list[1])
    return json.dumps(dict_list)


@app.route("/get_logs")
def get_logs():
    print("get_logs")
    start_time = time.time()
    stmt = db.session.query(Completion).all()
    stmt = stmt[:10]
    dict_list = [dataclasses.asdict(x) for x in stmt]
    print("finished getting logs, took: ", time.time() - start_time)
    # print(dict_list[1])
    return json.dumps(dict_list)


def to_dict(example):
    d = dataclasses.asdict(example)
    if d["notes"] == None:
        d["notes"] = ""
    d["options_dict"] = {
        option.id: dataclasses.asdict(option) for option in example.options_dict
    }

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
    if args.file_to_db:
        file_to_db("dataset.txt")
        exit()
    if args.update_all_show:
        update_all_show()
        exit()
    if args.debug:
        app.debug = True

    # app.config["SERVER_NAME"] = "flask-api"
    openai.api_key = os.getenv("OPENAI_API_KEY")

    app.run(
        host="0.0.0.0" if args.public else "127.0.0.1",
        port=int(os.getenv("PORT", "5000")),
        threaded=True,
    )
