# slackers.py: Generate lists of nations not endorsing a nation / nations

import psycopg2, sys, os, argparse, json

parser = argparse.ArgumentParser()
parser.add_argument("region")
parser.add_argument("exclude")
parser.add_argument("out_file")
args = parser.parse_args()

def open_db():
    url = os.getenv("DATABASE_URL")
    if url is None:
        print("DATABASE_URL not provided in the environment!", file=sys.stderr)
        sys.exit(1)

    return psycopg2.connect(url)

def check_endorsements(cursor, nation: str):
    cursor.execute("SELECT endorsements FROM nations_dump WHERE canon_name = %s", (nation, ))
    result = cursor.fetchone()

    return set(result[0])

def check_region_was(cursor, region: str):
    cursor.execute("SELECT canon_name FROM nations_dump WHERE is_wa = TRUE AND region = %s", (region, ))
    result = cursor.fetchall()

    return set([row[0] for row in result])

db = open_db()
cursor = db.cursor()

exclude = args.exclude.split(",")
endos_given = {}

nations = check_region_was(cursor, args.region)

for nation in nations:
    endos = check_endorsements(cursor, nation)

    for endo in endos:
        if endo in exclude:
            continue
        elif endo not in nations:
            continue
        elif endo in endos_given:
            endos_given[endo] += 1
        else:
            endos_given[endo] = 1

output = [{"nation":k, "endos":v} for k,v in endos_given.items()]
output = sorted(output, key=lambda a:a["endos"], reverse=True)

with open(args.out_file, "w+") as out_file:
    json.dump(output, out_file)