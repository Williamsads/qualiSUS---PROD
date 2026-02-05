from flask import Flask, render_template, request, redirect, session, flash

app = Flask(__name__)


@app.route('/cadastro_servidor')
def cadastro_servidor():
    return render_template('cadastro_servidor.html')