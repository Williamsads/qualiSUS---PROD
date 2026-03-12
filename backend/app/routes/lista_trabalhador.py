from flask import request, render_template
from psycopg2.extras import RealDictCursor
from flask import Blueprint
import psycopg2
<<<<<<< HEAD
from app.database import get_connection
trabalhadores_bp = Blueprint('trabalhadores', __name__, url_prefix="/trabalhadores")

=======
trabalhadores_bp = Blueprint('trabalhadores', __name__, url_prefix="/trabalhadores")

# --- Função de conexão com o banco ---
def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

>>>>>>> e1d7adbe17fe5d378b7629e63d43beecc7762f1a
@trabalhadores_bp.route("/lista")
def lista_trabalhadores():
    # Parâmetros
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    filters = {
        "nome": request.args.get("nome", ""),
        "cpf": request.args.get("cpf", ""),
        "telefone": request.args.get("telefone", ""),
        "email": request.args.get("email", ""),
        "cidade": request.args.get("cidade", "")
    }
    offset = (page - 1) * per_page

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Filtros dinâmicos
    where_clauses = []
    params = []
    for field, value in filters.items():
        if value:
            # Mapeamento do filtro 'nome' para a coluna 'nome_completo' no banco
            column = "nome_completo" if field == "nome" else field
            where_clauses.append(f"t.{column} ILIKE %s")
            params.append(f"%{value}%")
    where_sql = " AND ".join(where_clauses)
    if where_sql:
        where_sql = "WHERE " + where_sql

    # Total de registros
    cursor.execute(f"SELECT COUNT(*) as total FROM trabalhadores t {where_sql}", params)
    total = cursor.fetchone()["total"]

<<<<<<< HEAD
    # Seleção dos IDs dos trabalhadores da página atual
    cursor.execute(f"""
        SELECT t.id FROM trabalhadores t {where_sql}
        ORDER BY t.nome_completo
        LIMIT %s OFFSET %s
    """, params + [per_page, offset])
    
    id_rows = cursor.fetchall()
    if not id_rows:
        rows = []
    else:
        target_ids = [r["id"] for r in id_rows]
        # Seleção completa dos trabalhadores e seus vínculos apenas para os IDs da página
        cursor.execute(f"""
            SELECT
                t.id AS trabalhador_id,
                t.nome_completo,
                t.cpf,
                t.cns,
                t.data_nascimento,
                t.telefone,
                t.email,
                t.cidade,
                t.uf,
                v.id AS vinculo_id,
                v.tipo_vinculo,
                v.numero_funcional,
                v.especialidade,
                v.unidade_lotacao,
                v.data_admissao,
                v.situacao
            FROM trabalhadores t
            LEFT JOIN vinculos_trabalhadores v
                   ON v.trabalhador_id = t.id
            WHERE t.id IN %s
            ORDER BY t.nome_completo
        """, (tuple(target_ids),))
        rows = cursor.fetchall()
=======
    # Seleção com limite e offset
    cursor.execute(f"""
        SELECT
            t.id AS trabalhador_id,
            t.nome_completo,
            t.cpf,
            t.cns,
            t.data_nascimento,
            t.telefone,
            t.email,
            t.cidade,
            t.uf,
            v.id AS vinculo_id,
            v.tipo_vinculo,
            v.numero_funcional,
            v.especialidade,
            v.unidade_lotacao,
            v.data_admissao,
            v.situacao
        FROM trabalhadores t
        LEFT JOIN vinculos_trabalhadores v
               ON v.trabalhador_id = t.id
        {where_sql}
        ORDER BY t.nome_completo
        LIMIT %s OFFSET %s
    """, params + [per_page, offset])

    rows = cursor.fetchall()
>>>>>>> e1d7adbe17fe5d378b7629e63d43beecc7762f1a
    cursor.close()
    conn.close()

    # Agrupa trabalhadores com vínculos
    trabalhadores_map = {}
    for r in rows:
        tid = r["trabalhador_id"]
        if tid not in trabalhadores_map:
            trabalhadores_map[tid] = {
                "id": tid,
                "nome_completo": r["nome_completo"],
                "cpf": r["cpf"],
                "cns": r["cns"],
                "data_nascimento": r["data_nascimento"],
                "telefone": r["telefone"],
                "email": r["email"],
                "cidade": r["cidade"],
                "uf": r["uf"],
                "vinculos": []
            }
        if r["vinculo_id"]:
            trabalhadores_map[tid]["vinculos"].append({
                "id": r["vinculo_id"],
                "tipo_vinculo": r["tipo_vinculo"],
                "numero_funcional": r["numero_funcional"],
                "especialidade": r["especialidade"],
                "unidade_lotacao": r["unidade_lotacao"],
                "data_admissao": r["data_admissao"],
                "situacao": r["situacao"]
            })

    trabalhadores = list(trabalhadores_map.values())
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "lista_trabalhadores.html",
        trabalhadores=trabalhadores,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total=total,
        filters=filters
    )

   

