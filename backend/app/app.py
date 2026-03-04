import sys
import os

# Caminhos absolutos
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Remove o diretório atual do path para evitar conflito (shadowing) onde app.py impede encontrar o pacote app
if sys.path and (sys.path[0] == current_dir or sys.path[0] == ''):
    sys.path.pop(0)

# Adiciona o diretório pai (backend) ao sys.path para permitir importações do tipo 'from app.routes'
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from flask import Flask, render_template, request, redirect, session, flash, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import uuid
from datetime import datetime, timedelta
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash
from app.routes.servidor import servidor_bp
from app.routes.log_agendamento import bp_agendamento
from app.routes.agendar_exame import agendamento_bp
from app.routes.lista_usuario import usuarios_bp
from app.routes.lista_trabalhador import trabalhadores_bp
from app.routes.gerenciamento_agendamento import gerenciamento_bp
from app.routes.gestao_pacientes import gestao_pacientes_bp
from app.routes.ppp import ppp_bp
from app.routes.dashboard import dashboard_bp


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
app.register_blueprint(gestao_pacientes_bp)
app.register_blueprint(ppp_bp)
app.register_blueprint(dashboard_bp)

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
    if request.endpoint in ['static', 'login', 'raiz', 'logout', 'recuperar_senha', 'resetar_senha']:
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
    
    # Cálculo de Tendência (Trabalhadores admitidos nos últimos 30 dias)
    cursor.execute("SELECT COUNT(*) FROM vinculos_trabalhadores WHERE data_admissao >= CURRENT_DATE - interval '30 days'")
    novos_30_dias = cursor.fetchone()[0]
    worker_trend = f"+{((novos_30_dias / total_raw) * 100):.1f}%" if total_raw > 0 else "+0.0%"
    
    # Atendimentos de Hoje
    cursor.execute("SELECT COUNT(*) FROM agendamento_exames WHERE data_consulta = CURRENT_DATE")
    atendimentos_hoje = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()

    return render_template("home.html", 
                         nome=session["nome"], 
                         tipo=session["tipo"], 
                         total_trabalhadores=total_trabalhadores,
                         worker_trend=worker_trend,
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
    if not email:
        return redirect("/index")
        
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    if user:
        # Proteção contra abuso: Verifica se existe um token gerado a menos de 1 minuto (expira em > 14 min)
        minuto_expiracao_recente = datetime.now() + timedelta(minutes=14)
        cursor.execute("SELECT id FROM recuperacao_senha WHERE email = %s AND data_expiracao > %s", 
                       (email, minuto_expiracao_recente))
        recent_token = cursor.fetchone()
        
        if not recent_token:
            # Apaga tokens antigos e não utilizados
            cursor.execute("DELETE FROM recuperacao_senha WHERE email = %s", (email,))
            
            # Gera token seguro de 32 bytes na base64 url-safe
            token = secrets.token_urlsafe(32)
            expiracao = datetime.now() + timedelta(minutes=15)
            
            cursor.execute(
                "INSERT INTO recuperacao_senha (email, token, data_expiracao) VALUES (%s, %s, %s)",
                (email, token, expiracao)
            )
            conn.commit()
            
            # Constrói o link com query string (Exemplo: .../resetar-senha?token=XYZ)
            reset_link = url_for('resetar_senha', _external=True) + f"?token={token}"
            
            try:
                msg = MIMEMultipart()
                msg['From'] = "Agendamento QualiVida <naorespondases@saude.pe.gov.br>"
                msg['To'] = email
                msg['Subject'] = "Recuperação de Senha - QualiVida"
                
                body = f"""Olá,

Você solicitou a recuperação de senha no sistema QualiVida.
Clique no link abaixo para redefinir sua senha:

{reset_link}

Este link é válido por apenas 15 minutos e foi gerado como um token criptograficamente seguro com expiração.
Se você não solicitou a redefinição de sua senha, limpe este e-mail da sua caixa de entrada; nenhuma alteração será processada no seu usuário.

Atenciosamente,
Equipe QualiVida
"""
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                # Envio utilizando as credenciais SMTP repassadas
                server = smtplib.SMTP("antispamout.ati.pe.gov.br", 587)
                server.starttls()
                server.login("dgiis.ses", "$35dG!1s")
                server.sendmail("naorespondases@saude.pe.gov.br", email, msg.as_string())
                server.quit()
            except Exception as e:
                print(f"Erro ao enviar email de recuperação: {e}")

    # Não revelar se o e-mail existe! Sempre retornar mesma mensagem.
    flash("Se o e-mail estiver cadastrado, você receberá um link para redefinir sua senha.", "sucesso")
    
    cursor.close()
    conn.close()
    return redirect("/index")

@app.route("/resetar-senha", methods=["GET", "POST"])
def resetar_senha():
    token = request.args.get("token") or request.form.get("token")
    if not token:
        flash("Token ausente.", "erro")
        return redirect("/index")

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Verifica se o token não expirou (validação rigorosa de 15 minutos)
    cursor.execute(
        "SELECT * FROM recuperacao_senha WHERE token = %s AND data_expiracao > %s",
        (token, datetime.now())
    )
    request_data = cursor.fetchone()
    
    if not request_data:
        flash("Link de recuperação inválido ou expirado.", "erro")
        cursor.close()
        conn.close()
        return redirect("/index")
    
    if request.method == "POST":
        nova_senha = request.form.get("senha")
        confirmar_senha = request.form.get("confirmar_senha")
        
        if not nova_senha or nova_senha != confirmar_senha:
            flash("As senhas não coincidem ou estão vazias.", "erro")
            return render_template("reset_senha.html", token=token)
        
        senha_hash = generate_password_hash(nova_senha)
        
        # Atualiza a senha no banco
        cursor.execute(
            "UPDATE usuarios SET senha = %s WHERE email = %s",
            (senha_hash, request_data["email"])
        )
        
        # Invalida/remove esse token especifico para que não seja mais usado
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
