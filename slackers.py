# slackers.py: Generate lists of nations not endorsing a nation / nations

import psycopg2, sys, os, argparse, json

parser = argparse.ArgumentParser()
parser.add_argument("nations")
parser.add_argument("out_file")
args = parser.parse_args()

def open_db():
    url = os.getenv("DATABASE_URL")
    if url is None:
        print("DATABASE_URL not provided in the environment!", file=sys.stderr)
        sys.exit(1)

    return psycopg2.connect(url)

def check_endorsements(cursor, nation: str):
    cursor.execute("SELECT endorsements, region FROM nations_dump WHERE canon_name = %s", (nation, ))
    result = cursor.fetchone()

    return (set(result[0]), result[1])

def check_region_was(cursor, region: str):
    cursor.execute("SELECT canon_name FROM nations_dump WHERE is_wa = TRUE AND region = %s", (region, ))
    result = cursor.fetchall()

    return set([row[0] for row in result])

db = open_db()
cursor = db.cursor()

nations = args.nations.split(",")
slackers = {}

for nation in nations:
    (endos, region) = check_endorsements(cursor, nation)
    was = check_region_was(cursor, region)

    was.remove(nation)
    slackers[nation] = list(was.difference(endos))

with open(args.out_file, "w+") as out_file:
    json.dump(slackers, out_file)