from flask import jsonify
import os
from flask import session
from flask import Flask
from flask import render_template, request, redirect
from flaskext.mysql import MySQL
from datetime import datetime
from flask import send_from_directory
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


mysql = MySQL(app)

app.config['MYSQL_DATABASE_USER'] = os.getenv("MYSQLUSER")
app.config['MYSQL_DATABASE_PASSWORD'] = os.getenv("MYSQLPASSWORD")
app.config['MYSQL_DATABASE_DB'] = os.getenv("MYSQLDATABASE")
app.config['MYSQL_DATABASE_HOST'] = os.getenv("MYSQLHOST")
app.config['MYSQL_DATABASE_PORT'] = int(os.getenv("MYSQLPORT"))


mysql.init_app(app)


@app.route('/buscar_producto', methods=['POST'])
def buscar_producto():
    query = request.form.get('query', '')

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre, precio FROM productos WHERE nombre LIKE %s LIMIT 5", ("%" + query + "%",))
    resultados = cursor.fetchall()
    conexion.close()

    # Convertir resultados en una lista de diccionarios
    productos = [{"nombre": result[0], "precio": str(result[1])} for result in resultados]

    return jsonify(productos)


@app.route('/')
def inicio():
    return render_template('sitio/index.html')

@app.route('/img/<imagen>')
def imagenes(imagen):
    print(imagen)
    return send_from_directory(os.path.join('templates/sitio/img'),imagen)

@app.route("/css/<archivocss>")  
def css_link(archivocss):
    return send_from_directory(os.path.join('templates/sitio/css'),archivocss)  


@app.route('/productos')
def productos():

    conexion=mysql.connect()
    cursor=conexion.cursor()
    cursor.execute("SELECT * FROM `productos` ")
    productos=cursor.fetchall()
    conexion.commit()
    print(productos)

    return render_template('sitio/productos.html', productos=productos)

@app.route('/nosotros')
def nosotros():
    return render_template('sitio/nosotros.html')

@app.route('/admin')
def admin_index():
    if not 'login' in session:
        return redirect("/admin/login")
    return render_template('admin/index.html')

@app.route('/admin/login')
def admin_login():
    return render_template('/admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    _usuario=request.form['txtUsuario']
    _password=request.form['txtPassword']
    print(_usuario)
    print(_password)

    if _usuario=="admin" and _password=="123456":
        session["login"]=True
        session["usuario"]="Administrador"
        return redirect("/admin")
                
    return render_template("/admin/login.html", mensaje="Acceso Denegado Usuario o Contraseña incorrecta")

@app.route('/admin/cerrar')
def admin_login_cerrar():
    session.clear()
    return redirect('/admin/login')

@app.route('/admin/productos')
def admin_productos():

    if not 'login' in session:
        return redirect("/admin/login")

    conexion=mysql.connect()
    cursor=conexion.cursor()
    cursor.execute("SELECT * FROM `productos` ")
    productos=cursor.fetchall()
    conexion.commit()
    print(productos)

    return render_template("/admin/productos.html", productos=productos)

@app.route('/admin/cabecera')
def admin_cabecera():
    return render_template("admin/cabecera.html")

compras = [] # Esta lista almacenará temporalmente las compras.

@app.route('/admin/carrito', methods=['GET', 'POST'])
def admin_carrito():
    if request.method == 'POST':
        nombre = request.form['txtNombre']
        cantidad = float(request.form['txtCantidad'])
        fecha = request.form['txtFecha']
        precio = request.form['txtPrecio']
        

        # Aquí asigno un ID de manera incremental basado en la longitud de la lista. En una base de datos real, el ID sería generado automáticamente.
        compra_id = len(compras) + 1
        compras.append((compra_id, nombre, cantidad, fecha, precio))
        
    return render_template('/admin/carrito.html', compras=compras)

@app.route('/admin/carrito/borrar', methods=['POST'])
def admin_carrito_borrar():
    compra_id = int(request.form['txtID'])
    global compras
    compras = [compra for compra in compras if compra[0] != compra_id]
    return redirect('/admin/carrito')



@app.route('/admin/carrito/enviar-whatsapp', methods=['POST'])
def enviar_whatsapp():
    global compras
    message = "Mis compras:\n\n"
    
    for compra in compras:
        message += f"Nombre: {compra[1]}, Cantidad: {compra[2]}, Fecha: {compra[3]}\n"
    
    # Formatear el mensaje para la URL de WhatsApp
    message = message.replace(" ", "%20").replace("\n", "%0A")

    # Número de teléfono al que quieres enviar el mensaje en formato internacional
    telefono_destino = "+527751523417"
    
    # Crear la URL usando wa.me
    whatsapp_url = f"https://wa.me/{telefono_destino}?text={message}"
    
    # Limpiar la lista de compras
    compras = []

    # Redireccionar a WhatsApp
    return redirect(whatsapp_url)



@app.route('/admin/productos/guardar', methods=['POST'])
def admin_productos_guardar():

    if not 'login' in session:
        return redirect("/admin/login")

    _nombre=request.form['txtNombre']    
    _archivo=request.files['txtImagen']
    _url=request.form['txtURL']

    tiempo= datetime.now()
    horaActual=tiempo.strftime('%Y%H%M%S')

    if _archivo.filename!="":
        nuevoNombre=horaActual+"_"+_archivo.filename
        _archivo.save("templates/sitio/img/"+nuevoNombre)

    sql="INSERT INTO `productos` (`id`, `nombre`, `imagen`, `url`) VALUES (NULL,%s,%s,%s);"
    datos=(_nombre,nuevoNombre,_url)
    conexion=mysql.connect()
    cursor=conexion.cursor()
    cursor.execute(sql,datos)
    conexion.commit()

    print(_nombre)
    print(_url)
    print(_archivo)

    print(request.form['txtNombre'])
    return redirect("/admin/productos")



@app.route('/admin/productos/borrar', methods=['POST'])
def admin_productos_borrar():

    if not 'login' in session:
        return redirect("/admin/login")

    _id=request.form['txtID']
    print(_id)

    conexion=mysql.connect()
    cursor=conexion.cursor()
    cursor.execute("SELECT imagen FROM `productos` WHERE id=%s",(_id))
    producto=cursor.fetchall()
    conexion.commit()
    print(producto) 

    if os.path.exists("templates/sitio/img/"+str(producto[0][0])):
        os.unlink("templates/sitio/img/"+str(producto[0][0]))

    conexion=mysql.connect()
    cursor= conexion.cursor()
    cursor.execute("DELETE FROM productos WHERE id=%s",(_id))
    conexion.commit()

    return redirect('/admin/productos')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


