from flask import Blueprint, render_template

from app.catalog import PRODUCTS
from app.db import query

productos_bp = Blueprint("productos", __name__)

CATEGORIAS_WEB = {"leche", "yogurt", "queso", "mantequilla", "crema"}

IMAGENES = {
    "leche": "https://images.unsplash.com/photo-1550583724-b2692b85b150?auto=format&fit=crop&w=900&q=85",
    "yogurt": "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=900&q=85",
    "queso": "https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?auto=format&fit=crop&w=900&q=85",
}
IMAGEN_DEFECTO = IMAGENES["leche"]


def _productos_con_mysql():
    """Lo visual sale de catalog.py; precio/stock de MySQL.
    Los productos que solo existen en MySQL (creados en el escritorio) se agregan al final."""
    productos = [dict(p) for p in PRODUCTS]  # copia, no se modifica catalog.py

    try:
        filas = query(
            "SELECT p.identificador, p.slug, p.nombre, p.categoria, p.presentacion, p.precio, "
            "p.imagen_url, COALESCE(i.stock, 0) AS stock "
            "FROM producto p "
            "LEFT JOIN inventario i ON i.identificador_producto = p.identificador "
            "ORDER BY p.identificador"
        )
    except Exception as e:
        # Si MySQL está apagado, la web sigue funcionando con los datos de catalog.py
        print("No se pudo leer MySQL:", e)
        filas = []

    por_slug = {f["slug"]: f for f in filas if f["slug"]}
    slugs_catalogo = {p["id"] for p in productos}

    # 1) Productos de catalog.py: precio y stock desde MySQL
    for p in productos:
        fila = por_slug.get(p["id"])
        if fila:
            p["price"] = float(fila["precio"])
            p["stock"] = int(fila["stock"])
            p["agotado"] = p["stock"] <= 0
        else:
            p["stock"] = None      # sin dato en MySQL: no se bloquea la compra
            p["agotado"] = False

    # 2) Productos nuevos (solo en MySQL): se agregan completos
    for f in filas:
        if f["slug"] in slugs_catalogo:
            continue
        categoria = (f["categoria"] or "").lower()
        if categoria not in CATEGORIAS_WEB:
            categoria = "otros"
        stock = int(f["stock"])
        imagen = f["imagen_url"] or IMAGENES.get(categoria, IMAGEN_DEFECTO)
        productos.append({
            "id": f"db-{f['identificador']}",
            "name": f["nombre"],
            "detail": f["presentacion"] or "",
            "category": categoria,
            "price": float(f["precio"]),
            "featured": False,
            "rating": 0,
            "stock": stock,
            "agotado": stock <= 0,
            "image": imagen,
            "alt": f["nombre"],
        })
    return productos


@productos_bp.get("/productos")
def productos():
    return render_template("clientes/productos.html", products=_productos_con_mysql())