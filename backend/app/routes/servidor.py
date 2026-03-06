from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
import psycopg2
from psycopg2.extras import RealDictCursor
from mysql.connector import Error
import pandas as pd
import io

servidor_bp = Blueprint('servidor', __name__)

# ================= CONEXÃO =================
def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

# ================= LISTAR FUNCIONÁRIOS =================
@servidor_bp.route('/funcionarios')
def lista_funcionarios():
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                id,
                nome,
                cpf,
                num_func_num_vinc,
                especialidade,
                unidade_atendimento,
                ativo,
                atendimento,
                situacao,
                situacao_data_inicio,
                situacao_data_fim,
                email,
                telefone
            FROM funcionarios
            ORDER BY nome
        """)
        funcionarios = cursor.fetchall()

        cursor.execute("SELECT nome FROM unidades_saude ORDER BY nome")
        unidades = cursor.fetchall()
        
    except Error:
        flash("Erro ao carregar dados.", "error")
        funcionarios = []
        unidades = []

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    return render_template(
        'lista_funcionarios.html',
        funcionarios=funcionarios,
        unidades=unidades
    )

@servidor_bp.route('/funcionarios/exportar')
def exportar_funcionarios():
    nome = request.args.get('nome', '').strip()
    cpf = request.args.get('cpf', '').strip()
    matricula = request.args.get('matricula', '').strip()
    especialidade = request.args.get('especialidade', '').strip()
    unidade = request.args.get('unidade', '').strip()
    status = request.args.get('status', '').strip()

    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                nome as "Nome",
                cpf as "CPF",
                num_func_num_vinc as "Matrícula",
                especialidade as "Especialidade",
                unidade_atendimento as "Unidade",
                CASE WHEN atendimento THEN 'Sim' ELSE 'Não' END as "Atendimento",
                situacao as "Situação Atual",
                email as "E-mail",
                telefone as "Contato",
                CASE WHEN ativo THEN 'Ativo' ELSE 'Inativo' END as "Status"
            FROM funcionarios
            WHERE 1=1
        """
        params = []

        if nome:
            query += " AND LOWER(nome) LIKE LOWER(%s)"
            params.append(f"%{nome}%")
        if cpf:
            query += " AND cpf LIKE %s"
            params.append(f"%{cpf}%")
        if matricula:
            query += " AND num_func_num_vinc LIKE %s"
            params.append(f"%{matricula}%")
        if especialidade:
            query += " AND LOWER(especialidade) LIKE LOWER(%s)"
            params.append(f"%{especialidade}%")
        if unidade:
            query += " AND LOWER(unidade_atendimento) LIKE LOWER(%s)"
            params.append(f"%{unidade}%")
        if status:
            ativo = True if status == 'ativo' else False
            query += " AND ativo = %s"
            params.append(ativo)

        query += " ORDER BY nome"
        cursor.execute(query, params)
        rows = cursor.fetchall()

        if not rows:
            flash("Nenhum dado para exportar.", "warning")
            return redirect(url_for('servidor.lista_funcionarios'))

        df = pd.DataFrame(rows)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Funcionários')
        
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='lista_funcionarios.xlsx'
        )

    except Exception as e:
        flash(f"Erro ao exportar Excel: {str(e)}", "error")
        return redirect(url_for('servidor.lista_funcionarios'))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ================= CADASTRO =================
