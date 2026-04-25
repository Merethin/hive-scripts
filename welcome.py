# welcome.py: Generate lists of new nations to ping

import pika, sys, os, argparse, json

parser = argparse.ArgumentParser()
parser.add_argument("regions")
parser.add_argument("out_file")
parser.add_argument("seen_file")
parser.add_argument("-n", "--count", default=10, type=int)
args = parser.parse_args()

regions = args.regions.split(",")
nations = {}
seen = {}
count = args.count

try:
    with open(args.out_file, "r") as out_file:
        nations = json.load(out_file)
except Exception:
    pass

try:
    with open(args.seen_file, "r") as seen_file:
        seen = json.load(seen_file)
except Exception:
    pass

def update():
    with open(args.out_file, "w+") as out_file:
        json.dump(nations, out_file)

    with open(args.seen_file, "w+") as seen_file:
        json.dump(seen, seen_file)

for region in regions:
    if region not in nations:
        nations[region] = []
    if region not in seen:
        seen[region] = []

update()

url = os.getenv("RABBITMQ_URL")
if not url:
    print("Missing RABBITMQ_URL!")
    sys.exit(1)

connection = pika.BlockingConnection(pika.URLParameters(url))
channel = connection.channel()

channel.exchange_declare(exchange='akari_events', exchange_type='topic')

result = channel.queue_declare('', exclusive=True)
queue_name = result.method.queue

for key in ["move", "cte", "nfound", "nrefound"]:
    channel.queue_bind(exchange='akari_events', queue=queue_name, routing_key=key)

def callback(ch, method, properties, body):
    event = json.loads(body)
    if event["category"] == "cte":
        if event["origin"] in regions:
            try:
                nations[event["origin"]].remove(event["receptor"])
                seen[event["origin"]].remove(event["receptor"]) # re-ping if revived

                update()
            except ValueError:
                pass
    elif event["category"] == "move":
        if event["origin"] in regions:
            try:
                nations[event["origin"]].remove(event["actor"])

                update()
            except ValueError:
                pass
        if event["destination"] in regions:
            if event["actor"] in seen[event["destination"]]:
                return

            nations[event["destination"]].append(event["actor"])
            seen[event["destination"]].append(event["actor"])

            while len(nations[event["destination"]]) > count:
                nations[event["destination"]].pop(0)

            update()
    elif event["category"] in ["nfound", "nrefound"]:
        if event["origin"] in regions:
            nations[event["origin"]].append(event["actor"])
            seen[event["origin"]].append(event["actor"])

            while len(nations[event["origin"]]) > count:
                nations[event["origin"]].pop(0)

            update()

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()