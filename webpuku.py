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
    
    # 2. Tabla de productos
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
    
    # Usuario administrador por defecto
    cursor.execute("SELECT * FROM usuarios WHERE username = 'yamil'")
    if not cursor.fetchone():
        hashed_password = generate_password_hash('puku2026')
        cursor.execute(
            "INSERT INTO usuarios (username, password, rol, nombre_completo) VALUES (?, ?, ?, ?)",
            ('yamil', hashed_password, 'admin', 'Yamil Callizaya')
        )
    
    conn.commit()
    conn.close()

# Inicializar DB en Render / Gunicorn al arrancar
with app.app_context():
    init_db()

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def index():
    if 'usuario' in session:
        return redirect(url_for('pos'))
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
            return redirect(url_for('pos'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
            
    return render_template('login.html')

@app.route('/pos')
def pos():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', usuario=session['usuario'], rol=session['rol'], productos=productos)

@app.route('/productos')
def productos():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos")
    productos = cursor.fetchall()
    conn.close()
    
    return render_template('productos.html', productos=productos)

@app.route('/ventas')
def ventas():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ventas ORDER BY fecha DESC")
    ventas = cursor.fetchall()
    conn.close()
    
    return render_template('ventas.html', ventas=ventas)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