@servidor_bp.route('/cadastro_funcionario', methods=['GET', 'POST'])
def adicionar_funcionario():
    if request.method == 'POST':
        nome = request.form.get('nome')
        cpf = request.form.get('cpf')
        num_func_num_vinc = request.form.get('num_func_vinculo')
        data_nascimento = request.form.get('data_nascimento')
        especialidade = request.form.get('especialidade')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        unidade = request.form.get('unidade')
        situacao = request.form.get('situacao', 'Ativo')
        situacao_data_inicio = request.form.get('situacao_data_inicio') or None
        situacao_data_fim = request.form.get('situacao_data_fim') or None
        atendimento = request.form.get('atendimento') == 'on'
        # Normaliza CPF
        if cpf:
            cpf = cpf.replace('.', '').replace('-', '').strip()

        # Validação obrigatória
        if not all([
            nome,
            cpf,
            num_func_num_vinc,
            data_nascimento,
            especialidade,
            email,
            telefone
        ]):
            flash("Preencha todos os campos obrigatórios.", "error")
            return redirect(url_for('servidor.adicionar_funcionario'))

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Check Duplicates (CPF)
            cursor.execute("SELECT id FROM funcionarios WHERE cpf = %s", (cpf,))
            if cursor.fetchone():
                flash("CPF já cadastrado!", "error")
                cursor.close()
                conn.close()
                return redirect(url_for('servidor.adicionar_funcionario'))

            # Check Duplicates (Matrícula)
            cursor.execute("SELECT id FROM funcionarios WHERE num_func_num_vinc = %s", (num_func_num_vinc,))
            if cursor.fetchone():
                flash("Matrícula já cadastrada!", "error")
                cursor.close()
                conn.close()
                return redirect(url_for('servidor.adicionar_funcionario'))

            cursor.execute("""
                INSERT INTO funcionarios (
                    nome,
                    cpf,
                    num_func_num_vinc,
                    data_nascimento,
                    especialidade,
                    email,
                    telefone,
                    unidade_atendimento,
                    ativo,
                    atendimento,
                    situacao,
                    situacao_data_inicio,
                    situacao_data_fim
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                nome,
                cpf,
                num_func_num_vinc,
                data_nascimento,
                especialidade,
                email,
                telefone,
                unidade or None,
                True, # Novo funcionário é ativo por padrão
                atendimento,
                situacao,
                situacao_data_inicio,
                situacao_data_fim
            ))

            conn.commit()
            flash("Funcionário cadastrado com sucesso!", "success")
            return redirect(url_for('servidor.lista_funcionarios'))

        except Error as e:
            flash(f"Erro ao salvar funcionário: {e}. Tente novamente.", "error")
            return redirect(url_for('servidor.adicionar_funcionario'))

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    return render_template('cadastro_funcionario.html')

# ================= EDITAR =================
@servidor_bp.route('/funcionario/editar/<int:id>', methods=['GET', 'POST'])
def editar_funcionario(id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        num_func_vinculo = request.form['num_func_vinculo']
        especialidade = request.form['especialidade']
        unidade_atendimento = request.form['unidade_atendimento']
        situacao = request.form.get('situacao', 'Ativo')
        situacao_data_inicio = request.form.get('situacao_data_inicio') or None
        situacao_data_fim = request.form.get('situacao_data_fim') or None
        atendimento = request.form.get('atendimento') == 'on'
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        # Normaliza CPF
        if cpf:
            cpf = cpf.replace('.', '').replace('-', '').strip()

        sql = """
            UPDATE funcionarios
            SET nome = %s,
                cpf = %s,
                num_func_num_vinc = %s,
                especialidade = %s,
                unidade_atendimento = %s,
                atendimento = %s,
                situacao = %s,
                situacao_data_inicio = %s,
                situacao_data_fim = %s,
                email = %s,
                telefone = %s
            WHERE id = %s
        """

        try:
            # Check Duplicates (CPF)
            cursor.execute("SELECT id FROM funcionarios WHERE cpf = %s AND id != %s", (cpf, id))
            if cursor.fetchone():
                flash("CPF já cadastrado para outro funcionário!", "error")
                cursor.close()
                conn.close()
                return redirect(url_for('servidor.editar_funcionario', id=id))

            # Check Duplicates (Matrícula)
            cursor.execute("SELECT id FROM funcionarios WHERE num_func_num_vinc = %s AND id != %s", (num_func_vinculo, id))
            if cursor.fetchone():
                flash("Matrícula já cadastrada para outro funcionário!", "error")
                cursor.close()
                conn.close()
                return redirect(url_for('servidor.editar_funcionario', id=id))

            cursor.execute(sql, (
                nome,
                cpf,
                num_func_vinculo,
                especialidade,
                unidade_atendimento,
                atendimento,
                situacao,
                situacao_data_inicio,
                situacao_data_fim,
                email,
                telefone,
                id
            ))

            conn.commit()
            flash("Funcionário atualizado com sucesso!", "success")
            return redirect(url_for('servidor.lista_funcionarios'))
        except Error as e:
            conn.rollback()
            flash(f"Erro ao atualizar funcionário: {e}. Tente novamente.", "error")
            return redirect(url_for('servidor.editar_funcionario', id=id))
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    # GET → carregar dados
    cursor.execute("SELECT * FROM funcionarios WHERE id = %s", (id,))
    funcionario = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        'cadastro_funcionario.html',
        funcionario=funcionario
    )

@servidor_bp.route('/funcionario/status/<int:id>', methods=['POST'])
def alterar_status_funcionario(id):
    data = request.get_json()
    status = data.get('status')

    ativo = True if status == 'ativo' else False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE funcionarios
        SET ativo = %s
        WHERE id = %s
    """, (ativo, id))

    conn.commit()
    cursor.close()
    conn.close()

    return {'success': True}




