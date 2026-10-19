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
    
    # 2. Tabla de productos (con stock y categoría)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER DEFAULT 100,
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
        
    # Usuario cajero de prueba
    cursor.execute("SELECT * FROM usuarios WHERE username = 'cajero'")
    if not cursor.fetchone():
        hashed_password = generate_password_hash('puku2026')
        cursor.execute(
            "INSERT INTO usuarios (username, password, rol, nombre_completo) VALUES (?, ?, ?, ?)",
            ('cajero', hashed_password, 'cajero', 'Cajero PuKú')
        )
        
    # Productos iniciales de prueba si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM productos")
    if cursor.fetchone()[0] == 0:
        productos_iniciales = [
            ('Eco Pierna', 15.00, 50, 'Broaste'),
            ('Eco Contra', 15.00, 50, 'Broaste'),
            ('Eco Pecho', 16.00, 50, 'Broaste'),
            ('Eco Ala', 16.00, 50, 'Broaste'),
            ('1/4 Pecho', 30.00, 40, 'Broaste'),
            ('1/4 Pierna', 30.00, 40, 'Broaste'),
            ('1/2 Pollo', 55.00, 30, 'Broaste'),
            ('1 Pollo', 110.00, 20, 'Broaste')
        ]
        cursor.executemany("INSERT INTO productos (nombre, precio, stock, categoria) VALUES (?, ?, ?, ?)", productos_iniciales)
    
    conn.commit()
    conn.close()

# Inicializar Base de Datos al arrancar
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
    cursor.execute("SELECT id, nombre, precio, stock, categoria FROM productos")
    productos = cursor.fetchall()
    conn.close()
    
    stock_diccionario = {p['nombre']: p['stock'] for p in productos}
    
    return render_template('pos.html', 
                           usuario=session['usuario'], 
                           rol=session.get('rol', 'cajero'), 
                           productos=productos,
                           stock=stock_diccionario)

@app.route('/productos', methods=['GET', 'POST'])
def productos():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST' and session.get('rol') == 'admin':
        nombre = request.form['nombre']
        precio = float(request.form['precio'])
        stock = int(request.form['stock'])
        categoria = request.form['categoria']
        
        cursor.execute("INSERT INTO productos (nombre, precio, stock, categoria) VALUES (?, ?, ?, ?)",
                       (nombre, precio, stock, categoria))
        conn.commit()
        flash('Producto agregado exitosamente', 'success')
        
    cursor.execute("SELECT * FROM productos")
    lista_productos = cursor.fetchall()
    conn.close()
    
    return render_template('productos.html', productos=lista_productos, rol=session.get('rol'))

@app.route('/ventas')
def ventas():
    if 'usuario' not in session or session.get('rol') != 'admin':
        flash('Acceso denegado. Solo administradores.', 'danger')
        return redirect(url_for('pos'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ventas ORDER BY fecha DESC")
    lista_ventas = cursor.fetchall()
    conn.close()
    
    return render_template('ventas.html', ventas=lista_ventas)

@app.route('/usuarios')
def usuarios():
    if 'usuario' not in session or session.get('rol') != 'admin':
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('pos'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, rol, nombre_completo FROM usuarios")
    lista_usuarios = cursor.fetchall()
    conn.close()
    
    return render_template('usuarios.html', usuarios=lista_usuarios)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
