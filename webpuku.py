import sqlite3
import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "puku_secret_key_adahara_2026"
DB_NAME = "database.db"

# --- INICIALIZACIÓN DE LA BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla de Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre_completo TEXT,
            rol TEXT NOT NULL
        )
    ''')
    
    # Tabla de Ventas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT NOT NULL,
            cajero TEXT NOT NULL,
            cliente TEXT NOT NULL,
            tipo_pedido TEXT NOT NULL,
            metodo_pago TEXT NOT NULL,
            detalle TEXT NOT NULL,
            total REAL NOT NULL
        )
    ''')
    
    # Tabla de Stock e Insumos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock (
            item TEXT PRIMARY KEY,
            cantidad INTEGER NOT NULL,
            categoria TEXT NOT NULL
        )
    ''')
    
    # Insertar valores iniciales de stock de cocina si no existen
    cursor.execute("SELECT COUNT(*) FROM stock")
    if cursor.fetchone()[0] == 0:
        items_iniciales = [
            ("Pecho", 10, "cocina"), ("Pierna", 10, "cocina"),
            ("Pecho Brasa", 10, "cocina"), ("Pierna Brasa", 10, "cocina"),
            ("Hamburguesa", 15, "cocina"), ("Salchipapas", 15, "cocina"),
            ("Sodas Pekes", 50, "soda"), ("Sodas Personales", 50, "soda"),
            ("Sodas 2 Litros", 20, "soda")
        ]
        cursor.executemany("INSERT INTO stock VALUES (?, ?, ?)", items_iniciales)

    # Admin Yamil por defecto
    cursor.execute("SELECT * FROM usuarios WHERE username = 'yamil'")
    if not cursor.fetchone():
        pass_admin = generate_password_hash("puku2026")
        cursor.execute(
            "INSERT INTO usuarios (username, password, nombre_completo, rol) VALUES (?, ?, ?, ?)",
            ("yamil", pass_admin, "Yamil Callizaya", "admin")
        )
        
    # Cajero por defecto
    cursor.execute("SELECT * FROM usuarios WHERE username = 'cajero'")
    if not cursor.fetchone():
        pass_cajero = generate_password_hash("cajero123")
        cursor.execute(
            "INSERT INTO usuarios (username, password, nombre_completo, rol) VALUES (?, ?, ?, ?)",
            ("cajero", pass_cajero, "Cajero Turno", "cajero")
        )
        
    conn.commit()
    conn.close()

# --- DECORADORES ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Por favor, inicia sesión para acceder.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("rol") != "admin":
            flash("Acceso restringido solo para el Administrador / Creador.", "danger")
            return redirect(url_for("pos"))
        return f(*args, **kwargs)
    return decorated_function

# --- RUTAS ---
@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("pos"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT password, rol, nombre_completo FROM usuarios WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data[0], password):
            session["user"] = username
            session["rol"] = user_data[1]
            session["nombre"] = user_data[2] or username
            flash(f"¡Bienvenido {session['nombre']}!", "success")
            return redirect(url_for("pos"))
        else:
            flash("Usuario o contraseña incorrectos.", "danger")
            
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("login"))

@app.route("/pos")
@login_required
def pos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT item, cantidad, categoria FROM stock")
    stock_rows = cursor.fetchall()
    conn.close()
    
    stock_dict = {row[0]: row[1] for row in stock_rows}
    return render_template("pos.html", user=session.get("user"), nombre=session.get("nombre"), rol=session.get("rol"), stock=stock_dict)

# API PARA PROCESAR VENTA
@app.route("/api/cobrar", methods=["POST"])
@login_required
def api_cobrar():
    data = request.json
    cliente = data.get("cliente", "Sin Nombre")
    tipo_pedido = data.get("tipo_pedido", "Mesa")
    metodo_pago = data.get("metodo_pago", "Efectivo")
    items = data.get("items", [])
    total = data.get("total", 0.0)
    cajero = session.get("nombre", session.get("user"))
    
    if not items:
        return jsonify({"status": "error", "message": "El carrito está vacío."}), 400
        
    detalle_str = ", ".join([f"{item['nombre']} x{item['cant']} ({item['subtotal']}Bs)" for item in items])
    fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO ventas (fecha_hora, cajero, cliente, tipo_pedido, metodo_pago, detalle, total) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (fecha_hora, cajero, cliente, tipo_pedido, metodo_pago, detalle_str, total)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": f"¡Venta cobrada con éxito! Total: {total} Bs"})

# API PARA MODIFICAR STOCK
@app.route("/api/stock/update", methods=["POST"])
@login_required
def update_stock():
    data = request.json
    item = data.get("item")
    delta = data.get("delta", 0)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT cantidad, categoria FROM stock WHERE item = ?", (item,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"status": "error", "message": "Item no encontrado."}), 404
        
    categoria = row[1]
    
    # RESTRICCIÓN DE ROL: Cajero no puede cambiar Sodas
    if session.get("rol") != "admin" and categoria == "soda":
        conn.close()
        return jsonify({"status": "error", "message": "Solo el Administrador puede modificar el stock de Sodas."}), 403
        
    nueva_cant = max(0, row[0] + delta)
    cursor.execute("UPDATE stock SET cantidad = ? WHERE item = ?", (nueva_cant, item))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "nueva_cantidad": nueva_cant})

# GESTIÓN DE USUARIOS
@app.route("/usuarios", methods=["GET", "POST"])
@login_required
@admin_required
def gestion_usuarios():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    if request.method == "POST":
        nuevo_user = request.form.get("username", "").strip()
        nuevo_pass = request.form.get("password", "").strip()
        nombre_comp = request.form.get("nombre_completo", "").strip()
        nuevo_rol = request.form.get("rol", "cajero")
        
        if nuevo_user and nuevo_pass:
            hash_pass = generate_password_hash(nuevo_pass)
            try:
                cursor.execute(
                    "INSERT INTO usuarios (username, password, nombre_completo, rol) VALUES (?, ?, ?, ?)",
                    (nuevo_user, hash_pass, nombre_comp, nuevo_rol)
                )
                conn.commit()
                flash(f"Usuario '{nuevo_user}' creado exitosamente.", "success")
            except sqlite3.IntegrityError:
                flash(f"El usuario '{nuevo_user}' ya existe.", "danger")
                
    cursor.execute("SELECT id, username, nombre_completo, rol FROM usuarios")
    lista_usuarios = cursor.fetchall()
    conn.close()
    
    return render_template("usuarios.html", usuarios=lista_usuarios)

@app.route("/eliminar_usuario/<int:user_id>")
@login_required
@admin_required
def eliminar_usuario(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ? AND username != ?", (user_id, session.get("user")))
    conn.commit()
    conn.close()
    flash("Usuario actualizado.", "info")
    return redirect(url_for("gestion_usuarios"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)