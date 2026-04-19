from .entities.User import User
from datetime import date

class ModelUser():

    @classmethod
    def login(self,db,user):
        try:
            cursor=db.connection.cursor()
            sql="""SELECT id,Nombre,Apellido1,Apellido2, Correo, Contrasenya, Fecha from login where correo = '{}'""".format(user.Correo)
            cursor.execute(sql)
            row=cursor.fetchone()
            if row != None:
                print(row[0])
                print(row[4])
                print(row[5])
                print(user.Contrasenya+ " primero")
                print(user.check_password(row[5],user.Contrasenya))
                #user = User(row[0],User.check_password(row[1],user.password))
                user = User(row[0],row[4],row[5])
                user.nombre=row[1],row[6]
                user.Apellido1=row[2]
                user.Apellido2=row[3]
                user.fecha_hoy=row[6]
                return user
            else:
                print("Este tio no existe")
                return None
        except Exception as ex:
            raise Exception(ex)

    @classmethod
    def get_by_id(self,db,id):
        try:
            cursor=db.connection.cursor()
            sql="SELECT id,correo from login where id = {}".format(id)
            cursor.execute(sql)
            row=cursor.fetchone()
            if row != None:
                print(row[0])
                print(row[1])
                #print(user.password+ " primero")
                #print(user.check_password(row[1],user.password))
                #user = User(row[0],User.check_password(row[1],user.password))
                return User(row[0],row[1],None)
            else:
                print("Nada que retornar")
                return None
        except Exception as ex:
            raise Exception(ex)
    #Domingo
    @classmethod
    def obtener_id(self, db):
        try:
            cursor=db.connection.cursor()
            sql="select count(id) from login"
            cursor.execute(sql)
            row=cursor.fetchone()
            n=int(row[0])+1
            print(n)
            return n
        except Exception as ex:
            raise Exception(ex)

    @classmethod
    def fecha_hoy(self):
        return date.today().strftime('%Y-%m-%d')

    @classmethod
    def registro(self, db, user):
        try:
            fecha=ModelUser.fecha_hoy()
            id=ModelUser.obtener_id(db)
            cursor = db.connection.cursor()
            sql = """INSERT INTO login (id, Nombre, Apellido1, Apellido2, Correo, Contrasenya, Fecha) VALUES (%s,%s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (id, user.nombre, user.Apellido1, user.Apellido2, user.Correo, user.Contrasenya, fecha))
            db.connection.commit()
            cursor.close()
            return True  # Inserción exitosa
        except Exception as e:
            print("Error al insertar en la base de datos:", e)
            return False  # Error al insertar


    

