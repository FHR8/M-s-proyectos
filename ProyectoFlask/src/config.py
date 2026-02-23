class Config:
    SECRET_KEY = 'B!1weNAt1T^%kvhUI*S^'
#Clave para mensajes tipo "Contraseña no válida o similares".

class DevelopmentConfig(Config):
    DEBUG=True
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'dom_salamanca'
#Modo depuración activado y conexion BBDD
config={
    'development':DevelopmentConfig
}