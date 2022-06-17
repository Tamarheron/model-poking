import json


def make_options_dict(item):
    item["options_dict"] = {}
    for i, option in enumerate(item["options"]):
        logprob = item["answer_logprobs"].get(f" {i+1}", "None")
        correct_options = item.get("correct_options", [])
        item["options_dict"][option] = {
            "correct": i in correct_options,
            "logprob": logprob,
        }


for file in ["dataset.txt", "dataset_saved.txt"]:
    with open(file, "r") as f:
        data = f.read()

    with open(file, "w") as f:
        for line in data.split("\n"):
            if line:
                line = json.loads(line)
                make_options_dict(line)
                f.write(json.dumps(line) + "\n")
