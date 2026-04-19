from flask import Flask, render_template,request,redirect,url_for,flash
#Devolverá la renderización de una plantilla (una vista)
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager,login_user,logout_user,login_required
from config import config 

#Models
from models.ModelUser import ModelUser

#Entidades
from models.entities.User import User

app=Flask(__name__)

csrf=CSRFProtect()

db=MySQL(app)

login_manager_app=LoginManager(app)

@login_manager_app.user_loader
def load_user(id):
    return ModelUser.get_by_id(db, id)
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method =='POST':
        print(request.form['correo'])
        print(request.form['contrasenya'])
        print("Si es post")
        user=User(1,request.form['correo'], request.form['contrasenya'])
        logger_user=ModelUser.login(db,user)
        print("El email es: "+str(user.id)+" "+user.Correo+" "+user.Contrasenya)
        if logger_user != None:
            print("entramos en el if")
            if logger_user.Contrasenya==user.Contrasenya and logger_user.Correo != 'admin@gmail.com':
                login_user(logger_user)
                print("Logeruser contraseña")
                return redirect(url_for('home'))
            elif logger_user.Contrasenya==user.Contrasenya and logger_user.Correo == 'admin@gmail.com':
                login_user(logger_user)
                print("Logeruser contraseña")
                return redirect(url_for('admin'))
            else:
                print("contraseña no válida")
                flash("La contraseña no coincide")
                return render_template('auth/login.html') 
        else:
            print("Logeruser es none")
            flash("El usuario no existe")
            return render_template('auth/login.html')
    else: #Si no es post, devuelve la plantilla
        print("no es post")
        return render_template('auth/login.html')
#Domingo desde aquí
@app.route('/registro', methods=['GET','POST']) #Indicamos la ruta
def registro(): #Creamos un método
    print("Estoy en el registro "+str(ModelUser.obtener_id(db))+ " "+ ModelUser.fecha_hoy()) 
    tienen_algo()
    return render_template('auth/registro.html') #retornamos una página

def tienen_algo():
    if request.method == 'POST':
        print(request.form['Apellido1'])
        if  request.form['nombre'].strip() and request.form['Apellido1'].strip() and request.form['Apellido2'].strip() and request.form['Correo'].strip() and request.form['Contrasenya'].strip() and request.form['repite'].strip():
            print("Todos los campos contienen algo")
            user=User(0,request.form['Correo'],request.form['Contrasenya'])
            user.nombre=request.form['nombre']
            user.Apellido1=request.form['Apellido1']
            user.Apellido2=request.form['Apellido2']
            ModelUser.registro(db,user)
        else:
            print("Algún campo está vacio")
    else:
        print("No es post")


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))
@app.route('/home')
def home():
    return render_template('home.html')
@app.route('/protected')
@login_required
def protected():
    return "<h1>Esta es una vista protegida, sólo para usuarios autenticados</h1>"
@app.route('/admin')
def admin():
    return render_template('auth/admin.html')
def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1>Página no encontrada</h1>",404

if __name__=='__main__':
    app.config.from_object(config['development'])
    csrf.init_app(app)
    app.register_error_handler(401,status_401)
    app.register_error_handler(404,status_404)
    app.run()
#Activar el modo depuración y arrancar el programa.
