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


def get_logs_from_file(dataset=False):
    filename = "dataset.txt" if dataset else "log.txt"
    with open(filename, "r") as f:
        data = f.read()
    logs = []
    for line in data.split("\n"):
        if line:
            item = json.loads(line)
            if dataset:
                if not "correct_options" in item:
                    item["correct_options"] = [0]
            logs.append(item)

    logs.reverse()
    print(logs)
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

    log_to_file(data, dataset=True)

    return json.dumps(data)


@app.route("/save_dataset_log", methods=["POST"])
def save_dataset_log():
    print("save_dataset_log")
    # get id from request
    data = flask.request.get_json()
    print(data)

    add_to_saved(data["time_id"], dataset=True)
    return "saved"


@app.route("/update_correct_options", methods=["POST"])
def update_correct_options():
    print("update_correct_options")
    # get id from request
    data = flask.request.get_json()
    print(data)

    id = data["time_id"]
    index = data["index"]
    new_val = data["new_val"]
    for file in ["dataset", "archived_dataset_log", "dataset_saved"]:
        with open(file + ".txt", "r") as f:
            filedata = f.read()
        with open(file + ".txt", "w") as f:
            for line in filedata.split("\n"):
                if line:
                    line = json.loads(line)
                    if line:
                        if int(line["time_id"]) == int(id):
                            if new_val:
                                line["correct_options"].append(index)
                            else:
                                line["correct_options"] = [
                                    i for i in line["correct_options"] if i != index
                                ]
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
    engine = "davinci:ft-personal-2022-06-15-00-41-02"
    push_to_aws = True
    if args.debug:
        app.debug = True
        push_to_aws = False
    openai.api_key = os.getenv("OPENAI_API_KEY")
    app.run(
        host="0.0.0.0" if args.public else "127.0.0.1",
        port=port,
    )
