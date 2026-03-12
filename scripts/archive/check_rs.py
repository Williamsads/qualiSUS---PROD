import psycopg2
conn = psycopg2.connect("host=10.24.59.104 user=qualisus password=h5eXAx59gJ3h84Xa dbname=qualisus")
cur = conn.cursor()
try:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'recuperacao_senha';")
    print(cur.fetchall())
except Exception as e:
    print(e)
