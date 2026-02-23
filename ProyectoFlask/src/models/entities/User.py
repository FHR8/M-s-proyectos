from werkzeug.security import check_password_hash, generate_password_hash
#Importamos la libreria para la seguridad tipo has en las contraseñas
from flask_login import UserMixin
class User(UserMixin):
    def __init__(self,id,Correo,Contrasenya):
        self.id=id
        self.nombre=""
        self.Apellido1=""
        self.Apellido2=""
        self.Correo=Correo
        self.Contrasenya = Contrasenya
        self.fecha_hoy = "01-01-2000"
    #Un constructor al que le pasamos el email y el password.
    @classmethod
    def check_password(self, hashed_password, password):
        print(hashed_password)
        print(password)
        return check_password_hash(hashed_password, password)
    #Método que nos va a retornar la contraseña hasheada

print(generate_password_hash("admin"))


