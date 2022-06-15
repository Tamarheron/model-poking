from imaplib import IMAP4_stream
import flask
import json
from flask import Flask
import os
import argparse
import openai
import time

app = Flask(__name__)


def archive(id, dataset=False):
    from_file = "dataset.txt" if dataset else "log.txt"
    to_file = "archived_dataset_log.txt" if dataset else "archived_log.txt"
    with open(from_file, "r") as f:
        data = f.read()

    # save to temporary file
    with open("tmp.txt", "w") as f:
        f.write(data)

    line_to_remove = None

    with open(from_file, "w") as f:
        for line in data.split("\n"):
            if line:
                line = json.loads(line)
                if int(line["time_id"]) != int(id):
                    f.write(json.dumps(line) + "\n")
                else:
                    line_to_remove = line
                    # write to archive
    with open(to_file, "a") as f:
        f.write(json.dumps(line_to_remove) + "\n")


def log_to_file(data, dataset=False):
    filename = "dataset.txt" if dataset else "log.txt"
    # save json, preserving newlines
    data["prompt"].replace("\n", "\\n")
    data["completion"].replace("\n", "\\n")
    with open(filename, "a") as f:
        f.write(
            json.dumps(
                data,
            )
            + "\n"
        )


def add_to_saved(id, dataset=False):
    filename = "dataset" if dataset else "log"
    with open(filename + ".txt", "r") as f:
        data = f.read()
    filename += "_saved.txt"
    with open(filename, "a") as f:
        for line in data.split("\n"):
            if line:
                line = json.loads(line)
                if int(line["time_id"]) == int(id):
                    f.write(json.dumps(line) + "\n")


def make_options_dict(item):
    item["options_dict"] = {}
    for i, option in enumerate(item["options"]):
        logprob = item["answer_logprobs"].get(f" {i+1}", "None")
        correct_options = item.get("correct_options", [])
        item["options_dict"][option] = {
            "correct": i in correct_options,
            "logprob": logprob,
        }


def update_options_dict(item):
    for i, option in enumerate(item["options"]):
        logprob = item["answer_logprobs"].get(f" {i+1}", "None")
        item["options_dict"][option]["logprob"] = logprob


def get_logs_from_file(dataset=False):
    filename = "dataset.txt" if dataset else "log.txt"
    with open(filename, "r") as f:
        data = f.read()
    logs = []
    for line in data.split("\n"):
        if line:
            item = json.loads(line)
            if dataset:
                if not "options_dict" in item:
                    make_options_dict(item)
            logs.append(item)

    logs.reverse()
    return json.dumps(logs)


@app.route("/submit_prompt", methods=["POST"])
def submit_prompt():
    print("submit_prompt")
    # get json from request
    data = flask.request.get_json()
    print(data)
    prompt = data["text"]
    temp = float(data["temp"])
    n_tokens = int(data["n_tokens"])
    engine = data["engine"]
    # send prompt to openai
    response = openai.Completion.create(
        engine=engine,
        prompt=prompt,
        max_tokens=n_tokens,
        temperature=temp,
        logprobs=1,
    )
    print("getting completion from openai, engine: " + engine)
    completion = response.choices[0].text
    logprobs = response.choices[0].logprobs

    data["prompt"] = prompt
    data["completion"] = completion
    data["logprobs"] = logprobs
    data["time_id"] = time.time()
    log_to_file(data)
    return flask.jsonify(data)


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
    data["time_id"] = str(int(time.time()))
    data["completion"] = response.choices[0].text
    update_options_dict(data)
    print(data["options_dict"])
    log_to_file(data, dataset=True)

    return json.dumps(data)


@app.route("/save_dataset_log", methods=["POST"])
def save_dataset_log():
    print("save_dataset_log")
    # get id from request
    data = flask.request.get_json()
    # print(data)

    add_to_saved(data["time_id"], dataset=True)
    return "saved"


@app.route("/update_correct_options", methods=["POST"])
def update_correct_options():
    print("update_correct_options")
    # get id from request
    data = flask.request.get_json()
    print(data)

    id = data["time_id"]
    option = data["option"]
    new_val = data["new_val"]
    for file in ["dataset", "archived_dataset_log", "dataset_saved"]:
        with open(file + ".txt", "r") as f:
            filedata = f.read()
        with open("tmp.txt", "w") as f:
            f.write(filedata)
        with open(file + ".txt", "w") as f:
            for line in filedata.split("\n"):
                if line:
                    line = json.loads(line)
                    if line:
                        if int(line["time_id"]) == int(id):
                            if option in line["options_dict"]:
                                line["options_dict"][option]["correct"] = new_val
                        f.write(json.dumps(line) + "\n")
    return "updated"


@app.route("/save_log", methods=["POST"])
def save_log():
    print("save_log")
    # get json from request
    data = flask.request.get_json()

    add_to_saved(data["time_id"])
    return "saved"


@app.route("/get_logs")
def get_logs():
    return get_logs_from_file()


@app.route("/get_dataset_logs")
def get_dataset_logs():
    return get_logs_from_file(dataset=True)


@app.route("/archive_log", methods=["POST"])
def archive_log():
    print("archive_log")
    # get string from request
    data = flask.request.get_json()

    print(data)
    id = data["time_id"]
    archive(id)
    return "archived"


@app.route("/archive_dataset_log", methods=["POST"])
def archive_dataset_log():
    print("archive_dataset_log")
    # get string from request
    data = flask.request.get_json()
    print(data)
    id = data["time_id"]
    archive(id, dataset=True)
    return "archived"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--debug", action="store_true")

    # add argument for port
    parser.add_argument("--port", type=int, default=5004)
    args = parser.parse_args()
    port = args.port
    aws = True
    push_to_aws = True
    if args.debug:
        app.debug = True
        push_to_aws = False
    openai.api_key = os.getenv("OPENAI_API_KEY")
    app.run(
        host="0.0.0.0" if args.public else "127.0.0.1",
        port=port,
    )
