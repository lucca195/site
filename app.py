
import os
import mysql.connector
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import bcrypt
import mercadopago

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'  # Mantenha essa chave em segredo

# Configuração do Mercado Pago
mp = mercadopago.SDK("SUA_ACCESS_TOKEN_AQUI")

# Função para conectar ao banco de dados
def get_db_connection():
    DATABASE_URL = os.environ.get('CLEARDB_DATABASE_URL')
    
    if not DATABASE_URL:
        raise ValueError("A variável CLEARDB_DATABASE_URL não está configurada.")
    
    # Extrair os componentes da URL do banco de dados
    db_config = mysql.connector.connect(
        host=DATABASE_URL.split('@')[1].split('/')[0],
        user=DATABASE_URL.split('//')[1].split(':')[0],
        password=DATABASE_URL.split(':')[2].split('@')[0],
        database=DATABASE_URL.split('/')[1]
    )
    
    return db_config

# Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):  # Supondo que a senha está na coluna 2
            session['user_id'] = user[0]  # Supondo que o ID do usuário está na coluna 0
            return redirect(url_for('dashboard'))
        else:
            return 'Email ou senha inválidos!'

    return render_template('login.html')

# Rota para registro de novos usuários
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (email, password) VALUES (%s, %s)', (email, hashed_password.decode('utf-8')))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

# Rota do dashboard do usuário
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return 'Bem-vindo ao seu painel!'

# Rota para pagamentos com Mercado Pago
@app.route('/pay', methods=['POST'])
def pay():
    preference_data = {
        "items": [
            {
                "title": "Produto Exemplo",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": 100
            }
        ],
        "back_urls": {
            "success": "https://www.seusite.com/success",
            "failure": "https://www.seusite.com/failure",
            "pending": "https://www.seusite.com/pending"
        },
        "auto_return": "approved",
    }

    preference = mp.preference().create(preference_data)
    return jsonify({'init_point': preference['response']['init_point']})

# Rota para logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
