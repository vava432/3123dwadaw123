from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_cors import CORS
import sqlite3
import hashlib
import os
import html
from datetime import datetime
import ssl
import logging
import re
import secrets
import string
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Настройка загрузки файлов
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'*'}  # Разрешаем все файлы
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/chat.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_room_link(length=16):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_salt():
    return os.urandom(16).hex()

def hash_password(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

def verify_password(stored_password, provided_password, salt):
    return stored_password == hash_password(provided_password, salt)

def validate_username(username):
    if not username or len(username) < 3 or len(username) > 20:
        return False
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False
    return True

def validate_password(password):
    if len(password) < 6:
        return False
    return True

def sanitize_input(input_string, max_length=500):
    if not input_string:
        return ""
    input_string = input_string[:max_length]
    return html.escape(input_string.strip())

def sanitize_message(message, max_length=1000):
    if not message:
        return ""
    message = message[:max_length]
    message = html.escape(message)
    message = message.replace('\n', '<br>')
    return message

def get_file_icon(filename):
    extension = filename.lower().split('.')[-1] if '.' in filename else ''
    icons = {
    # Документы и текстовые файлы
    'pdf': '📕', 'doc': '📄', 'docx': '📄', 'txt': '📝', 'rtf': '📄',
    'odt': '📄', 'pages': '📄', 'tex': '📝', 'md': '📝', 'log': '📋',
    
    # Электронные таблицы и базы данных
    'xls': '📊', 'xlsx': '📊', 'csv': '📊', 'ods': '📊', 'numbers': '📊',
    'db': '🗄️', 'sql': '🗄️', 'mdb': '🗄️', 'accdb': '🗄️', 'dbf': '🗄️',
    
    # Презентации
    'ppt': '📽️', 'pptx': '📽️', 'odp': '📽️', 'key': '📽️',
    
    # Архивы
    'zip': '📦', 'rar': '📦', '7z': '📦', 'tar': '📦', 'gz': '📦',
    'bz2': '📦', 'iso': '💿', 'dmg': '💿', 'pkg': '📦',
    
    # Изображения
    'jpg': '🖼', 'jpeg': '🖼', 'png': '🖼', 'gif': '🖼', 'bmp': '🖼',
    'svg': '🖼', 'ico': '🖼', 'webp': '🖼', 'tiff': '🖼', 'tif': '🖼',
    'psd': '🎨', 'ai': '🎨', 'sketch': '🎨', 'xd': '🎨', 'fig': '🎨',
    'eps': '🎨', 'raw': '📸', 'cr2': '📸', 'nef': '📸', 'arw': '📸',
    
    # Аудио файлы
    'mp3': '🎵', 'wav': '🎵', 'flac': '🎵', 'ogg': '🎵', 'aac': '🎵',
    'm4a': '🎵', 'wma': '🎵', 'aiff': '🎵', 'mid': '🎵', 'midi': '🎵',
    'opus': '🎵', 'amr': '🎵',
    
    # Видео файлы
    'mp4': '🎬', 'avi': '🎬', 'mov': '🎬', 'mkv': '🎬', 'wmv': '🎬',
    'flv': '🎬', 'webm': '🎬', 'm4v': '🎬', '3gp': '🎬', 'vob': '🎬',
    'mpeg': '🎬', 'mpg': '🎬', 'ts': '🎬', 'm2ts': '🎬', 'rmvb': '🎬',
    
    # Исполняемые файлы и приложения
    'exe': '⚙️', 'msi': '⚙️', 'apk': '📱', 'app': '🍎', 'deb': '🐧',
    'rpm': '🐧', 'bat': '🖥️', 'sh': '🐚', 'cmd': '🖥️', 'ps1': '🔧',
    'jar': '☕', 'dll': '🔧', 'so': '🔧',
    
    # Программирование и веб
    'py': '🐍', 'js': '📜', 'html': '🌐', 'css': '🎨', 'php': '🐘',
    'java': '☕', 'cpp': '⚙️', 'c': '⚙️', 'h': '⚙️', 'cs': '🔷',
    'rb': '💎', 'go': '🐹', 'rs': '🦀', 'swift': '🐦', 'kt': '🟪',
    'ts': '📘', 'jsx': '⚛️', 'tsx': '⚛️', 'vue': '💚', 'json': '📋',
    'xml': '📋', 'yml': '📋', 'yaml': '📋', 'toml': '📋', 'ini': '⚙️',
    'cfg': '⚙️', 'conf': '⚙️',
    
    # Системные файлы
    'sys': '🔧', 'bin': '🔧', 'bak': '💾', 'tmp': '📄', 'temp': '📄',
    'log': '📋', 'dmp': '🐛', 'lock': '🔒',
    
    # Файлы настроек и данных
    'ini': '⚙️', 'cfg': '⚙️', 'config': '⚙️', 'properties': '⚙️',
    'env': '🌐', 'gitignore': '🔒', 'dockerfile': '🐳', 'makefile': '🔧',
    
    # Файлы шрифтов
    'ttf': '🔤', 'otf': '🔤', 'woff': '🔤', 'woff2': '🔤', 'fon': '🔤',
    
    # Виртуальные машины и образы
    'vmdk': '💻', 'ova': '💻', 'ovf': '💻', 'vdi': '💻', 'vhdx': '💻',
    
    # Резервные копии и дампы
    'bak': '💾', 'backup': '💾', 'bkp': '💾', 'dump': '💾', 'tar.gz': '📦',
    
    # Другие распространенные форматы
    'torrent': '🔽', 'url': '🔗', 'webloc': '🔗', 'lnk': '🔗',
    'ics': '📅', 'vcf': '👤', 'epub': '📚', 'mobi': '📚', 'azw': '📚',
    
    # Файлы проектов
    'sln': '🏗️', 'proj': '🏗️', 'xcodeproj': '🏗️', 'xcworkspace': '🏗️',
    'pkgproj': '🏗️', 'mk': '🔧'
}
    return icons.get(extension, '📎')

def format_file_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names)-1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

