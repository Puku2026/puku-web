import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'puku_secret_key_2026'

DATABASE = 'puku.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL,
            nombre_completo TEXT NOT NULL
        )
    ''')
    
    # 2. Tabla de productos / menú
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            categoria TEXT NOT NULL
        )
    ''')

    # 3. Tabla de ventas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total REAL NOT NULL,
            usuario TEXT NOT NULL
        )
    ''')
    
    # Crear usuario administrador por defecto si no existe
    cursor.execute("SELECT * FROM usuarios WHERE username = 'yamil'")
    if not cursor.fetchone():
        hashed_password = generate_password_hash('puku2026')
        cursor.execute(
            "INSERT INTO usuarios (username, password, rol, nombre_completo) VALUES (?, ?, ?, ?)",
            ('yamil', hashed_password, 'admin', 'Yamil Callizaya')
        )
    
    conn.commit()
    conn.close()

# ESTA LÍNEA ES LA CLAVE: Crea la base de datos y las tablas al arrancar en Render / Gunicorn
with app.app_context():
    init_db()

@app.route('/')
def index():
    if 'usuario' in session:
        return render_template('index.html', usuario=session['usuario'], rol=session['rol'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password, rol, nombre_completo FROM usuarios WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['usuario'] = user['nombre_completo']
            session['rol'] = user['rol']
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
