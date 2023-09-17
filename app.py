from flask import jsonify
import os
from flask import session
from flask import Flask
from flask import render_template, request, redirect
from flaskext.mysql import MySQL
from datetime import datetime
from flask import send_from_directory
from dotenv import load_dotenv
import uuid



load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


mysql = MySQL(app)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['MYSQL_DATABASE_HOST'] = 'bkpxwmspyhvlwbsedoix-mysql.services.clever-cloud.com'
app.config['MYSQL_DATABASE_USER'] = 'ulp53jflirtiiq73'
app.config['MYSQL_DATABASE_PASSWORD'] = 'jGxGZjj8kmle7w7F5UWk'
app.config['MYSQL_DATABASE_DB'] = 'bkpxwmspyhvlwbsedoix'


mysql.init_app(app)


@app.route('/buscar_producto', methods=['POST'])
def buscar_producto():
    query = request.form.get('query', '')

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre, precio FROM productos WHERE nombre LIKE %s LIMIT 5", ("%" + query + "%",))
    resultados = cursor.fetchall()
    conexion.close()

    
    return jsonify(resultados)



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


@app.route('/admin/carrito', methods=['GET', 'POST'])
def admin_carrito():

    if 'compras' not in session:
        session['compras'] = []

    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, precio FROM productos")
    productos = cursor.fetchall()
    conexion.close()
    nombres_productos = [producto[1] for producto in productos]

    if request.method == 'POST':
        nombre = request.form['txtNombre']
        cantidad = float(request.form['txtCantidad'])
        fecha = request.form['txtFecha']
        precio = request.form['txtPrecio']

        id_generado = str(uuid.uuid4())
        compra = (id_generado, nombre, cantidad, fecha, precio)
        session['compras'].append(compra)
        session.modified = True  # Asegurarte de que Flask sabe que la sesión ha cambiado

    return render_template('/admin/carrito.html', nombres_productos=nombres_productos, productos=productos)



@app.route('/admin/carrito/borrar', methods=['POST'])
def admin_carrito_borrar():
    compra_id = request.form['txtID']
    session['compras'] = [compra for compra in session['compras'] if compra[0] != compra_id]
    session.modified = True  # Notifica a Flask que la sesión ha cambiado
    return redirect('/admin/carrito')




@app.route('/admin/productos/guardar', methods=['POST'])
def admin_productos_guardar():

    if not 'login' in session:
        return redirect("/admin/login")

    _nombre=request.form['txtNombre']    
    _archivo=request.files['txtImagen']
    _url=request.form['txtURL']
    _precio = request.form['txtPrecio']

    tiempo= datetime.now()
    horaActual=tiempo.strftime('%Y%H%M%S')

    if _archivo.filename!="":
        nuevoNombre=horaActual+"_"+_archivo.filename
        _archivo.save("templates/sitio/img/"+nuevoNombre)

    sql = "INSERT INTO `productos` (`id`, `nombre`, `imagen`, `url`, `precio`) VALUES (NULL, %s, %s, %s, %s);"

    datos = (_nombre, nuevoNombre, _url, _precio)
    conexion=mysql.connect()
    cursor=conexion.cursor()
    cursor.execute(sql,datos)
    conexion.commit()

    print(_nombre)
    print(_url)
    print(_archivo)
    print(_precio)

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



