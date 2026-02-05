import pandas as pd
import psycopg2

# =========================
# CONEXÃO COM O BANCO
# =========================
def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

# =========================
# LEITURA DO EXCEL
# =========================
df = pd.read_excel(
    r"C:\Users\williams.sobrinho\Downloads\FOLHA NOVA NOVEMBRO'2025 - ENVIO.xlsx"
)

# =========================
# FUNÇÃO CPF (IGUAL AO EXCEL)
# =========================
def limpa_cpf(cpf):
    if pd.isna(cpf):
        return None

    cpf_str = str(cpf).strip()

    # remove ".0" se vier como float
    if cpf_str.endswith(".0"):
        cpf_str = cpf_str[:-2]

    # mantém apenas números
    cpf_str = ''.join(filter(str.isdigit, cpf_str))

    if not cpf_str:
        return None

    # garante 11 dígitos (preserva padrão do Excel)
    return cpf_str.zfill(11)

# =========================
# CARGA DE DADOS
# =========================
conn = get_connection()
cursor = conn.cursor()

try:
    for index, row in df.iterrows():

        cpf = limpa_cpf(row.get("CPF"))

        # 🚫 ignora CPF inválido
        if not cpf:
            print(f"Linha {index + 2} ignorada (CPF inválido)")
            continue

        # =========================
        # VERIFICA TRABALHADOR
        # =========================
        cursor.execute(
            "SELECT id FROM trabalhadores WHERE cpf = %s",
            (cpf,)
        )
        resultado = cursor.fetchone()

        if resultado:
            trabalhador_id = resultado[0]
        else:
            cursor.execute("""
                INSERT INTO trabalhadores (
                    nome_completo,
                    cpf,
                    data_nascimento,
                    telefone,
                    email,
                    logradouro,
                    cidade
                ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
            """, (
                row.get("NOME DO SERVIDOR"),
                cpf,
                pd.to_datetime(row.get("DATA NASCIMENTO"), errors="coerce"),
                None if pd.isna(row.get("FONE")) else str(row.get("FONE")),
                None if pd.isna(row.get("E-MAIL")) else row.get("E-MAIL"),
                None if pd.isna(row.get("ENDERECO")) else row.get("ENDERECO"),
                None if pd.isna(row.get("CIDADE")) else row.get("CIDADE"),
            ))

            trabalhador_id = cursor.fetchone()[0]

        # =========================
        # EVITA VÍNCULO DUPLICADO
        # =========================
        cursor.execute("""
            SELECT 1
              FROM vinculos_trabalhadores
             WHERE trabalhador_id = %s
               AND numero_funcional = %s
        """, (
            trabalhador_id,
            row.get("MATRICULA SGP")
        ))

        if cursor.fetchone():
            print(f"Vínculo já existe (CPF {cpf})")
            continue

        # =========================
        # INSERE VÍNCULO
        # =========================
        cursor.execute("""
            INSERT INTO vinculos_trabalhadores (
                trabalhador_id,
                numero_funcional,
                tipo_vinculo,
                especialidade,
                unidade_lotacao,
                data_admissao
            ) VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            trabalhador_id,
            row.get("MATRICULA SGP"),
            row.get("VINCULO"),
            row.get("FUNÇÃO FICHA"),
            row.get("UNIDADE FOLHA"),
            pd.to_datetime(row.get("DATA ADMISSAO"), errors="coerce"),
        ))

    conn.commit()
    print("✅ Carga realizada com sucesso")

except Exception as e:
    conn.rollback()
    print("❌ Erro durante a carga:", e)

finally:
    cursor.close()
    conn.close()