# Регистрируем функции для использования в шаблонах
app.jinja_env.globals.update(get_file_icon=get_file_icon)
app.jinja_env.globals.update(format_file_size=format_file_size)

def init_db():
    conn = sqlite3.connect('admin/chat_app.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            link TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_link TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_link) REFERENCES rooms (link),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Таблица для файлов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_link TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_type TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_link) REFERENCES rooms (link),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_room_link ON messages(room_link)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rooms_link ON rooms(link)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_room_link ON files(room_link)')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('admin/chat_app.db')
    conn.row_factory = sqlite3.Row
    return conn

def safe_execute(conn, query, params=()):
    try:
        return conn.execute(query, params)
    except sqlite3.Error as e:
        logger.error(f"SQL error: {e}")
        raise

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/info')
def info():
    return render_template('info.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')
        
        if not validate_username(username):
            return render_template('register.html', error='Имя пользователя должно содержать от 3 до 20 символов')
        
        if not validate_password(password):
            return render_template('register.html', error='Пароль должен содержать минимум 6 символов')
        
        salt = generate_salt()
        hashed_password = hash_password(password, salt)
        
        conn = get_db_connection()
        try:
            cursor = safe_execute(conn, 'INSERT INTO users (username, password, salt) VALUES (?, ?, ?)',
                         (username, hashed_password, salt))
            
            # Получаем ID только что созданного пользователя
            user_id = cursor.lastrowid
            
            conn.commit()
            
            # Автоматически логиним пользователя после регистрации
            session['user_id'] = user_id
            session['username'] = username
            session.permanent = True
            
            conn.close()
            
            # Перенаправляем на главную страницу вместо страницы логина
            return redirect(url_for('dashboard'))
            
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error='Имя пользователя уже занято')
        except Exception as e:
            conn.close()
            logger.error(f"Registration error: {e}")
            return render_template('register.html', error='Ошибка при регистрации')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')
        
        if not username or not password:
            return render_template('login.html', error='Все поля обязательны для заполнения')
        
        conn = get_db_connection()
        try:
            user = safe_execute(conn, 'SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            if user and verify_password(user['password'], password, user['salt']):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session.permanent = True
                conn.close()
                return redirect(url_for('dashboard'))
            else:
                conn.close()
                return render_template('login.html', error='Неверное имя пользователя или пароль')
        except Exception as e:
            conn.close()
            logger.error(f"Login error: {e}")
            return render_template('login.html', error='Ошибка сервера')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    try:
        rooms = safe_execute(conn, 'SELECT * FROM rooms').fetchall()
        conn.close()
        return render_template('dashboard.html', username=session['username'], rooms=rooms)
    except Exception as e:
        conn.close()
        logger.error(f"Dashboard error: {e}")
        return render_template('error.html', error='Ошибка загрузки данных')

@app.route('/create_room', methods=['GET', 'POST'])
def create_room():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        room_name = sanitize_input(request.form.get('room_name', ''))
        room_password = request.form.get('room_password', '')
        
        if not room_name or len(room_name) < 3 or len(room_name) > 30:
            return render_template('create_room.html', error='Название комнаты должно содержать от 3 до 30 символов')
        
        if not validate_password(room_password):
            return render_template('create_room.html', error='Пароль должен содержать минимум 6 символов')
        
        room_link = generate_room_link()
        salt = generate_salt()
        hashed_password = hash_password(room_password, salt)
        
        conn = get_db_connection()
        try:
            while True:
                existing_room = safe_execute(conn, 'SELECT * FROM rooms WHERE link = ?', (room_link,)).fetchone()
                if not existing_room:
                    break
                room_link = generate_room_link()
            
            safe_execute(conn, 'INSERT INTO rooms (link, name, password, salt, created_by) VALUES (?, ?, ?, ?, ?)',
                         (room_link, room_name, hashed_password, salt, session['user_id']))
            conn.commit()
            conn.close()
            
            session['created_room_link'] = room_link
            return redirect(url_for('room_created'))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('create_room.html', error='Комната с таким именем уже существует')
        except Exception as e:
            conn.close()
            logger.error(f"Create room error: {e}")
            return render_template('create_room.html', error='Ошибка при создании комнаты')
    
    return render_template('create_room.html')

@app.route('/room_created')
def room_created():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    room_link = session.get('created_room_link')
    if not room_link:
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    room = safe_execute(conn, 'SELECT * FROM rooms WHERE link = ?', (room_link,)).fetchone()
    conn.close()
    
    if not room:
        return redirect(url_for('dashboard'))
    
    return render_template('room_created.html', room=room)

@app.route('/join_room', methods=['POST'])
def join_room():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    room_link = sanitize_input(request.form.get('room_link', ''))
    room_password = request.form.get('room_password', '')
    
    if not room_link or not room_password:
        return render_template('dashboard.html', error='Все поля обязательны для заполнения')
    
    if len(room_link) != 16 or not re.match(r'^[a-zA-Z0-9]+$', room_link):
        return render_template('dashboard.html', error='Неверный формат ссылки')
    
    conn = get_db_connection()
    try:
        room = safe_execute(conn, 'SELECT * FROM rooms WHERE link = ?', (room_link,)).fetchone()
        
        if room and verify_password(room['password'], room_password, room['salt']):
            if 'visited_rooms' not in session:
                session['visited_rooms'] = []
            if room_link not in session['visited_rooms']:
                session['visited_rooms'].append(room_link)
                session.modified = True
            
            conn.close()
            return redirect(url_for('chat_room', room_link=room_link))
        else:
            conn.close()
            return render_template('dashboard.html', error='Неверная ссылка комнаты или пароль')
    except Exception as e:
        conn.close()
        logger.error(f"Join room error: {e}")
        return render_template('dashboard.html', error='Ошибка подключения к комнате')

@app.route('/room/<room_link>')
def chat_room(room_link):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if len(room_link) != 16 or not re.match(r'^[a-zA-Z0-9]+$', room_link):
        return redirect(url_for('dashboard'))
    
    conn = get_db_connection()
    try:
        room = safe_execute(conn, 'SELECT * FROM rooms WHERE link = ?', (room_link,)).fetchone()
        
        if not room:
            conn.close()
            return redirect(url_for('dashboard'))
        
        messages = safe_execute(conn, '''
            SELECT messages.*, users.username 
            FROM messages 
            JOIN users ON messages.user_id = users.id 
            WHERE room_link = ? 
            ORDER BY timestamp ASC
        ''', (room_link,)).fetchall()
        
        files = safe_execute(conn, '''
            SELECT files.*, users.username 
            FROM files 
            JOIN users ON files.user_id = users.id 
            WHERE room_link = ? 
            ORDER BY upload_date DESC
        ''', (room_link,)).fetchall()
        
        conn.close()
        
        last_message_id = messages[-1]['id'] if messages else 0
        
        if 'visited_rooms' not in session:
            session['visited_rooms'] = []
        if room_link not in session['visited_rooms']:
            session['visited_rooms'].append(room_link)
            session.modified = True
        
        return render_template('room.html', room=room, messages=messages, files=files, last_message_id=last_message_id)
    except Exception as e:
        conn.close()
        logger.error(f"Chat room error: {e}")
        return render_template('error.html', error='Ошибка загрузки комнаты')

@app.route('/send_message', methods=['POST'])
def send_message_api():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated', 'success': False}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data', 'success': False}), 400
            
        room_link = sanitize_input(data.get('room_link', ''))
        message = data.get('message', '').strip()
        
        if not room_link or len(room_link) != 16 or not re.match(r'^[a-zA-Z0-9]+$', room_link):
            return jsonify({'error': 'Invalid room link', 'success': False}), 400
        
        if not message:
            return jsonify({'error': 'Message cannot be empty', 'success': False}), 400
        
        sanitized_message = sanitize_message(message)
        
        conn = get_db_connection()
        try:
            room = safe_execute(conn, 'SELECT * FROM rooms WHERE link = ?', (room_link,)).fetchone()
            if not room:
                conn.close()
                return jsonify({'error': 'Room not found', 'success': False}), 404
            
            safe_execute(conn, 'INSERT INTO messages (room_link, user_id, message) VALUES (?, ?, ?)',
                         (room_link, session['user_id'], sanitized_message))
            conn.commit()
            conn.close()
            
            logger.info(f"User {session['username']} sent message to room {room_link}")
            return jsonify({'success': True})
        except Exception as e:
            conn.close()
            logger.error(f"Send message error: {e}")
            return jsonify({'error': 'Database error', 'success': False}), 500
            
    except Exception as e:
        logger.error(f"Send message API error: {e}")
        return jsonify({'error': 'Server error', 'success': False}), 500

