from flask import Flask, render_template_string, request, redirect, url_for, send_file, flash
import psycopg2
import psycopg2.extras
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

app = Flask(__name__)
app.secret_key = "hikmah_secret_key"

# Apne Supabase / PostgreSQL ka Database URL yahan daalein
"postgresql://postgres:Rukh002015@db.szujlftvsoedapkbihit.supabase.co:5432/postgres"

def get_db():
    conn = psycopg2.connect(DB_URL)
    return conn

# Database Table Setup
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            sport TEXT NOT NULL,
            amount REAL NOT NULL,
            entry_date TEXT NOT NULL,
            month TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# HTML Interface (Mobile Friendly Design)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hikmah Sports Academy</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body class="bg-light">
    <div class="container py-3">
        <h2 class="text-center text-primary fw-bold mb-3">🏀 Hikmah Sports Academy</h2>
        
        <!-- Entry Form -->
        <div class="card shadow-sm mb-4">
            <div class="card-header bg-primary text-white fw-bold">Add / Edit Fee Entry</div>
            <div class="card-body">
                <form action="/add" method="POST" class="row g-2">
                    <div class="col-6 col-md-4">
                        <input type="text" name="name" class="form-control" placeholder="Student Name" required>
                    </div>
                    <div class="col-6 col-md-4">
                        <select name="sport" class="form-select" required>
                            <option value="">Select Sport</option>
                            <option value="Skating">Skating</option>
                            <option value="Cricket">Cricket</option>
                            <option value="Football">Football</option>
                            <option value="Karate">Karate</option>
                            <option value="Basketball">Basketball</option>
                        </select>
                    </div>
                    <div class="col-6 col-md-4">
                        <input type="number" step="0.01" name="amount" class="form-control" placeholder="Amount (₹)" required>
                    </div>
                    <div class="col-6 col-md-4">
                        <input type="date" name="entry_date" class="form-control" required>
                    </div>
                    <div class="col-6 col-md-4">
                        <select name="month" class="form-select" required>
                            <option value="January">January</option><option value="February">February</option>
                            <option value="March">March</option><option value="April">April</option>
                            <option value="May">May</option><option value="June">June</option>
                            <option value="July">July</option><option value="August">August</option>
                            <option value="September">September</option><option value="October">October</option>
                            <option value="November">November</option><option value="December">December</option>
                        </select>
                    </div>
                    <div class="col-6 col-md-4">
                        <select name="status" class="form-select" required>
                            <option value="Paid">Paid</option>
                            <option value="Pending">Pending</option>
                        </select>
                    </div>
                    <div class="col-12 text-center mt-3">
                        <button type="submit" class="btn btn-success fw-bold px-4">Save Entry</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Filter Options -->
        <div class="d-flex justify-content-between mb-3">
            <form action="/" method="GET" class="d-flex gap-2">
                <select name="filter_sport" class="form-select">
                    <option value="">All Sports</option>
                    <option value="Skating">Skating</option>
                    <option value="Cricket">Cricket</option>
                    <option value="Football">Football</option>
                    <option value="Karate">Karate</option>
                </select>
                <button type="submit" class="btn btn-purple btn-dark">Filter</button>
            </form>
            <a href="/pdf-group?filter_sport={{ request.args.get('filter_sport', '') }}" class="btn btn-danger">Group PDF</a>
        </div>

        <!-- Data Table -->
        <div class="table-responsive bg-white rounded shadow-sm">
            <table class="table table-bordered align-middle text-center mb-0">
                <thead class="table-dark">
                    <tr>
                        <th>ID</th><th>Name</th><th>Sport</th><th>Amount</th><th>Date</th><th>Status</th><th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in students %}
                    <tr>
                        <td>{{ row.id }}</td>
                        <td>{{ row.name }}</td>
                        <td>{{ row.sport }}</td>
                        <td>₹{{ row.amount }}</td>
                        <td>{{ row.entry_date }}</td>
                        <td>
                            <span class="badge {% if row.status == 'Paid' %}bg-success{% else %}bg-danger{% endif %}">
                                {{ row.status }}
                            </span>
                        </td>
                        <td>
                            <a href="/pdf-single/{{ row.id }}" class="btn btn-sm btn-outline-primary">Receipt</a>
                            <a href="/delete/{{ row.id }}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Delete karein?')">X</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    filter_sport = request.args.get('filter_sport', '')
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if filter_sport:
        cursor.execute("SELECT * FROM students WHERE sport ILIKE %s ORDER BY id DESC", (filter_sport,))
    else:
        cursor.execute("SELECT * FROM students ORDER BY id DESC")
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template_string(HTML_TEMPLATE, students=students)

@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    sport = request.form['sport']
    amount = float(request.form['amount'])
    entry_date = request.form['entry_date']
    month = request.form['month']
    status = request.form['status']

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO students (name, sport, amount, entry_date, month, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (name, sport, amount, entry_date, month, status))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
