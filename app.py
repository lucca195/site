from flask import Flask, request, render_template_string, redirect, url_for, session
import mysql.connector
import bcrypt
import mercadopago

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

# Credenciais do Mercado Pago
MERCADO_PAGO_PUBLIC_KEY = "APP_USR-5027b829-8b4e-47ab-a603-15f4011e50a5"
MERCADO_PAGO_ACCESS_TOKEN = "APP_USR-2957403152017240-091400-a4ac3b9b1025c4dce0447d24868e088e-657641042"

# Configuração da API do Mercado Pago
sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)

# Configurações do banco de dados MySQL (usando ClearDB no Heroku)
DATABASE_CONFIG = {
    'user': 'bf4f36ce29443b',
    'password': '6b0486f7',
    'host': 'us-cluster-east-01.k8s.cleardb.net',
    'database': 'heroku_c37d1ea8733062b',
    'raise_on_warnings': True,
    'reconnect': True,
}

# Função para obter conexão com o banco de dados
def get_db_connection():
    return mysql.connector.connect(**DATABASE_CONFIG)

# Função para hashear a senha
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Função para verificar se a senha corresponde ao hash
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
        <p>Não tem uma conta? <a href="/register">Cadastre-se</a></p>
    </div>
</body>
</html>
    ''')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        age = request.form['age']
        phone = request.form['phone']
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()

        if user:
            cur.close()
            conn.close()
            return 'Usuário já existe', 400

        hashed_password = hash_password(password)

        cur.execute('''
            INSERT INTO users (username, password_hash, full_name, age, phone, balance)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (username, hashed_password, full_name, age, phone, 0.00))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('index'))

    return render_template_string('''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cadastro</title>
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
        <h1>Cadastro</h1>
        <form method="post" action="/register">
            <label for="full_name">Nome completo:</label>
            <input type="text" id="full_name" name="full_name" required>
            <label for="age">Idade:</label>
            <input type="number" id="age" name="age" required>
            <label for="phone">Telefone:</label>
            <input type="text" id="phone" name="phone" required>
            <label for="username">Usuário:</label>
            <input type="text" id="username" name="username" required>
            <label for="password">Senha:</label>
            <input type="password" id="password" name="password" required>
            <button type="submit">Cadastrar</button>
        </form>
    </div>
</body>
</html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT id, password_hash FROM users WHERE username = %s', (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and check_password(user['password_hash'], password):
        session['user_id'] = user['id']
        return redirect(url_for('user_balance'))
    return 'Usuário ou senha incorretos', 401

@app.route('/user/balance', methods=['GET', 'POST'])
def user_balance():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute('SELECT balance, full_name, age, phone FROM users WHERE id = %s', (user_id,))
    user_data = cur.fetchone()
    cur.close()
    conn.close()

    if request.method == 'POST':
        if 'withdraw' in request.form:
            withdrawal_amount = float(request.form['withdrawal_amount'])
            if withdrawal_amount <= user_data['balance']:
                new_balance = user_data['balance'] - withdrawal_amount
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute('UPDATE users SET balance = %s WHERE id = %s', (new_balance, user_id))
                conn.commit()
                cur.close()
                conn.close()

                preference_data = {
                    'items': [{
                        'title': 'Saque via Pix',
                        'quantity': 1,
                        'unit_price': withdrawal_amount,
                        'currency_id': 'BRL',
                    }],
                    'payment_methods': {
                        'excluded_payment_types': [{'id': 'ticket'}]
                    },
                    'back_urls': {
                        'success': url_for('withdraw_success', _external=True),
                        'failure': url_for('withdraw_failure', _external=True),
                        'pending': url_for('withdraw_pending', _external=True),
                    },
                    'auto_return': 'approved',
                }

                preference_response = sdk.preference().create(preference_data)
                preference_id = preference_response['response']['id']

                return redirect(preference_response['response']['init_point'])

        return 'Erro na transação', 400

    return render_template_string('''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Saldo do Usuário</title>
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
        <h1>Saldo</h1>
        <p>Nome: {{ user_data['full_name'] }}</p>
        <p>Idade: {{ user_data['age'] }}</p>
        <p>Telefone: {{ user_data['phone'] }}</p>
        <p>Saldo atual: R$ {{ user_data['balance'] }}</p>
        <form method="post">
            <label for="withdrawal_amount">Quantia para saque:</label>
            <input type="number" step="0.01" name="withdrawal_amount" id="withdrawal_amount" required>
            <button type="submit" name="withdraw">Sacar</button>
        </form>
    </div>
</body>
</html>
    ''', user_data=user_data)

@app.route('/withdraw/success')
def withdraw_success():
    return 'Saque efetuado com sucesso!'

@app.route('/withdraw/failure')
def withdraw_failure():
    return 'Falha no saque. Tente novamente.'

@app.route('/withdraw/pending')
def withdraw_pending():
    return 'Saque pendente. Aguarde confirmação.'

if __name__ == '__main__':
    app.run(debug=True)
