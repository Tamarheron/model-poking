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


def archive(id):
    with open("log.txt", "r") as f:
        data = f.read()

    line_to_remove = None
    with open("log.txt", "w") as f:
        for line in data.split("\n"):
            if line:
                line = json.loads(line)
                if int(line["time_id"]) != int(id):
                    f.write(json.dumps(line) + "\n")
                else:
                    line_to_remove = line
                    # write to archive
    with open("archive.txt", "a") as f:
        f.write(json.dumps(line_to_remove) + "\n")


def log_to_file(data, logprobs, completion):
    prompt = data["text"]
    temp = data["temp"]
    # make id
    id = str(int(time.time()))
    # save json, preserving newlines
    prompt.replace("\n", "\\n")
    completion.replace("\n", "\\n")
    with open("log.txt", "a") as f:
        f.write(
            json.dumps(
                {
                    "temp": temp,
                    "prompt": prompt,
                    "completion": completion,
                    "logprobs": logprobs,
                    "time_id": id,
                }
            )
            + "\n"
        )


def log_answer(data, logprobs):
    data["answer_logprobs"] = logprobs
    data["time_id"] = str(int(time.time()))
    with open("answered_qs.txt", "a") as f:
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
    print(completion)
    log_to_file(data, logprobs, completion)
    return completion


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
    print(logprobs)
    answer_logprobs = logprobs[0]
    print(answer_logprobs)

    log_answer(data, answer_logprobs)
    return json.dumps(answer_logprobs)


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


@app.route("/archive_log", methods=["POST"])
def archive_log():
    print("archive_log")
    # get string from request
    data = flask.request.get_json()

    print(data)
    id = data["id"]
    archive(id)
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
