import pandas as pd
import json
import numpy as np
import psycopg2
import pickle
from picklefield import fields

cf = {
"database":"ebdb",
"user": "jokedurnez",
"host": "aah134s4xy4oa9.csqxsimytgy9.us-west-1.rds.amazonaws.com",
"port": 5432,
"passw": "###"
}

conn_str = "host={} dbname={} user={} password={}".format(cf["host"], cf["database"], cf['user'], cf['passw'])


conn = psycopg2.connect(conn_str)

df = pd.read_sql('select * from designtoolbox_designmodel',con=conn)
df[df.email=="joke.durnez@gmail.com"]

metrics = fields.dbsafe_decode(df.iloc[0]['metrics'])
fields.dbsafe_decode(df.iloc[0]['metrics'])


np.unique(df['email'])

df.columns




psql --host=aabdl6fu9ctbm7.csqxsimytgy9.us-west-1.rds.amazonaws.com --port=5432 --username jokedurnez --password --dbname=ebdb
