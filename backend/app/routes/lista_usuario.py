# backend/app/usuarios.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.errors import UniqueViolation
usuarios_bp = Blueprint('usuarios', __name__)
from werkzeug.security import generate_password_hash


# --- Função de conexão com o banco ---
def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )
# ================= LISTA DE USUÁRIOS =================
@usuarios_bp.route('/usuarios')
def lista_usuarios():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id, nome, email, tipo, cpf, num_func_vinculo, ativo FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("lista_usuarios.html", usuarios=usuarios)

# ================= CADASTRO =================

@usuarios_bp.route('/usuarios/cadastro', methods=['GET', 'POST'])
def cadastro_usuario():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        tipo = request.form.get('tipo')
        cpf = request.form.get('cpf')
        num_func_vinculo = request.form.get('num_func_vinculo')
        senha = request.form.get('senha')

        if not all([nome, email, tipo, senha]):
            flash("Preencha todos os campos obrigatórios!", "error")
            return redirect(url_for('usuarios.cadastro_usuario'))

        senha_hash = generate_password_hash(senha)

        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Check for duplicates (CPF)
            if cpf:
                cursor.execute("SELECT id FROM usuarios WHERE cpf = %s", (cpf,))
                if cursor.fetchone():
                    flash("CPF já cadastrado!", "error")
                    return redirect(url_for('usuarios.cadastro_usuario'))

            # Check for duplicates (Matrícula)
            if num_func_vinculo:
                cursor.execute("SELECT id FROM usuarios WHERE num_func_vinculo = %s", (num_func_vinculo,))
                if cursor.fetchone():
                    flash("Número de vínculo já cadastrado!", "error")
                    return redirect(url_for('usuarios.cadastro_usuario'))

            cursor.execute("""
                INSERT INTO usuarios (nome, email, tipo, cpf, num_func_vinculo, senha)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (nome, email, tipo, cpf, num_func_vinculo, senha_hash))
            conn.commit()
            flash("Usuário cadastrado com sucesso!", "success")

        except UniqueViolation:
            conn.rollback()
            flash("CPF ou Número de vínculo já cadastrado!", "error")

        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('usuarios.lista_usuarios'))

    return render_template("cadastro_usuario.html")


# ================= EDITAR =================
@usuarios_bp.route('/usuarios/editar/<int:id>', methods=['POST'])
def editar_usuario(id):
    # Security check: only devs or admins can edit (optional, but good)
    if session.get('tipo', '').upper() not in ['DESENVOLVEDOR', 'DEV', 'ADMIN']:
        flash("Permissão insuficiente para editar usuários.", "error")
        return redirect(url_for('usuarios.lista_usuarios'))

    nome = request.form.get('nome')
    email = request.form.get('email')
    tipo = request.form.get('tipo', '').upper() # Match DB expected uppercase
    cpf = request.form.get('cpf')
    num_func_vinculo = request.form.get('num_func_vinculo')
    ativo = request.form.get('ativo') == 'on'
    nova_senha = request.form.get('senha')

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Check for duplicates (CPF)
        if cpf:
            cursor.execute("SELECT id FROM usuarios WHERE cpf = %s AND id != %s", (cpf, id))
            if cursor.fetchone():
                flash(f"O CPF {cpf} já está cadastrado para outro usuário!", "error")
                return redirect(url_for('usuarios.lista_usuarios'))

        # Check for duplicates (Matrícula)
        if num_func_vinculo:
            cursor.execute("SELECT id FROM usuarios WHERE num_func_vinculo = %s AND id != %s", (num_func_vinculo, id))
            if cursor.fetchone():
                flash(f"A matrícula {num_func_vinculo} já está em uso!", "error")
                return redirect(url_for('usuarios.lista_usuarios'))

        if nova_senha and nova_senha.strip():
            senha_hash = generate_password_hash(nova_senha)
            cursor.execute("""
                UPDATE usuarios
                SET nome=%s, email=%s, tipo=%s, cpf=%s, num_func_vinculo=%s, ativo=%s, senha=%s
                WHERE id=%s
            """, (nome, email, tipo, cpf, num_func_vinculo, ativo, senha_hash, id))
        else:
            cursor.execute("""
                UPDATE usuarios
                SET nome=%s, email=%s, tipo=%s, cpf=%s, num_func_vinculo=%s, ativo=%s
                WHERE id=%s
            """, (nome, email, tipo, cpf, num_func_vinculo, ativo, id))

        conn.commit()
        flash(f"Usuário {nome} atualizado com sucesso!", "success")

    except Exception as e:
        conn.rollback()
        print(f"Error editing user: {e}")
        flash("Erro ao processar atualização. Verifique os dados.", "error")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('usuarios.lista_usuarios'))
@usuarios_bp.route('/usuarios/status/<int:id>', methods=['POST'])
def alterar_status_usuario(id):
    data = request.get_json()
    novo_status = data.get('status')
    
    # Converte 'ativo' em True e 'inativo' em False
    ativo = (novo_status == 'ativo')
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET ativo = %s WHERE id = %s", (ativo, id))
    conn.commit()
    cursor.close()
    conn.close()
    return {"success": True}

# ================= EXCLUIR =================
@usuarios_bp.route('/usuarios/excluir/<int:id>')
def excluir_usuario(id):
    # Trava de Segurança: Apenas desenvolvedores podem excluir
    user_tipo = str(session.get("tipo", "")).upper()
    if user_tipo not in ["DESENVOLVEDOR", "DEV"]:
        flash("Acesso negado: Apenas desenvolvedores podem excluir usuários.", "error")
        return redirect(url_for('usuarios.lista_usuarios'))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Usuário excluído com sucesso!", "success")
    return redirect(url_for('usuarios.lista_usuarios'))
