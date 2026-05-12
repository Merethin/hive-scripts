# endorsers.py: Generate a list of nations endorsing all of the specified nations

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
    cursor.execute("SELECT endorsements FROM nations_dump WHERE canon_name = %s", (nation, ))
    result = cursor.fetchone()

    return set(result[0])

db = open_db()
cursor = db.cursor()

nations = args.nations.split(",")

sets = [check_endorsements(cursor, nation) for nation in nations]
result = sorted(list(set.intersection(*sets)))

with open(args.out_file, "w+") as out_file:
    json.dump(result, out_file)