@app.route('/get_messages/<room_link>')
def get_messages_api(room_link):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        last_id = request.args.get('last_id', 0, type=int)
        
        if len(room_link) != 16 or not re.match(r'^[a-zA-Z0-9]+$', room_link) or last_id < 0:
            return jsonify({'error': 'Invalid parameters', 'success': False}), 400
        
        conn = get_db_connection()
        try:
            room = safe_execute(conn, 'SELECT * FROM rooms WHERE link = ?', (room_link,)).fetchone()
            if not room:
                conn.close()
                return jsonify({'error': 'Room not found', 'success': False}), 404
            
            messages = safe_execute(conn, '''
                SELECT messages.*, users.username 
                FROM messages 
                JOIN users ON messages.user_id = users.id 
                WHERE room_link = ? AND messages.id > ? 
                ORDER BY timestamp ASC
            ''', (room_link, last_id)).fetchall()
            
            conn.close()
            
            messages_list = []
            for msg in messages:
                messages_list.append({
                    'id': msg['id'],
                    'username': sanitize_input(msg['username']),
                    'message': msg['message'],
                    'timestamp': msg['timestamp']
                })
            
            return jsonify({'messages': messages_list, 'success': True})
        except Exception as e:
            conn.close()
            logger.error(f"Get messages error: {e}")
            return jsonify({'error': 'Database error', 'success': False}), 500
            
    except Exception as e:
        logger.error(f"Get messages API error: {e}")
        return jsonify({'error': 'Server error', 'success': False}), 500

