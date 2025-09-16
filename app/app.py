from flask import Flask, jsonify, request
from db import get_conn

app = Flask(__name__)

def init_db():
    """Crea la tabla 'items' si no existe."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)
            conn.commit()

@app.get("/health")
def health():
    return {"status": "ok"}, 200

@app.get("/items")
def list_items():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM items ORDER BY id ASC;")
            rows = cur.fetchall()
            return jsonify([{"id": r[0], "name": r[1]} for r in rows])

@app.post("/items")
def create_item():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    if not name:
        return {"error": "name is required"}, 400
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO items(name) VALUES (%s) RETURNING id;", (name,))
            new_id = cur.fetchone()[0]
            conn.commit()
            return {"id": new_id, "name": name}, 201

if __name__ == "__main__":
    init_db()  # Llama a la función para inicializar la base de datos
    app.run(host="0.0.0.0", port=5000)