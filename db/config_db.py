import mysql.connector

# Conexão com o banco
conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="1006",
    database="qualivida"
)

cursor = conn.cursor()