# Новые маршруты для работы с файлами
@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated', 'success': False}), 401
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part', 'success': False}), 400
        
        file = request.files['file']
        room_link = request.form.get('room_link', '')
        
        if file.filename == '':
            return jsonify({'error': 'No selected file', 'success': False}), 400
        
        if not room_link or len(room_link) != 16 or not re.match(r'^[a-zA-Z0-9]+$', room_link):
            return jsonify({'error': 'Invalid room link', 'success': False}), 400
        
        conn = get_db_connection()
        room = safe_execute(conn, 'SELECT * FROM rooms WHERE link = ?', (room_link,)).fetchone()
        if not room:
            conn.close()
            return jsonify({'error': 'Room not found', 'success': False}), 404
        
        # Генерируем уникальное имя файла
        filename = str(uuid.uuid4())
        original_filename = secure_filename(file.filename)
        file_extension = os.path.splitext(original_filename)[1]
        filename += file_extension
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Сохраняем файл
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # Сохраняем информацию о файле в БД
        safe_execute(conn, '''
            INSERT INTO files (room_link, user_id, filename, original_filename, file_path, file_size, file_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (room_link, session['user_id'], filename, original_filename, file_path, file_size, file_extension))
        
        conn.commit()
        conn.close()
        
        logger.info(f"User {session['username']} uploaded file {original_filename} to room {room_link}")
        return jsonify({'success': True, 'message': 'File uploaded successfully'})
        
    except Exception as e:
        conn.close()
        logger.error(f"File upload error: {e}")
        return jsonify({'error': 'File upload failed', 'success': False}), 500

@app.route('/download_file/<int:file_id>')
def download_file(file_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    try:
        file_record = safe_execute(conn, '''
            SELECT files.*, rooms.link 
            FROM files 
            JOIN rooms ON files.room_link = rooms.link 
            WHERE files.id = ?
        ''', (file_id,)).fetchone()
        
        if not file_record:
            conn.close()
            return jsonify({'error': 'File not found', 'success': False}), 404
        
        # Проверяем доступ к комнате
        if 'visited_rooms' not in session or file_record['link'] not in session['visited_rooms']:
            conn.close()
            return jsonify({'error': 'Access denied', 'success': False}), 403
        
        if not os.path.exists(file_record['file_path']):
            conn.close()
            return jsonify({'error': 'File not found on server', 'success': False}), 404
        
        conn.close()
        return send_file(file_record['file_path'], 
                        as_attachment=True, 
                        download_name=file_record['original_filename'])
        
    except Exception as e:
        conn.close()
        logger.error(f"File download error: {e}")
        return jsonify({'error': 'Download failed', 'success': False}), 500

@app.route('/get_files/<room_link>')
def get_files_api(room_link):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        if len(room_link) != 16 or not re.match(r'^[a-zA-Z0-9]+$', room_link):
            return jsonify({'error': 'Invalid room link', 'success': False}), 400
        
        conn = get_db_connection()
        room = safe_execute(conn, 'SELECT * FROM rooms WHERE link = ?', (room_link,)).fetchone()
        if not room:
            conn.close()
            return jsonify({'error': 'Room not found', 'success': False}), 404
        
        files = safe_execute(conn, '''
            SELECT files.*, users.username 
            FROM files 
            JOIN users ON files.user_id = users.id 
            WHERE room_link = ? 
            ORDER BY upload_date DESC
        ''', (room_link,)).fetchall()
        
        conn.close()
        
        files_list = []
        for file in files:
            files_list.append({
                'id': file['id'],
                'filename': file['filename'],
                'original_filename': file['original_filename'],
                'file_size': file['file_size'],
                'file_type': file['file_type'],
                'upload_date': file['upload_date'],
                'username': file['username'],
                'icon': get_file_icon(file['original_filename']),
                'size_formatted': format_file_size(file['file_size'])
            })
        
        return jsonify({'files': files_list, 'success': True})
    except Exception as e:
        conn.close()
        logger.error(f"Get files error: {e}")
        return jsonify({'error': 'Database error', 'success': False}), 500

@app.route('/delete_file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated', 'success': False}), 401
    
    conn = get_db_connection()
    try:
        file_record = safe_execute(conn, 'SELECT * FROM files WHERE id = ?', (file_id,)).fetchone()
        
        if not file_record:
            conn.close()
            return jsonify({'error': 'File not found', 'success': False}), 404
        
        # Проверяем, что пользователь является владельцем файла или создателем комнаты
        room = safe_execute(conn, 'SELECT * FROM rooms WHERE link = ?', (file_record['room_link'],)).fetchone()
        if file_record['user_id'] != session['user_id'] and room['created_by'] != session['user_id']:
            conn.close()
            return jsonify({'error': 'Permission denied', 'success': False}), 403
        
        # Удаляем файл с диска
        if os.path.exists(file_record['file_path']):
            os.remove(file_record['file_path'])
        
        # Удаляем запись из БД
        safe_execute(conn, 'DELETE FROM files WHERE id = ?', (file_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'File deleted successfully'})
        
    except Exception as e:
        conn.close()
        logger.error(f"File delete error: {e}")
        return jsonify({'error': 'Delete failed', 'success': False}), 500

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Страница не найдена'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server error: {error}")
    return render_template('error.html', error='Внутренняя ошибка сервера'), 500

if __name__ == '__main__':
    os.makedirs('log', exist_ok=True)
    os.makedirs('key', exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    init_db()
    
    cert_path = 'key/cert.pem'
    key_path = 'key/key.pem'
    
    ssl_context = None
    if os.path.exists(cert_path) and os.path.exists(key_path):
        try:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(cert_path, key_path)
            logger.info("SSL certificates loaded successfully")
        except Exception as e:
            logger.error(f"SSL certificate error: {e}")
            ssl_context = None
    else:
        logger.warning("SSL certificates not found. Running without SSL")
    
    app.run(debug=True, host="0.0.0.0", ssl_context=ssl_context, port="443")