import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import json

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
            usuario TEXT NOT NULL,
            cliente TEXT,
            tipo_pedido TEXT,
            metodo_pago TEXT,
            detalle TEXT
        )
    ''')
    
    # 4. Tabla de stock de sodas por sabor
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_sodas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            sabor TEXT NOT NULL,
            cantidad INTEGER DEFAULT 6
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
        
    # Sabores base de sodas
    sabores_base = [
        "Coca Cola", "Coca Cola Zero", "Sprite", "Fanta Naranja", 
        "Fanta Mandarina", "Fanta Guaraná", "Fanta Papaya", "Fanta Uva", 
        "Acuarius Pera", "Acuarius Pomelo", "Oro", "Inka Kola", 
        "Del Valle Manzana", "Del Valle Guayaba", "Del Valle Naranja"
    ]
    
    cursor.execute("SELECT COUNT(*) FROM stock_sodas")
    if cursor.fetchone()[0] == 0:
        for cat in ["Pekes", "Personales", "2 Litros"]:
            for sab in sabores_base:
                cursor.execute("INSERT INTO stock_sodas (categoria, sabor, cantidad) VALUES (?, ?, ?)", (cat, sab, 6))

    # Productos iniciales de cocina si está vacío
    cursor.execute("SELECT COUNT(*) FROM productos")
    if cursor.fetchone()[0] == 0:
        productos_iniciales = [
            ('Eco Pierna', 15.00, 20, 'Broaste'),
            ('Eco Contra', 15.00, 20, 'Broaste'),
            ('Eco Pecho', 16.00, 20, 'Broaste'),
            ('Eco Ala', 16.00, 20, 'Broaste'),
            ('¼ Pecho Broaste', 30.00, 20, 'Broaste'),
            ('¼ Pierna Broaste', 30.00, 20, 'Broaste'),
            ('½ Pollo Broaste', 55.00, 15, 'Broaste'),
            ('1 Pollo Broaste', 110.00, 10, 'Broaste'),
            ('¼ Pecho Brasa', 30.00, 20, 'Brasa'),
            ('¼ Pierna Brasa', 30.00, 20, 'Brasa'),
            ('½ Pollo Brasa', 55.00, 15, 'Brasa'),
            ('1 Pollo Brasa', 110.00, 10, 'Brasa'),
            ('Hamburguesa Simple', 15.00, 30, 'Especiales'),
            ('Salchipapas', 12.00, 30, 'Especiales'),
            ('Pecho', 20, 20, 'Stock Cocina'),
            ('Pierna', 20, 20, 'Stock Cocina'),
            ('Contra', 20, 20, 'Stock Cocina'),
            ('Ala', 20, 20, 'Stock Cocina')
        ]
        cursor.executemany("INSERT INTO productos (nombre, precio, stock, categoria) VALUES (?, ?, ?, ?)", productos_iniciales)
    
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

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
    
    cursor.execute("SELECT categoria, sabor, cantidad FROM stock_sodas")
    sodas_db = cursor.fetchall()
    conn.close()
    
    stock_diccionario = {p['nombre']: p['stock'] for p in productos}
    
    # Organizar sodas por categoría y sabor para la web
    stock_sodas_dic = {"Pekes": {}, "Personales": {}, "2 Litros": {}}
    for s in sodas_db:
        if s['categoria'] in stock_sodas_dic:
            stock_sodas_dic[s['categoria']][s['sabor']] = s['cantidad']
            
    sabores_lista = list(stock_sodas_dic["Pekes"].keys())

    return render_template('pos.html', 
                           usuario=session['usuario'], 
                           rol=session.get('rol', 'cajero'), 
                           productos=productos,
                           stock=stock_diccionario,
                           stock_sodas=stock_sodas_dic,
                           sabores=sabores_lista)

@app.route('/api/cobrar', methods=['POST'])
def api_cobrar():
    if 'usuario' not in session:
        return jsonify({'status': 'error', 'message': 'No autorizado'}), 401
    
    data = request.get_json()
    if not data or not data.get('items'):
        return jsonify({'status': 'error', 'message': 'Carrito vacío'}), 400
        
    cliente = data.get('cliente', 'Sin Nombre')
    tipo_pedido = data.get('tipo_pedido', 'Para Llevar')
    metodo_pago = data.get('metodo_pago', 'Efectivo')
    items = data.get('items', [])
    total = data.get('total', 0.0)
    usuario = session['usuario']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    detalle_str = ", ".join([f"{item['cant']}x {item['nombre']}" for item in items])
    
    cursor.execute(
        "INSERT INTO ventas (total, usuario, cliente, tipo_pedido, metodo_pago, detalle) VALUES (?, ?, ?, ?, ?, ?)",
        (total, usuario, cliente, tipo_pedido, metodo_pago, detalle_str)
    )
    
    for item in items:
        nombre = item['nombre']
        cant = item['cant']
        # Descontar stock de cocina si aplica
        cursor.execute("UPDATE productos SET stock = stock - ? WHERE nombre = ?", (cant, nombre))
        
        # Si es soda con sabor específico
        if 'categoria_soda' in item and 'sabor_soda' in item:
            cat = item['categoria_soda']
            sabor = item['sabor_soda']
            cursor.execute("UPDATE stock_sodas SET cantidad = cantidad - ? WHERE categoria = ? AND sabor = ?", (cant, cat, sabor))
        
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'message': f'¡Venta cobrada con éxito por {total:.2f} Bs!'})

@app.route('/api/stock/update', methods=['POST'])
def api_stock_update():
    if 'usuario' not in session:
        return jsonify({'status': 'error', 'message': 'No autorizado'}), 401
        
    data = request.get_json()
    item = data.get('item')
    delta = data.get('delta', 0)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT stock FROM productos WHERE nombre = ?", (item,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Item no encontrado'}), 404
        
    nueva_cantidad = row['stock'] + delta
    if nueva_cantidad < 0:
        conn.close()
        return jsonify({'status': 'error', 'message': 'El stock no puede ser menor a 0'}), 400
        
    cursor.execute("UPDATE productos SET stock = ? WHERE nombre = ?", (nueva_cantidad, item))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'nueva_cantidad': nueva_cantidad})

@app.route('/api/soda/update', methods=['POST'])
def api_soda_update():
    if 'usuario' not in session:
        return jsonify({'status': 'error', 'message': 'No autorizado'}), 401
        
    data = request.get_json()
    categoria = data.get('categoria')
    sabor = data.get('sabor')
    delta = data.get('delta', 0)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT cantidad FROM stock_sodas WHERE categoria = ? AND sabor = ?", (categoria, sabor))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Sabor no encontrado'}), 404
        
    nueva_cantidad = row['cantidad'] + delta
    if nueva_cantidad < 0:
        conn.close()
        return jsonify({'status': 'error', 'message': 'El stock no puede ser menor a 0'}), 400
        
    cursor.execute("UPDATE stock_sodas SET cantidad = ? WHERE categoria = ? AND sabor = ?", (nueva_cantidad, categoria, sabor))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'nueva_cantidad': nueva_cantidad})

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
def usuarios_route():
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
