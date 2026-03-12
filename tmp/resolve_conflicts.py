import os
import re

def resolve_conflict(file_path):
    print(f"Resolving: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # regex to find <<<<<<< HEAD ... ======= ... >>>>>>> marker
    # This will keep ONLY the HEAD part
    # We use re.DOTALL to match across multiple lines
    pattern = re.compile(r'<<<<<<< HEAD\n(.*?)\n?=======\n.*?\n?>>>>>>> [a-z0-9]+', re.DOTALL)
    
    new_content = pattern.sub(r'\1', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

files = [
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\README.md",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\front\src\templates\agendar_exame.html",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\front\src\templates\base.html",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\front\src\templates\cadastro_paciente.html",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\front\src\templates\cadastro_usuario.html",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\front\src\templates\gerenciamento_agendamento.html",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\front\src\templates\home.html",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\front\src\templates\atendimento_clinico.html",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\front\src\templates\index.html",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\front\src\templates\lista_funcionarios.html",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\front\src\templates\lista_trabalhadores.html",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\front\src\templates\lista_usuarios.html",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\front\src\templates\includes\sidebar.html",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\front\src\templates\log_agendamento.html",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\front\src\templates\includes\header.html",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\front\src\templates\perfil.html",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\backend\app\routes\agendar_exame.py",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\backend\app\routes\gerenciamento_agendamento.py",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\backend\app\routes\lista_trabalhador.py",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\backend\app\routes\lista_usuario.py",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\backend\app\routes\log_agendamento.py",
    r"c:\Users\williams.sobrinho\qualiSUS---PROD\backend\app\routes\servidor.py"
]

for f in files:
    try:
        resolve_conflict(f)
    except Exception as e:
        print(f"Error resolving {f}: {e}")
