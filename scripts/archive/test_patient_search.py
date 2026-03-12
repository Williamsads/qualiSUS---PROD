import psycopg2
from psycopg2.extras import RealDictCursor

def test_search():
    conn = psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Teste 1: Verificar se há trabalhadores
    cur.execute("SELECT COUNT(*) as total FROM trabalhadores")
    total = cur.fetchone()
    print(f"Total de trabalhadores: {total['total']}")
    
    # Teste 2: Listar alguns CPFs
    cur.execute("SELECT id, nome_completo, cpf FROM trabalhadores LIMIT 5")
    print("\nPrimeiros 5 trabalhadores:")
    for row in cur.fetchall():
        print(f"  ID: {row['id']} | Nome: {row['nome_completo']} | CPF: {row['cpf']}")
    
    # Teste 3: Testar busca por CPF específico
    test_cpf = "1254845"  # CPF do log
    cur.execute("""
        SELECT
            t.id,
            t.nome_completo,
            t.cpf,
            vt.numero_funcional
        FROM trabalhadores t
        LEFT JOIN vinculos_trabalhadores vt ON vt.trabalhador_id = t.id
        WHERE t.cpf = %s OR vt.numero_funcional = %s
        LIMIT 1
    """, (test_cpf, test_cpf))
    
    result = cur.fetchone()
    if result:
        print(f"\n✓ Encontrado com CPF/Funcional '{test_cpf}':")
        print(f"  Nome: {result['nome_completo']}")
        print(f"  CPF: {result['cpf']}")
    else:
        print(f"\n✗ NÃO encontrado com '{test_cpf}'")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    test_search()
