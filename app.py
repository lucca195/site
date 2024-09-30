from flask import Flask, request, render_template_string, redirect, url_for, session
import mysql.connector
import bcrypt
import mercadopago
import os

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Credenciais do Mercado Pago
MERCADO_PAGO_PUBLIC_KEY = "APP_USR-5027b829-8b4e-47ab-a603-15f4011e50a5"
MERCADO_PAGO_ACCESS_TOKEN = "APP_USR-2957403152017240-091400-a4ac3b9b1025c4dce0447d24868e088e-657641042"

# Configuração da API do Mercado Pago
sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)

# Configurações do banco de dados MySQL
DATABASE_CONFIG = {
    'user': 'root',
    'password': 'braga152',
    'host': 'localhost',
    'database': 'meu_banco',
}

def get_db_connection():
    return mysql.connector.connect(**DATABASE_CONFIG)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(stored_hash, password):
    return bcrypt.checkpw(password.encode(), stored_hash.encode())

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('user_balance'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login ou Cadastro</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f4; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); width: 300px; }
            h1 { text-align: center; margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; }
            input { width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; }
            button { width: 100%; padding: 10px; background-color: #007bff; border: none; color: white; font-size: 16px; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Login</h1>
            <form method="post" action="/login">
                <label for="username">Usuário:</label>
                <input type="text" id="username" name="username" required>
                <label for="password">Senha:</label>
                <input type="password" id="password" name="password" required>
                <button type="submit">Entrar</button>
            </form>
            <h1>Cadastro</h1>
            <form method="post" action="/register">
                <label for="new_username">Usuário:</label>
                <input type="text" id="new_username" name="new_username" required>
                <label for="new_password">Senha:</label>
                <input type="password" id="new_password" name="new_password" required>
                <button type="submit">Cadastrar</button>
            </form>
        </div>
    </body>
    </html>
    ''')

@app.route('/user_balance')
def user_balance():
    # Simulação de dados do usuário
    user_data = {
        'full_name': 'Nome Completo',
        'age': 30,
        'phone': '123456789',
        'balance': 100.00
    }
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Seu Saldo</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f4f4; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); width: 300px; }
            h1 { text-align: center; margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; }
            input { width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; }
            button { width: 100%; padding: 10px; background-color: #007bff; border: none; color: white; font-size: 16px; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Seu Saldo</h1>
            <p><strong>Nome:</strong> {{ user_data['full_name'] }}</p>
            <p><strong>Idade:</strong> {{ user_data['age'] }}</p>
            <p><strong>Telefone:</strong> {{ user_data['phone'] }}</p>
            <p><strong>Saldo:</strong> R$ {{ user_data['balance'] }}</p>
            <form method="post" action="/payment">
                <button type="submit">Realizar Pagamento</button>
            </form>
            <form method="post" action="/withdraw">
                <label for="withdrawal_amount">Valor para saque:</label>
                <input type="number" id="withdrawal_amount" name="withdrawal_amount" step="0.01" min="0" required>
                <button type="submit" name="withdraw">Sacar</button>
            </form>
            <form method="post" action="/logout">
                <button type="submit">Sair</button>
            </form>
        </div>
    </body>
    </html>
    ''', user_data=user_data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)



