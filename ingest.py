import psycopg2
import json
import pandas as pd
import csv
import io

with open("secrets/config.json") as o:
	config = json.loads(o.read())

def pg_connect():
  username = config['database']['user']
  password = config['database']['pass']
  database = config['database']['name']
  hostname = config['database']['server']
  port = config['database']['port']
  connection = psycopg2.connect(
      database = database,
      user = username,
      password = password,
      host = hostname,
      port = port
  )
  return connection

tables = [
	"users",
	"roles",
	"role_policy",
	"policy_files",
	"accesskey",
	"policies",
	"policy_collections",
	"user_roles",
	"collections",
	"files",
	"download_logs",
	
]

connection = pg_connect()

for table in tables:
	df = pd.read_csv(f"data/{table}.tsv", sep="\t")

	cur = connection.cursor()
	try:
		print(table)
		cur.execute(f'''
			create table {table}_tmp
			as table {table}
			with no data;
		''')
		buf = io.StringIO()
		df.to_csv(buf, header=True, sep="\t", index=False)
		buf.seek(0)
		columns = next(buf).strip().split('\t')
		cur.copy_from(buf, f'{table}_tmp',
			columns=df.columns,
			null='',
			sep='\t',
		)

		updates = [f"{col} = excluded.{col}" for col in df.columns]
		# print(f'''
		# 	insert into {table} ({",".join(df.columns)})
		# 	select {",".join(df.columns)}
		# 	from {table}_tmp
		# 	on conflict (id)
		# 		do update
		# 		set {"\n".join(updates)}
		# 	;
		# ''')
		cur.execute(f'''
			insert into {table} ({",".join(df.columns)})
			select {",".join(df.columns)}
			from {table}_tmp
			on conflict (id)
				do update
				set {",\n".join(updates)}
			;
		''')
		cur.execute(f'drop table {table}_tmp;')
		connection.commit()
	except Exception as e:
		print(f"failed {table}", e)
		connection.rollback()
		cur.close()
