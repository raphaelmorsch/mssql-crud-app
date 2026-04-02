import os

import pyodbc
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mssql-crud-app-key")

MSSQL_HOST = os.environ.get("MSSQL_HOST", "mssql-deployment")
MSSQL_PORT = os.environ.get("MSSQL_PORT", "1433")
MSSQL_USER = os.environ.get("MSSQL_USER", "sa")
MSSQL_PASSWORD = os.environ.get("MSSQL_SA_PASSWORD", "")
MSSQL_DATABASE = os.environ.get("MSSQL_DATABASE", "cruddb")


def get_connection_string():
    return (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={MSSQL_HOST},{MSSQL_PORT};"
        f"DATABASE={MSSQL_DATABASE};"
        f"UID={MSSQL_USER};"
        f"PWD={MSSQL_PASSWORD};"
        f"TrustServerCertificate=yes;"
    )


def get_db():
    return pyodbc.connect(get_connection_string())


def init_db():
    """Create the database and items table if they don't exist."""
    master_conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={MSSQL_HOST},{MSSQL_PORT};"
        f"DATABASE=master;"
        f"UID={MSSQL_USER};"
        f"PWD={MSSQL_PASSWORD};"
        f"TrustServerCertificate=yes;"
    )
    conn = pyodbc.connect(master_conn_str, autocommit=True)
    cursor = conn.cursor()
    cursor.execute(
        f"IF DB_ID('{MSSQL_DATABASE}') IS NULL CREATE DATABASE [{MSSQL_DATABASE}]"
    )
    cursor.close()
    conn.close()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        IF OBJECT_ID('items', 'U') IS NULL
        CREATE TABLE items (
            id        INT IDENTITY(1,1) PRIMARY KEY,
            name      NVARCHAR(200)  NOT NULL,
            description NVARCHAR(MAX) NULL,
            quantity  INT            NOT NULL DEFAULT 0,
            created_at DATETIME2     NOT NULL DEFAULT GETUTCDATE()
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()


@app.route("/")
def index():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, description, quantity, created_at "
            "FROM items ORDER BY created_at DESC"
        )
        columns = [col[0] for col in cursor.description]
        items = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        db_ok = True
    except Exception as exc:
        items = []
        db_ok = False
        flash(f"Database error: {exc}", "error")

    return render_template(
        "index.html",
        items=items,
        db_ok=db_ok,
        db_host=MSSQL_HOST,
        db_name=MSSQL_DATABASE,
    )


@app.route("/create", methods=["POST"])
def create():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    quantity = request.form.get("quantity", "0").strip()

    if not name:
        flash("Name is required.", "error")
        return redirect(url_for("index"))

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO items (name, description, quantity) VALUES (?, ?, ?)",
            (name, description, int(quantity)),
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash(f"Item '{name}' created successfully.", "success")
    except Exception as exc:
        flash(f"Create failed: {exc}", "error")
    return redirect(url_for("index"))


@app.route("/update/<int:item_id>", methods=["POST"])
def update(item_id):
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    quantity = request.form.get("quantity", "0").strip()

    if not name:
        flash("Name is required.", "error")
        return redirect(url_for("index"))

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE items SET name = ?, description = ?, quantity = ? WHERE id = ?",
            (name, description, int(quantity), item_id),
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash(f"Item '{name}' updated successfully.", "success")
    except Exception as exc:
        flash(f"Update failed: {exc}", "error")
    return redirect(url_for("index"))


@app.route("/delete/<int:item_id>", methods=["POST"])
def delete(item_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Item deleted.", "success")
    except Exception as exc:
        flash(f"Delete failed: {exc}", "error")
    return redirect(url_for("index"))


@app.route("/health")
def health():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return jsonify({"status": "healthy", "database": MSSQL_DATABASE}), 200
    except Exception as exc:
        return jsonify({"status": "degraded", "error": str(exc)}), 503


with app.app_context():
    try:
        init_db()
    except Exception as exc:
        print(f"[WARN] Could not initialise DB on startup: {exc}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
