import psycopg2

url = input("Cole a connection string do Neon e aperte Enter: ").strip()

conn = psycopg2.connect(url, connect_timeout=15)
cur = conn.cursor()

cur.execute("SELECT count(*), count(embedding) FROM documentos")
print("linhas, com embedding:", cur.fetchone())

q = """SELECT id, embedding <=> (SELECT embedding FROM documentos LIMIT 1) AS d
       FROM documentos ORDER BY d LIMIT 5"""

cur.execute("EXPLAIN " + q)
print("plano:", [linha[0] for linha in cur.fetchall()])

cur.execute(q)
print("busca padrao:", cur.fetchall())

cur.execute("SET enable_indexscan = off")
cur.execute(q)
print("busca sem indice:", cur.fetchall())