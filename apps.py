from flask import Flask, render_template, request, redirect, flash, send_file, session
import sqlite3
import csv
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Initialize the database
def init_db():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
        roll_no INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        course TEXT,
        grade TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )''')
    conn.commit()
    conn.close()


# Seed the database with a default admin user
def seed_user():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'password123')")
    conn.commit()
    conn.close()


# Route: Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = username
            return redirect('/dashboard')
        else:
            flash("Invalid credentials!", "danger")
    
    return render_template('login.html')


# Route: Dashboard
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/')
    return render_template('dashboard.html')


# Route: Add Student
@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if 'username' not in session:
        return redirect('/')

    if request.method == 'POST':
        roll_no = request.form['roll_no']
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        course = request.form['course']
        grade = request.form['grade']

        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()

        # Check if the roll number already exists
        cursor.execute("SELECT * FROM students WHERE roll_no = ?", (roll_no,))
        existing_student = cursor.fetchone()

        if existing_student:
            flash("Roll number already exists! Please use a unique roll number.", "danger")
        else:
            try:
                cursor.execute("INSERT INTO students VALUES (?, ?, ?, ?, ?, ?)", 
                               (roll_no, name, age, gender, course, grade))
                conn.commit()
                flash("Student added successfully!", "success")
            except Exception as e:
                flash(f"An error occurred: {e}", "danger")
            finally:
                conn.close()

        return redirect('/view')

    return render_template('add.html')


# Route: View Students with pagination and sorting
@app.route('/view')
def view_students():
    if 'username' not in session:
        return redirect('/')

    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()

    # Query is now fixed to sort by roll_no in ascending order
    query = "SELECT * FROM students ORDER BY roll_no ASC LIMIT ? OFFSET ?"
    cursor.execute(query, (per_page, offset))
    students = cursor.fetchall()

    # Fetch total students for pagination
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]
    conn.close()

    total_pages = (total_students + per_page - 1) // per_page

    return render_template('view.html', students=students, page=page, total_pages=total_pages)


# Route: Edit Student
@app.route('/edit', methods=['GET', 'POST'])
def edit_student():
    if 'username' not in session:
        return redirect('/')

    if request.method == 'POST':
        roll_no = request.form['roll_no']
        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE roll_no=?", (roll_no,))
        student = cursor.fetchone()
        conn.close()
        if student:
            return render_template('edit.html', student=student)
        else:
            flash("Student not found!", "danger")
            return redirect('/edit')

    return render_template('edit_search.html')


# Route: Save Edited Student Details
@app.route('/update_student', methods=['POST'])
def update_student():
    if 'username' not in session:
        return redirect('/')

    roll_no = request.form['roll_no']
    name = request.form['name']
    age = request.form['age']
    gender = request.form['gender']
    course = request.form['course']
    grade = request.form['grade']

    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE students
        SET name=?, age=?, gender=?, course=?, grade=?
        WHERE roll_no=?
    """, (name, age, gender, course, grade, roll_no))
    conn.commit()
    conn.close()

    flash("Student details updated successfully!", "success")
    return redirect('/view')


# Route: Delete Student
@app.route('/delete', methods=['GET', 'POST'])
def delete_student():
    if 'username' not in session:
        return redirect('/')

    if request.method == 'POST':
        roll_no = request.form['roll_no']
        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE roll_no=?", (roll_no,))
        conn.commit()
        conn.close()
        flash("Student deleted successfully!", "success")
        return redirect('/view')

    return render_template('delete.html')


# Route: Search Students
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        if search_query:
            conn = sqlite3.connect('students.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE name LIKE ?", ('%' + search_query + '%',))
            results = cursor.fetchall()
            conn.close()
            if not results:
                flash("No results found!", "info")
            return render_template('search.html', results=results, query=search_query)
        else:
            flash("Please enter a search term!", "error")
    return render_template('search.html', results=None, query=None)


# Route: Export Students
@app.route('/export')
def export_students():
    if 'username' not in session:
        return redirect('/')

    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    rows = cursor.fetchall()
    conn.close()

    with open('student.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Roll No', 'Name', 'Age', 'Gender', 'Course', 'Grade'])
        writer.writerows(rows)

    return send_file('student.csv', as_attachment=True)


# Route: Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("Logged out successfully!", "success")
    return redirect('/')


if __name__ == '__main__':
    init_db()
    seed_user()
    app.run(debug=True)
