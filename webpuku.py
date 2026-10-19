import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL,
            nombre_completo TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            precio REAL NOT NULL,
            costo REAL DEFAULT 0.0,
            stock INTEGER DEFAULT 20,
            categoria TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total REAL NOT NULL,
            monto_efectivo REAL DEFAULT 0.0,
            monto_qr REAL DEFAULT 0.0,
            monto_peya REAL DEFAULT 0.0,
            usuario TEXT NOT NULL,
            cliente TEXT,
            tipo_pedido TEXT,
            metodo_pago TEXT,
            nota TEXT,
            detalle TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_sodas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            sabor TEXT NOT NULL,
            cantidad INTEGER DEFAULT 6
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mercado (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insumo TEXT NOT NULL,
            cantidad TEXT NOT NULL,
            costo REAL NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cenas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            costo_u REAL NOT NULL,
            subtotal REAL NOT NULL,
            es_soda INTEGER DEFAULT 0,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS costos_config (
            clave TEXT PRIMARY KEY,
            costo REAL NOT NULL
        )
    ''')

    cursor.execute("SELECT * FROM usuarios WHERE username = 'yamil'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO usuarios (username, password, rol, nombre_completo) VALUES (?, ?, ?, ?)",
            ('yamil', generate_password_hash('puku2026'), 'admin', 'Yamil Callizaya')
        )
        
    cursor.execute("SELECT * FROM usuarios WHERE username = 'cajero'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO usuarios (username, password, rol, nombre_completo) VALUES (?, ?, ?, ?)",
            ('cajero', generate_password_hash('puku2026'), 'cajero', 'Cajero PuKú')
        )
        
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

    costos_sodas_iniciales = [
        ('Pekes (Sodas)', 3.50),
        ('Personal (Sodas)', 4.80),
        ('2 L (Sodas)', 13.00),
        ('Pollo (Presa)', 4.50),
        ('Guarnición', 5.00)
    ]
    for c_clave, c_val in costos_sodas_iniciales:
        cursor.execute("INSERT OR IGNORE INTO costos_config (clave, costo) VALUES (?, ?)", (c_clave, c_val))

    productos_iniciales = [
        ('Eco Pierna', 15.00, 9.50, 20, 'Broaste'),
        ('Eco Contra', 15.00, 9.50, 20, 'Broaste'),
        ('Eco Pecho', 16.00, 9.50, 20, 'Broaste'),
        ('Eco Ala', 16.00, 9.50, 20, 'Broaste'),
        ('¼ Pecho Broaste', 30.00, 14.00, 20, 'Broaste'),
        ('¼ Pierna Broaste', 30.00, 14.00, 20, 'Broaste'),
        ('½ Pollo Broaste', 55.00, 28.00, 15, 'Broaste'),
        ('1 Pollo Broaste', 110.00, 56.00, 10, 'Broaste'),
        ('Eco Pierna Brasa', 15.00, 9.50, 20, 'Brasa'),
        ('Eco Contra Brasa', 15.00, 9.50, 20, 'Brasa'),
        ('Eco Pecho Brasa', 16.00, 9.50, 20, 'Brasa'),
        ('Eco Ala Brasa', 16.00, 9.50, 20, 'Brasa'),
        ('¼ Pecho Brasa', 30.00, 14.00, 20, 'Brasa'),
        ('¼ Pierna Brasa', 30.00, 14.00, 20, 'Brasa'),
        ('½ Pollo Brasa', 55.00, 28.00, 15, 'Brasa'),
        ('1 Pollo Brasa', 110.00, 56.00, 10, 'Brasa'),
        ('Hamburguesa Simple', 17.00, 14.00, 30, 'Especiales'),
        ('Hamburguesa Clásica', 20.00, 14.00, 30, 'Especiales'),
        ('Hamburguesa Doble', 30.00, 18.00, 30, 'Especiales'),
        ('Hamburguesa con Extra Papas', 25.00, 16.00, 30, 'Especiales'),
        ('Salchipapas', 15.00, 10.00, 30, 'Especiales'),
        ('Salchiburguer', 30.00, 17.00, 20, 'Especiales'),
        ('Salchipollo', 25.00, 14.50, 20, 'Especiales'),
        ('Presa Extra', 10.00, 4.50, 50, 'Extras'),
        ('Porcion Papa', 6.00, 2.50, 50, 'Extras'),
        ('Porcion Arroz', 6.00, 2.50, 50, 'Extras'),
        ('Pecho', 0.0, 4.50, 20, 'Stock Cocina'),
        ('Contra', 0.0, 4.50, 20, 'Stock Cocina'),
        ('Pierna', 0.0, 4.50, 20, 'Stock Cocina'),
        ('Ala', 0.0, 4.50, 20, 'Stock Cocina'),
        ('Pecho Brasa', 0.0, 4.50, 20, 'Stock Cocina'),
        ('Contra Brasa', 0.0, 4.50, 20, 'Stock Cocina'),
        ('Pierna Brasa', 0.0, 4.50, 20, 'Stock Cocina'),
        ('Ala Brasa', 0.0, 4.50, 20, 'Stock Cocina'),
        ('Hamburguesas', 0.0, 14.0, 10, 'Stock Cocina'),
        ('Salchipapas', 0.0, 10.0, 10, 'Stock Cocina')
    ]
    
    for p in productos_iniciales:
        cursor.execute("""
            INSERT OR IGNORE INTO productos (nombre, precio, costo, stock, categoria) 
            VALUES (?, ?, ?, ?, ?)
        """, p)
    
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
            session['username'] = username
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
    cursor.execute("SELECT id, nombre, precio, costo, stock, categoria FROM productos")
    productos = cursor.fetchall()
    
    cursor.execute("SELECT categoria, sabor, cantidad FROM stock_sodas")
    sodas_db = cursor.fetchall()

    cursor.execute("SELECT * FROM mercado ORDER BY id DESC")
    mercado_items = cursor.fetchall()

    cursor.execute("SELECT * FROM cenas ORDER BY id DESC")
    cenas_items = cursor.fetchall()

    cursor.execute("SELECT * FROM ventas ORDER BY fecha DESC")
    ventas_list = cursor.fetchall()

    cursor.execute("SELECT * FROM usuarios ORDER BY id DESC")
    usuarios_list = cursor.fetchall()

    cursor.execute("SELECT clave, costo FROM costos_config")
    costos_config_db = dict(cursor.fetchall())

    conn.close()
    
    stock_diccionario = {p['nombre']: p['stock'] for p in productos}
    
    stock_sodas_dic = {"Pekes": {}, "Personales": {}, "2 Litros": {}}
    for s in sodas_db:
        if s['categoria'] in stock_sodas_dic:
            stock_sodas_dic[s['categoria']][s['sabor']] = s['cantidad']
            
    sabores_lista = list(stock_sodas_dic["Pekes"].keys())

    return render_template('pos.html', 
                           usuario=session['usuario'], 
                           username=session.get('username'),
                           rol=session.get('rol', 'cajero'), 
                           productos=productos,
                           stock=stock_diccionario,
                           stock_sodas=stock_sodas_dic,
                           sabores=sabores_lista,
                           mercado=mercado_items,
                           cenas=cenas_items,
                           ventas=ventas_list,
                           usuarios=usuarios_list,
                           costos_config=costos_config_db)

@app.route('/api/producto/add', methods=['POST'])
def api_producto_add():
    if 'usuario' not in session: return jsonify({'status': 'error'}), 401
    data = request.get_json()
    nombre = data.get('nombre')
    precio = float(data.get('precio', 0.0))
    costo = float(data.get('costo', 0.0))
    categoria = data.get('categoria', 'Especiales')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO productos (nombre, precio, costo, categoria) VALUES (?, ?, ?, ?)",
                       (nombre, precio, costo, categoria))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': f'Producto {nombre} agregado y guardado con éxito'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'status': 'error', 'message': 'El producto ya existe'}), 400

@app.route('/api/sabor/add', methods=['POST'])
def api_sabor_add():
    if 'usuario' not in session: return jsonify({'status': 'error'}), 401
    data = request.get_json()
    sabor = data.get('sabor')
    if not sabor: return jsonify({'status': 'error', 'message': 'El sabor no puede estar vacío'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    for cat in ["Pekes", "Personales", "2 Litros"]:
        cursor.execute("INSERT OR IGNORE INTO stock_sodas (categoria, sabor, cantidad) VALUES (?, ?, ?)", (cat, sabor, 6))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': f'Sabor {sabor} agregado con éxito'})

@app.route('/api/cobrar', methods=['POST'])
def api_cobrar():
    if 'usuario' not in session: return jsonify({'status': 'error'}), 401
    data = request.get_json()
    if not data or not data.get('items'): return jsonify({'status': 'error', 'message': 'Carrito vacío'}), 400
        
    cliente = data.get('cliente', 'Sin Nombre')
    tipo_pedido = data.get('tipo_pedido', 'Para Llevar')
    metodo_pago = data.get('metodo_pago', 'Efectivo')
    nota = data.get('nota', '')
    items = data.get('items', [])
    total = data.get('total', 0.0)
    monto_ef = data.get('monto_efectivo', 0.0)
    monto_qr = data.get('monto_qr', 0.0)
    usuario = session['usuario']

    monto_peya = total if metodo_pago == 'PeYa' else 0.0
    if metodo_pago == 'Efectivo': monto_ef = total
    elif metodo_pago == 'QR': monto_qr = total

    conn = get_db_connection()
    cursor = conn.cursor()
    
    detalle_str = ", ".join([f"{item['cant']}x {item['nombre']}" for item in items])
    if nota: detalle_str += f" [OBS: {nota}]"
    
    cursor.execute(
        "INSERT INTO ventas (total, monto_efectivo, monto_qr, monto_peya, usuario, cliente, tipo_pedido, metodo_pago, nota, detalle) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (total, monto_ef, monto_qr, monto_peya, usuario, cliente, tipo_pedido, metodo_pago, nota, detalle_str)
    )
    
    for item in items:
        nombre = item.get('nombre_base', item['nombre'])
        cant = item['cant']
        cursor.execute("UPDATE productos SET stock = stock - ? WHERE nombre = ?", (cant, nombre))
        
        if 'categoria_soda' in item and 'sabor_soda' in item and item['categoria_soda'] and item['sabor_soda']:
            cursor.execute("UPDATE stock_sodas SET cantidad = cantidad - ? WHERE categoria = ? AND sabor = ?", 
                           (cant, item['categoria_soda'], item['sabor_soda']))
        
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': f'¡Venta cobrada con éxito por {total:.2f} Bs!'})

@app.route('/api/mercado/add', methods=['POST'])
def api_mercado_add():
    if 'usuario' not in session: return jsonify({'status': 'error'}), 401
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mercado (insumo, cantidad, costo) VALUES (?, ?, ?)",
                   (data['insumo'], data['cantidad'], float(data['costo'])))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/mercado/delete/<int:item_id>', methods=['DELETE'])
def api_mercado_delete(item_id):
    if 'usuario' not in session: return jsonify({'status': 'error'}), 401
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM mercado WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/cena/add', methods=['POST'])
def api_cena_add():
    if 'usuario' not in session: return jsonify({'status': 'error'}), 401
    data = request.get_json()
    prod = data['producto']
    cant = int(data['cantidad'])
    costo_u = float(data['costo_u'])
    es_soda = 1 if data.get('es_soda') else 0
    subtotal = cant * costo_u
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO cenas (producto, cantidad, costo_u, subtotal, es_soda) VALUES (?, ?, ?, ?, ?)",
                   (prod, cant, costo_u, subtotal, es_soda))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/precios/update', methods=['POST'])
def api_precios_update():
    if 'usuario' not in session or session.get('rol') != 'admin': return jsonify({'status': 'error'}), 401
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    for prod_id, p_val in data.get('precios', {}).items():
        cursor.execute("UPDATE productos SET precio = ? WHERE id = ?", (float(p_val), prod_id))
    for prod_id, c_val in data.get('costos', {}).items():
        cursor.execute("UPDATE productos SET costo = ? WHERE id = ?", (float(c_val), prod_id))
    
    for clave, c_val in data.get('costos_sodas', {}).items():
        cursor.execute("INSERT OR REPLACE INTO costos_config (clave, costo) VALUES (?, ?)", (clave, float(c_val)))

    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/stock/update', methods=['POST'])
def api_stock_update():
    if 'usuario' not in session: return jsonify({'status': 'error'}), 401
    data = request.get_json()
    item = data.get('item')
    delta = data.get('delta', 0)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE productos SET stock = stock + ? WHERE nombre = ?", (delta, item))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/soda/update', methods=['POST'])
def api_soda_update():
    if 'usuario' not in session: 
        return jsonify({'status': 'error', 'message': 'Acceso no autorizado.'}), 403
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE stock_sodas SET cantidad = cantidad + ? WHERE categoria = ? AND sabor = ?", 
                   (data['delta'], data['categoria'], data['sabor']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/usuarios/add', methods=['POST'])
def api_usuarios_add():
    if 'usuario' not in session or session.get('rol') != 'admin': return jsonify({'status': 'error'}), 401
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    nombre = data.get('nombre_completo')
    rol = data.get('rol', 'cajero')

    if not username or not password or not nombre:
        return jsonify({'status': 'error', 'message': 'Faltan datos obligatorios'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO usuarios (username, password, rol, nombre_completo) VALUES (?, ?, ?, ?)",
            (username, generate_password_hash(password), rol, nombre)
        )
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': f'Usuario {username} creado con éxito'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'status': 'error', 'message': 'El nombre de usuario ya existe'}), 400

@app.route('/api/usuarios/delete/<int:user_id>', methods=['DELETE'])
def api_usuarios_delete(user_id):
    if 'usuario' not in session or session.get('rol') != 'admin': return jsonify({'status': 'error'}), 401
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/cierre/ejecutar', methods=['POST'])
def api_cierre_ejecutar():
    if 'usuario' not in session: return jsonify({'status': 'error'}), 401
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ventas")
    cursor.execute("DELETE FROM cenas")
    cursor.execute("DELETE FROM mercado")
    cursor.execute("UPDATE productos SET stock = 20 WHERE categoria = 'Stock Cocina' AND nombre NOT IN ('Hamburguesas', 'Salchipapas')")
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': '¡Jornada cerrada y caja reiniciada! Stock de presas restablecido, stock de hamburguesas, salchipapas y bebidas conservado.'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
