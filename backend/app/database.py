import os
import psycopg2
from dotenv import load_dotenv

# Garante que as variáveis de ambiente sejam carregadas
load_dotenv()

def get_connection():
    """
    Retorna uma conexão com o banco de dados PostgreSQL usando 
    variáveis de ambiente para segurança.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
