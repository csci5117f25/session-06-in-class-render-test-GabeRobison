import os
from contextlib import contextmanager
from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import DictCursor

app = Flask(__name__)
pool = None

def setup():
    global pool
    DATABASE_URL = os.environ['DATABASE_URL']
    pool = ThreadedConnectionPool(1, 10, dsn=DATABASE_URL, sslmode='require')

@contextmanager
def get_db_connection():
    try:
        connection = pool.getconn()
        yield connection
    finally:
        pool.putconn(connection)

@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as connection:
        cursor = connection.cursor(cursor_factory=DictCursor)
        try:
            yield cursor
            if commit:
                connection.commit()
        finally:
            cursor.close()

def add_guestbook_entry(name, message):
    with get_db_cursor(True) as cur:
        cur.execute("INSERT INTO guestbook (name, message) VALUES (%s, %s)", (name, message))

def get_guestbook_entries():
    with get_db_cursor() as cur:
        cur.execute("SELECT name, message, created_at FROM guestbook ORDER BY created_at DESC LIMIT 50")
        return cur.fetchall()

@app.before_request
def before_request():
    global pool
    if pool is None:
        setup()

@app.route('/')
def hello():
    entries = get_guestbook_entries()
    return render_template('hello.html', entries=entries)

@app.route('/sign', methods=['POST'])
def sign_guestbook():
    name = request.form.get('name', '')
    message = request.form.get('message', '')
    if name and message:
        add_guestbook_entry(name, message)
    return redirect(url_for('hello'))

if __name__ == '__main__':
    app.run(debug=True)