# ================= EXCLUIR =================
@servidor_bp.route('/funcionario/excluir/<int:id>')
def excluir_funcionario(id):
    return f"Excluir funcionário {id}"

# ================= OUTRAS TELAS =================
from flask import request, render_template, redirect, flash
from psycopg2.extras import RealDictCursor

@servidor_bp.route('/cadastro_paciente', methods=['GET', 'POST'])
def cadastro_paciente():
    if request.method == 'POST':
        data = request.form

        trabalhador_id = data.get('trabalhador_id')
        
        # Normalização de dados para evitar estouro de campo
        raw_cpf = data.get('cpf', '')
        cpf = raw_cpf.replace('.', '').replace('-', '').strip() if raw_cpf else ''
        
        raw_tel = data.get('telefone', '')
        telefone = raw_tel.replace('(', '').replace(')', '').replace('-', '').replace(' ', '').strip() if raw_tel else ''
        
        raw_cns = data.get('cns', '')
        cns = raw_cns.replace('.', '').replace('-', '').replace(' ', '').strip() if raw_cns else ''

        raw_cep = data.get('cep', '')
        cep = raw_cep.replace('-', '').replace('.', '').strip() if raw_cep else ''

        try:
            conn = get_connection()
            cur = conn.cursor()

            # --- VALIDAÇÃO DE DUPLICIDADE (CPF) ---
            if cpf:
                if trabalhador_id:
                     cur.execute("SELECT id FROM trabalhadores WHERE cpf = %s AND id != %s", (cpf, trabalhador_id))
                else:
                     cur.execute("SELECT id FROM trabalhadores WHERE cpf = %s", (cpf,))
                
                if cur.fetchone():
                    flash("CPF já cadastrado para outro trabalhador!", "danger")
                    cur.close()
                    conn.close()
                    return redirect('/trabalhadores/lista')

            # --- VALIDAÇÃO DE DUPLICIDADE (MATRÍCULA) ---
            num_func_vinc_list_check = data.getlist('num_func_vinculo[]')
            for nf in num_func_vinc_list_check:
                if nf:
                    if trabalhador_id:
                         # Verifica se existe em QUALQUER outro trabalhador (id diferente)
                         cur.execute("""
                            SELECT t.nome_completo 
                            FROM vinculos_trabalhadores v
                            JOIN trabalhadores t ON v.trabalhador_id = t.id
                            WHERE v.numero_funcional = %s AND v.trabalhador_id != %s
                         """, (nf, trabalhador_id))
                    else:
                         cur.execute("""
                            SELECT t.nome_completo 
                            FROM vinculos_trabalhadores v
                            JOIN trabalhadores t ON v.trabalhador_id = t.id
                            WHERE v.numero_funcional = %s
                         """, (nf,))
                    
                    existing = cur.fetchone()
                    if existing:
                         flash(f"Matrícula {nf} já pertence a {existing[0]}!", "danger")
                         cur.close()
                         conn.close()
                         return redirect('/trabalhadores/lista')

            if trabalhador_id:
                # -------- UPDATE trabalhadores --------
                sql_trabalhador = """
                    UPDATE trabalhadores
                    SET
                        nome_completo = %s,
                        cpf = %s,
                        cns = %s,
                        data_nascimento = %s,
                        telefone = %s,
                        email = %s,
                        cep = %s,
                        logradouro = %s,
                        numero = %s,
                        bairro = %s,
                        cidade = %s,
                        uf = %s
                    WHERE id = %s
                """
                cur.execute(sql_trabalhador, (
                    data.get('nome'),
                    cpf,
                    cns,
                    data.get('data_nascimento'),
                    telefone,
                    data.get('email'),
                    cep,
                    data.get('logradouro'),
                    data.get('numero'),
                    data.get('bairro'),
                    data.get('cidade'),
                    data.get('uf'),
                    trabalhador_id
                ))
            else:
                # -------- INSERT trabalhadores --------
                sql_trabalhador = """
                    INSERT INTO trabalhadores (
                        nome_completo, cpf, cns, data_nascimento, telefone, email,
                        cep, logradouro, numero, bairro, cidade, uf
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                cur.execute(sql_trabalhador, (
                    data.get('nome'),
                    cpf,
                    cns,
                    data.get('data_nascimento'),
                    telefone,
                    data.get('email'),
                    cep,
                    data.get('logradouro'),
                    data.get('numero'),
                    data.get('bairro'),
                    data.get('cidade'),
                    data.get('uf')
                ))
                trabalhador_id = cur.fetchone()[0]

            # -------- ATUALIZAR VÍNCULOS (PROFISSIONAL) --------
            # Para evitar complexidade de Update/Insert individual, limpamos os antigos e inserimos os novos
            cur.execute("DELETE FROM vinculos_trabalhadores WHERE trabalhador_id = %s", (trabalhador_id,))

            num_func_vinc_list = data.getlist('num_func_vinculo[]')
            tipo_vinculo_list = data.getlist('tipo_vinculo[]')
            especialidade_list = data.getlist('especialidade[]')
            lotacao_list = data.getlist('lotacao[]')
            data_admissao_list = data.getlist('data_admissao[]')
            data_desligamento_list = data.getlist('data_desligamento[]')
            situacao_list = data.getlist('situacao[]')

            sql_vinculo = """
                INSERT INTO vinculos_trabalhadores (
                    trabalhador_id, numero_funcional, tipo_vinculo, 
                    especialidade, unidade_lotacao, data_admissao, data_desligamento, situacao
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            for i in range(len(num_func_vinc_list)):
                if num_func_vinc_list[i]: # Só insere se tiver identificação
                    cur.execute(sql_vinculo, (
                        trabalhador_id,
                        num_func_vinc_list[i],
                        tipo_vinculo_list[i],
                        especialidade_list[i],
                        lotacao_list[i],
                        data_admissao_list[i] or None,
                        data_desligamento_list[i] or None,
                        situacao_list[i] or 'Ativo'
                    ))

            conn.commit()
            flash('Cadastro salvo com sucesso!', 'success')

        except Exception as e:
            conn.rollback()
            flash(f'Erro ao atualizar cadastro: {e}', 'danger')

        finally:
            cur.close()
            conn.close()

        return redirect('/trabalhadores/lista')

    # -------- GET (abrir tela) --------
    trabalhador_id = request.args.get('id')
    trabalhador = None

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if trabalhador_id and trabalhador_id.strip():
        # Busca dados base do trabalhador
        cur.execute("SELECT * FROM trabalhadores WHERE id = %s", (trabalhador_id,))
        trabalhador = cur.fetchone()

        if trabalhador:
            # Busca TODOS os vínculos completos do trabalhador
            cur.execute("""
                SELECT * FROM vinculos_trabalhadores 
                WHERE trabalhador_id = %s 
                ORDER BY id ASC
            """, (trabalhador_id,))
            trabalhador['vinculos'] = cur.fetchall()

    # Busca listas para os selects
    cur.execute("SELECT nome FROM unidades_saude ORDER BY nome")
    unidades = cur.fetchall()

    cur.execute("SELECT nome FROM especialidades ORDER BY nome")
    especialidades = cur.fetchall()

    # Tipos de vínculo comuns no banco (EST=Estatutário, CTD=Contratado)
    tipos_vinculo = [
        {'nome': 'EST'}, {'nome': 'CTD'}, {'nome': 'CLT'}, {'nome': 'COM'}, 
        {'nome': 'Servidor'}, {'nome': 'Contratado'}, {'nome': 'Terceirizado'}, {'nome': 'Jovem Aprendiz'}
    ]

    cur.close()
    conn.close()

    return render_template(
        'cadastro_paciente.html',
        trabalhador=trabalhador,
        unidades=unidades,
        especialidades=especialidades,
        tipos_vinculo=tipos_vinculo
    )

