from sqlite3 import Timestamp
from click import prompt
import flask
import json
from flask import Flask, render_template, Markup
import os
import argparse
import openai
import time

app = Flask(__name__)


def archive(id, dataset=False):
    from_file = "dataset.txt" if dataset else "log.txt"
    to_file = "archived_qs.txt" if dataset else "archived_log.txt"
    with open("log.txt", "r") as f:
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


def log_to_file(data):

    # save json, preserving newlines
    data["prompt"].replace("\n", "\\n")
    data["completion"].replace("\n", "\\n")
    with open("log.txt", "a") as f:
        f.write(
            json.dumps(
                data,
            )
            + "\n"
        )


def log_answer(data, logprobs, save_to_dataset=False):
    with open("answered_qs.txt", "a") as f:
        f.write(json.dumps(data) + "\n")
    if save_to_dataset:
        with open("dataset.txt", "a") as f:
            f.write(json.dumps(data) + "\n")


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
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=n_tokens,
        temperature=temp,
        logprobs=1,
    )
    completion = response.choices[0].text
    logprobs = response.choices[0].logprobs

    data["prompt"] = prompt
    data["completion"] = completion
    data["logprobs"] = logprobs
    data["time_id"] = time.time()
    log_to_file(data)


@app.route("/get_answer", methods=["POST"])
def get_answer():
    print("submit_prompt")
    # get json from request
    data = flask.request.get_json()
    print(data)
    prompt = data["prompt"]
    # send prompt to openai
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=1,
        temperature=0,
        logprobs=5,
    )
    logprobs = response.choices[0].logprobs.top_logprobs

    answer_logprobs = logprobs[0]
    data["answer_logprobs"] = logprobs
    data["time_id"] = str(int(time.time()))

    log_answer(data)

    return json.dumps(data)


@app.route("/save_example", methods=["POST"])
def save_example():
    print("save example")
    # get json from request
    data = flask.request.get_json()
    prompt = data["prompt"]
    # send prompt to openai
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=1,
        temperature=0,
        logprobs=5,
    )
    logprobs = response.choices[0].logprobs.top_logprobs
    print(logprobs)
    answer_logprobs = logprobs[0]
    print(answer_logprobs)

    log_answer(data, answer_logprobs, save_to_dataset=True)
    return "saved"


@app.route("/save_log", methods=["POST"])
def save_log():
    print("save_log")
    # get json from request
    data = flask.request.get_json()
    with open("saved.txt", "a") as f:
        f.write(json.dumps(data) + "\n")
    return "saved"


@app.route("/get_logs")
def get_logs():
    with open("log.txt", "r") as f:
        data = f.read()
    logs = []
    for line in data.split("\n")[-4:]:
        if line:
            logs.append(json.loads(line))
    logs.reverse()
    print(logs)
    return json.dumps(logs)


@app.route("/get_dataset_logs")
def get_dataset_logs():
    with open("dataset.txt", "r") as f:
        data = f.read()
    logs = []
    for line in data.split("\n")[-4:]:
        if line:
            logs.append(json.loads(line))
    logs.reverse()
    print(logs)
    return json.dumps(logs)


@app.route("/archive_log", methods=["POST"])
def archive_log():
    print("archive_log")
    # get string from request
    data = flask.request.get_json()

    print(data)
    id = data["id"]
    archive(id)
    return "archived"


@app.route("/archive_dataset_log", methods=["POST"])
def archive_dataset_log():
    print("archive_dataset_log")
    # get string from request
    data = flask.request.get_json()

    print(data)
    id = data["id"]
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
