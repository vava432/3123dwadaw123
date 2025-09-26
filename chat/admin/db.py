from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['DATABASE'] = 'chat_app.db'

# Данные для авторизации
VALID_USERNAME = 'Va_Dar'
VALID_PASSWORD = 'WEPDARqwe'

# Пути к SSL ключам
SSL_CERTIFICATE = 'key/cert.pem'
SSL_PRIVATE_KEY = 'key/privkey.pem'

def get_db_connection():
    """Создает соединение с базой данных"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def check_ssl_files():
    """Проверяет наличие SSL файлов"""
    if not os.path.exists(SSL_CERTIFICATE):
        raise FileNotFoundError(f"SSL certificate not found: {SSL_CERTIFICATE}")
    if not os.path.exists(SSL_PRIVATE_KEY):
        raise FileNotFoundError(f"SSL private key not found: {SSL_PRIVATE_KEY}")
    return True

def check_auth():
    """Проверяет авторизацию пользователя"""
    return session.get('authenticated') == True

@app.route('/')
def index():
    """Главная страница с авторизацией"""
    if check_auth():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница авторизации"""
    if check_auth():
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session['authenticated'] = True
            session['username'] = username
            flash('Успешный вход!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверные учетные данные!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Выход из системы"""
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Панель управления базы данных"""
    if not check_auth():
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/api/tables')
def get_tables():
    """API для получения списка таблиц"""
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        conn.close()
        return jsonify({'tables': tables})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/table/<table_name>')
def get_table_data(table_name):
    """API для получения данных таблицы"""
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        
        # Получаем структуру таблицы
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [{'name': col[1], 'type': col[2]} for col in cursor.fetchall()]
        
        # Получаем данные
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        data = df.to_dict('records')
        
        conn.close()
        
        return jsonify({
            'table_name': table_name,
            'columns': columns,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_database_stats():
    """API для получения статистики базы данных"""
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        tables = ['users', 'rooms', 'messages', 'files']
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        
        # Дополнительная статистика
        cursor.execute("SELECT COUNT(DISTINCT room_link) FROM messages")
        stats['active_rooms'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM messages")
        stats['active_users'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(timestamp) FROM messages")
        stats['last_message'] = cursor.fetchone()[0]
        
        conn.close()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
def execute_query():
    """API для выполнения SQL запросов"""
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is empty'}), 400
        
        # Запрещаем опасные операции
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
        if any(keyword in query.upper() for keyword in dangerous_keywords):
            return jsonify({'error': 'Operation not allowed'}), 403
        
        conn = get_db_connection()
        
        if query.upper().startswith('SELECT'):
            df = pd.read_sql_query(query, conn)
            result = df.to_dict('records')
            conn.close()
            return jsonify({
                'success': True,
                'data': result,
                'count': len(result)
            })
        else:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            conn.close()
            return jsonify({
                'success': True,
                'message': 'Query executed successfully'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        # Проверяем наличие SSL файлов
        check_ssl_files()
        
        # Запускаем с поддержкой HTTPS
        app.run(
            debug=True, 
            host='0.0.0.0', 
            port=5000,
            ssl_context=(SSL_CERTIFICATE, SSL_PRIVATE_KEY)
        )
    except FileNotFoundError as e:
        print(f"SSL error: {e}")
        print("Falling back to HTTP mode")
        # Запускаем без HTTPS если файлы не найдены
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Error: {e}")