# region.py: Generate real-time lists of nations slacking, endorsing officers, and endorsing each other in a region

import argparse, json, sseclient, os, sys, requests

parser = argparse.ArgumentParser()
parser.add_argument("region")
parser.add_argument("nations")
parser.add_argument("out_file")
args = parser.parse_args()

region = args.region
nations = args.nations.split(",")

def create_sse_feed(url):
    res = requests.get(url, stream=True)
    yield from sseclient.SSEClient(res).events()

def get_endorsements(state, nation):
    for n in state["nations"]:
        if n["name"] == nation:
            return set(n["endorsements"])

    return set()

def get_members(state):
    return set([n["name"] for n in state["nations"]])

def calculate_slackers(state):
    members = get_members(state)

    slackers = {}
    for nation in nations:
        endos = get_endorsements(state, nation)
        diff = members.difference(endos)
        diff.discard(nation)
        slackers[nation] = sorted(list(diff))

    return slackers

def calculate_endorsers(state):
    sets = [get_endorsements(state, nation) for nation in nations]
    members = get_members(state)
    return sorted(list(members.intersection(*sets)))

def calculate_tart(state):
    members = get_members(state)

    endos_given = {}
    for nation in state["nations"]:
        endos = nation["endorsements"]

        for endo in endos:
            if endo in nations:
                continue
            elif endo not in members:
                continue
            elif endo in endos_given:
                endos_given[endo] += 1
            else:
                endos_given[endo] = 1

    output = [{"nation":k, "endos":v} for k,v in endos_given.items()]
    return sorted(output, key=lambda a:a["endos"], reverse=True)

def build_and_save_output(state):
    output = {
        "slackers": calculate_slackers(state),
        "endorsers": calculate_endorsers(state),
        "tart": calculate_tart(state)
    }

    with open(args.out_file, "w+") as out_file:
        json.dump(output, out_file)

retina_url = os.getenv("RETINA_URL")

response = requests.get(f"{retina_url}/region/{region}")
if response.status_code != 200:
    print("Error: region not found")
    sys.exit(1)

state = json.loads(response.text)
build_and_save_output(state)

for event in create_sse_feed(f"{retina_url}/sse/region:{region}"):
    obj = json.loads(event.data)
    for name, state in obj["state"].items():
        if name == region:
            build_and_save_output(state)