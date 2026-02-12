from flask import Flask, render_template, request, redirect, session, flash, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import os
import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from routes.servidor import servidor_bp
from routes.log_agendamento import bp_agendamento
from routes.agendar_exame import agendamento_bp
from routes.lista_usuario import usuarios_bp
from routes.lista_trabalhador import trabalhadores_bp
from routes.gerenciamento_agendamento import gerenciamento_bp


# --------------------------
# CONFIGURAÇÃO DOS DIRETÓRIOS DO FRONTEND
# --------------------------
# BASE_DIR no seu caso deve apontar para a raiz do projeto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

TEMPLATE_DIR = os.path.join(BASE_DIR, "front", "src", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "front", "src", "static")


app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR
)

app.register_blueprint(servidor_bp)
app.register_blueprint(bp_agendamento)
app.register_blueprint(agendamento_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(trabalhadores_bp)
app.register_blueprint(gerenciamento_bp)

app.secret_key = "chave_muito_secreta"  # troque depois

# --------------------------
# CONEXÃO COM postgreSQL
# --------------------------
def get_connection():
    return psycopg2.connect(
        host="10.24.59.104",
        user="qualisus",
        password="h5eXAx59gJ3h84Xa",
        database="qualisus"
    )

# --------------------------
# ROTA RAIZ
# --------------------------
@app.route("/")
def raiz():
    return redirect("/index")

# --------------------------
# LOGIN
# --------------------------
# --------------------------
# HOOK: VERIFICAR STATUS DO USUÁRIO
# --------------------------
@app.before_request
def verificar_status_usuario():
    # Rotas que não precisam de verificação (estáticos e o próprio login)
    if request.endpoint in ['static', 'login', 'raiz', 'logout', 'recuperar_senha', 'redefinir_senha_token']:
        return
    
    # Se usuário estiver logado na sessão
    if "user_id" in session:
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT ativo FROM usuarios WHERE id = %s", (session["user_id"],))
            user_status = cur.fetchone()
            cur.close()
            conn.close()
            
            # Se usuário não encontrado ou inativo (ativo=False)
            if not user_status or not user_status[0]:
                session.clear()
                flash("Sua conta foi desativada. Entre em contato com o suporte.", "erro")
                return redirect("/index")
                
        except Exception as e:
            # Em caso de erro de conexão, faz logout por segurança
            print(f"Erro ao verificar status: {e}")
            session.clear()
            return redirect("/index")

@app.route("/index", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            # Check password (supports both sha256 and werkzeug hash)
            stored_hash = user["senha"]
            is_valid = False
            
            if stored_hash and (':' in stored_hash):
                is_valid = check_password_hash(stored_hash, senha)
            else:
                is_valid = hashlib.sha256(senha.encode()).hexdigest() == stored_hash

            if is_valid:
                # Check if user is active
                if not user.get("ativo"):
                    flash("Usuário inativo. Entre em contato com o suporte.", "erro")
                    return render_template("index.html")

                session["user_id"] = user["id"]
                session["nome"] = user["nome"]
                session["tipo"] = user["tipo"]
                session["email"] = user["email"]
                return redirect("/home")

        flash("Email ou senha inválidos!", "erro")

    return render_template("index.html")

# --------------------------
# HOME
# --------------------------
@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect("/index")

    conn = get_connection()
    cursor = conn.cursor()
    
    # Total de Trabalhadores
    cursor.execute("SELECT COUNT(*) FROM trabalhadores")
    total_raw = cursor.fetchone()[0]
    total_trabalhadores = f"{total_raw:,}".replace(",", ".")
    
    # Atendimentos de Hoje
    cursor.execute("SELECT COUNT(*) FROM agendamento_exames WHERE data_consulta = CURRENT_DATE")
    atendimentos_hoje = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()

    return render_template("home.html", 
                         nome=session["nome"], 
                         tipo=session["tipo"], 
                         total_trabalhadores=total_trabalhadores,
                         atendimentos_hoje=atendimentos_hoje)

# --------------------------
# LOGOUT
# --------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/index")

# --------------------------
# RECUPERAR SENHA
# --------------------------
@app.route("/recuperar-senha", methods=["POST"])
def recuperar_senha():
    email = request.form.get("email")
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    if user:
        token = str(uuid.uuid4())
        expiracao = datetime.now() + timedelta(hours=1)
        
        cursor.execute(
            "INSERT INTO recuperacao_senha (email, token, data_expiracao) VALUES (%s, %s, %s)",
            (email, token, expiracao)
        )
        conn.commit()
        
        # Simula o envio de e-mail imprimindo no console
        reset_link = url_for('redefinir_senha_token', token=token, _external=True)
        print(f"\n--- LINK DE RECUPERAÇÃO PARA {email} ---\n{reset_link}\n-----------------------------------\n")
        
        flash("Se o e-mail estiver cadastrado, você receberá um link para redefinir sua senha.", "sucesso")
    else:
        # Por segurança, não confirmamos se o e-mail existe ou não
        flash("Se o e-mail estiver cadastrado, você receberá um link para redefinir sua senha.", "sucesso")
    
    cursor.close()
    conn.close()
    return redirect("/index")

@app.route("/redefinir-senha/<token>", methods=["GET", "POST"])
def redefinir_senha_token(token):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute(
        "SELECT * FROM recuperacao_senha WHERE token = %s AND data_expiracao > %s",
        (token, datetime.now())
    )
    request_data = cursor.fetchone()
    
    if not request_data:
        flash("Link de recuperação inválido ou expirado.", "erro")
        return redirect("/index")
    
    if request.method == "POST":
        nova_senha = request.form.get("senha")
        confirmar_senha = request.form.get("confirmar_senha")
        
        if nova_senha != confirmar_senha:
            flash("As senhas não coincidem.", "erro")
            return render_template("reset_senha.html", token=token)
        
        senha_hash = generate_password_hash(nova_senha)
        
        # Atualiza a senha no banco
        cursor.execute(
            "UPDATE usuarios SET senha = %s WHERE email = %s",
            (senha_hash, request_data["email"])
        )
        
        # Remove o token usado
        cursor.execute("DELETE FROM recuperacao_senha WHERE token = %s", (token,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash("Senha redefinida com sucesso! Agora você pode fazer login.", "sucesso")
        return redirect("/index")
    
    cursor.close()
    conn.close()
    return render_template("reset_senha.html", token=token)

# --------------------------
# RUN
@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    if "user_id" not in session:
        return redirect("/index")
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    if request.method == "POST":
        novo_nome = request.form.get("nome")
        nova_senha = request.form.get("senha")
        
        try:
            if novo_nome:
                cursor.execute("UPDATE usuarios SET nome = %s WHERE id = %s", (novo_nome, session["user_id"]))
                session["nome"] = novo_nome
                
            if nova_senha:
                senha_hash = generate_password_hash(nova_senha)
                cursor.execute("UPDATE usuarios SET senha = %s WHERE id = %s", (senha_hash, session["user_id"]))
                
            conn.commit()
            flash("Perfil atualizado com sucesso!", "sucesso")
        except Exception as e:
            conn.rollback()
            flash(f"Erro ao atualizar perfil: {str(e)}", "erro")
        
        return redirect("/perfil")

    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template("perfil.html", user=user)

# --------------------------
if __name__ == "__main__":
    app.run(debug=True)
