import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import get_db

formulario_bp = Blueprint('formulario', __name__)

@formulario_bp.route('/formulario', methods=['GET', 'POST'])
def formulario():
    if request.method == 'POST':
        # 1. Obtener datos del formulario
        nombre = request.form.get('nombre')
        telefono = request.form.get('telefono')
        correo = request.form.get('correo')
        
        distrito = request.form.get('distrito', '')
        direccion = request.form.get('direccion', '')
        direccion_completa = f"{direccion}, {distrito}".strip(", ")
        tipo_entrega = request.form.get('entrega', 'entrega_domicilio')
        comentarios = request.form.get('comentarios', '')
        
        productos_carrito_raw = request.form.get('productos_carrito')

        db = get_db()
        with db.cursor() as cur:
            # 2. Insertar cliente
            sql_cliente = "INSERT INTO cliente (nombre, telefono) VALUES (%s, %s)"
            cur.execute(sql_cliente, (nombre, telefono))
            cliente_id = cur.lastrowid

            # 3. Guardar detalles del cliente
            sql_detalle_cliente = """
                INSERT INTO detalle_cliente (identificador_cliente, direccion, tipo_cliente, fecha_registro)
                VALUES (%s, %s, %s, CURDATE())
            """
            cur.execute(sql_detalle_cliente, (cliente_id, direccion_completa, tipo_entrega))

            # 4. Registrar la Venta
            sql_venta = "INSERT INTO Venta (fecha, identificador_cliente) VALUES (CURDATE(), %s)"
            cur.execute(sql_venta, (cliente_id,))
            venta_id = cur.lastrowid

            # 5. Procesar productos
            if productos_carrito_raw:
                items = json.loads(productos_carrito_raw)
                for item in items:
                    prod_nombre = item.get('name')
                    cant = int(item.get('quantity', 1))
                    precio = float(item.get('price', 0.0))

                    cur.execute("SELECT identificador FROM producto WHERE nombre = %s", (prod_nombre,))
                    prod_row = cur.fetchone()
                    if prod_row:
                        prod_id = prod_row['identificador']
                    else:
                        cur.execute("INSERT INTO producto (nombre, categoria, precio) VALUES (%s, %s, %s)",
                                    (prod_nombre, 'Lácteos', precio))
                        prod_id = cur.lastrowid

                    cur.execute("""
                        INSERT INTO detalle_venta (identificador_venta, identificador_producto, cantidad, precio_unitario)
                        VALUES (%s, %s, %s, %s)
                    """, (venta_id, prod_id, cant, precio))
            else:
                prod_nombre = request.form.get('producto')
                cant = int(request.form.get('cantidad', 1))

                if prod_nombre:
                    cur.execute("SELECT identificador, precio FROM producto WHERE nombre = %s", (prod_nombre,))
                    prod_row = cur.fetchone()
                    if prod_row:
                        prod_id = prod_row['identificador']
                        precio = prod_row['precio']
                    else:
                        precio = 0.0
                        cur.execute("INSERT INTO producto (nombre, categoria, precio) VALUES (%s, %s, %s)",
                                    (prod_nombre, 'Lácteos', precio))
                        prod_id = cur.lastrowid

                    cur.execute("""
                        INSERT INTO detalle_venta (identificador_venta, identificador_producto, cantidad, precio_unitario)
                        VALUES (%s, %s, %s, %s)
                    """, (venta_id, prod_id, cant, precio))

        db.commit()
        
        flash("¡Tu pedido ha sido registrado con éxito!", "ok")
        return redirect(url_for('formulario.formulario'))

    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT nombre AS name, precio AS price, categoria AS detail FROM producto")
        products = cur.fetchall()

    return render_template('clientes/formulario.html', products=products, datos={})