# Flask -> Todas las herramientas para la web
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, session, flash
# Werkzeug -> Para la seguridad en el registro
from werkzeug.security import generate_password_hash, check_password_hash
#Functools -> Creación de decoradores propios
from functools import wraps
#Sqlite -> Base de datos interna
import sqlite3
#Os -> Funciones del sistema operativo
import os
# Time -> Funciones relacionadas con el tiempo
import time
# logging -> Para el registro de errores y eventos
import logging
# Importamos nuestra clase 'cerebro' para utilizarla
from motor_nlp import OrquestadorApp

# Silenciamos el log por defecto de la consola.
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
logging.basicConfig(filename='app_nlp.log', level=logging.INFO, format='%(asctime)s - API - %(message)s', encoding='utf-8')

#Nacimiento del servidor y encriptación de datos
app = Flask(__name__)
app.secret_key = 'una_clave_secreta_muy_dificil_de_adivinar_123' 

#Creación de la carpeta uploads, para guardar los archivos de descarga
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Iniciamos el motor.
analizador = OrquestadorApp()

# Configuración de la BBDD Sqlite de usuarios
def get_db_connection():
    conn = sqlite3.connect('usuarios.db')
    conn.row_factory = sqlite3.Row
    return conn

#Inserción cuando sea necesario de los datos de usuarios y los informes a los que se asocia dicho usuario
def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS informes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nombre_informe TEXT, archivo_final TEXT, archivo_favor TEXT, archivo_contra TEXT, fecha DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES usuarios (id))''')
    conn.commit()
    conn.close()

#Función que impide el acceso a la parte valiosa de la web si no se inicia la sesión de modo adecuado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Acceso denegado. Por favor, inicia sesión primero.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

init_db()

# RUTAS
#En la ruta base vamos a la pantalla de inicio si no hay sesion comenzada
#Si si está comenzada vamos a análisis
@app.route('/')
def index():
    if 'user_id' in session: return redirect(url_for('analisis'))
    return render_template('index.html')

#Página de registro, si nos registramos con un nombre no existente, se graba nombre y contraseña y nos redirije al inicio de sesión
#De lo contrario nos muestra un error y nos mantiene en la página de registro.
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        hashed_password = generate_password_hash(password)
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit(); conn.close()
            flash('¡Registro exitoso! Inicia sesión.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Ese nombre de usuario ya está en uso.', 'error')
    return render_template('registro.html')

#Login. Si introducimos un nombre y contraseña adecuados nos dirige a la página de análisis
#En caso contrario nos mostrara un error y nos mantiene en la página.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'], session['username'] = user['id'], user['username']
            flash('¡Bienvenido de nuevo!', 'success')
            return redirect(url_for('analisis'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    return render_template('login.html')
#Simplemente al clicar en cerrar sesión, se borra la misma y nos devuelve a inicio
@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('index'))

# RUTAS PROTEGIDAS
#Análisis: No se puede acceder si no tenemos un usuario logeado
@app.route('/analisis')
@login_required
def analisis():
    conn = get_db_connection()
    informes = conn.execute('SELECT * FROM informes WHERE user_id = ? ORDER BY fecha DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('analisis.html', informes=informes)

#En este caso a parte del login, requerimos de los 3 nombres para los archivos y de haber cargado los archivos 1 y 2 (y que tengan el formato Word o PDF indicados)
@app.route('/procesar', methods=['POST'])
@login_required
def procesar():
    try:
        if 'archivo_favor' not in request.files or 'archivo_contra' not in request.files:
            flash('Faltan archivos en el formulario', 'error')
            return redirect(url_for('analisis'))
            
        file1, file2 = request.files['archivo_favor'], request.files['archivo_contra']
        
        # Capturamos los tres nombres del formulario
        nombre_fav = request.form.get('nombre_fav', 'Doc_Favor').replace(" ", "_")
        nombre_con = request.form.get('nombre_con', 'Doc_Contra').replace(" ", "_")
        nombre_comb = request.form.get('nombre_comb', 'Doc_Combinado').replace(" ", "_")
        
        if file1.filename == '' or file2.filename == '':
            flash('No seleccionaste ningún archivo', 'error')
            return redirect(url_for('analisis'))
        #Obtenemos fecha, se guarda la dirección e descarga y se guardan ahí los documentos
        uid = int(time.time())
        ruta1 = os.path.join(app.config['UPLOAD_FOLDER'], f"F_{uid}_{file1.filename}")
        ruta2 = os.path.join(app.config['UPLOAD_FOLDER'], f"C_{uid}_{file2.filename}")
        file1.save(ruta1); file2.save(ruta2)

        # Pasamos los tres excel, las imagenes de nueves de palabras, y el gráfico de sentimientos
        a_total, a_fav, a_con, img_f, img_c, sentimientos = analizador.procesar_corpus(ruta1, ruta2, nombre_fav, nombre_con, nombre_comb, uid)
        
        #Asociamos los 3 excel al usuario, para que llegado el momento pueda ver el historial
        conn = get_db_connection()
        conn.execute('INSERT INTO informes (user_id, nombre_informe, archivo_final, archivo_favor, archivo_contra) VALUES (?, ?, ?, ?, ?)', 
                     (session['user_id'], nombre_comb, a_total, a_fav, a_con))
        conn.commit(); conn.close()

        return render_template('resultados.html', 
                               excel=a_total, excel_fav=a_fav, excel_con=a_con,
                               nube_favor=img_f, nube_contra=img_c, sent=sentimientos)
    except Exception as e:
        logging.error(f"Error procesando HTTP: {e}")
        flash(f'Ocurrió un error al procesar: {str(e)}', 'error')
        return redirect(url_for('analisis'))

#Para descargar los archivos debemos estar logeados (cada uno podrá descargar los suyos)
@app.route('/descargar/<nombre>')
@login_required
def descargar(nombre):
    try: return send_file(nombre, as_attachment=True)
    except Exception as e: return "Archivo no encontrado.", 404

#Mediante un JSON provisional, y siempre que estemos logeados, procedemos a las busquedas de palabras cuando así se indique.
@app.route('/buscar', methods=['POST'])
@login_required
def buscar():
    try:
        palabra = request.get_json().get('palabra', '')
        if len(palabra) < 2: return jsonify({'favor': {'frases': [], 'conteo': 0, 'porcentaje': 0}, 'contra': {'frases': [], 'conteo': 0, 'porcentaje': 0}, 'total_menciones': 0})
        return jsonify(analizador.buscar_contexto(palabra))
    except Exception as e: return jsonify({'error': str(e)}), 500

# ARRANQUE DEL SERVIDOR (para poder ejecutar desde consola)

if __name__ == '__main__':
    print("\n" + "="*60)
    print(" 🚀 SERVIDOR NLP INICIADO CON ÉXITO")
    print(" 👉 Haz CTRL+CLIC aquí para abrir: \033[94mhttp://127.0.0.1:5000\033[0m")
    print("="*60 + "\n")
    
    # Arrancamos Flask
    app.run(port=5000, debug=False)

