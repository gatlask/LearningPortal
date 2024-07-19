import csv
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set this to a random secret key

def load_users():
    users = {}
    if not os.path.exists('users.csv'):
        with open('users.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['email', 'password', 'role', 'name'])
            # Add a default manager
            writer.writerow(['manager@example.com', generate_password_hash('manager123'), 'manager', 'John Manager'])
    with open('users.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            users[row[0]] = {'password': row[1], 'role': row[2], 'name': row[3]}
    return users

def load_courses():
    courses = {}
    if not os.path.exists('courses.csv'):
        with open('courses.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'assigned_to'])
    with open('courses.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            courses[int(row[0])] = {'name': row[1], 'assigned_to': row[2].split(';') if row[2] else []}
    return courses

# def load_users():
#     users = {}
#     with open('users.csv', 'r') as f:
#         reader = csv.reader(f)
#         next(reader)  # Skip header
#         for row in reader:
#             users[row[0]] = {'password': row[1], 'role': row[2], 'name': row[3]}
#     return users


def save_users(users):
    with open('users.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['email', 'password', 'role', 'name'])
        for email, data in users.items():
            writer.writerow([email, data['password'], data['role'], data['name']])


# def load_courses():
#     courses = {}
#     with open('courses.csv', 'r') as f:
#         reader = csv.reader(f)
#         next(reader)  # Skip header
#         for row in reader:
#             courses[int(row[0])] = {'name': row[1], 'assigned_to': row[2].split(';') if row[2] else []}
#     return courses


def save_courses(courses):
    with open('courses.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'name', 'assigned_to'])
        for id, data in courses.items():
            writer.writerow([id, data['name'], ';'.join(data['assigned_to'])])


users = load_users()
courses = load_courses()


@app.route('/')
def home():
    return render_template('portal.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email in users and check_password_hash(users[email]['password'], password):
            session['user'] = email
            session['role'] = users[email]['role']
            session['name'] = users[email]['name']
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid email or password')
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['role'] == 'manager':
        return redirect(url_for('manager_dashboard'))
    else:
        return redirect(url_for('employee_dashboard'))


@app.route('/manager_dashboard')
def manager_dashboard():
    if 'user' not in session or session['role'] != 'manager':
        return redirect(url_for('login'))
    return render_template('manager_dashboard.html', user=session['name'], courses=courses, users=users)


@app.route('/employee_dashboard')
def employee_dashboard():
    if 'user' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))
    assigned_courses = [course for course in courses.values() if session['name'] in course['assigned_to']]
    return render_template('employee_dashboard.html', user=session['name'], courses=assigned_courses)


@app.route('/courses')
def course_list():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('course_list.html', courses=courses)


@app.route('/add_course', methods=['POST'])
def add_course():
    if 'user' not in session or session['role'] != 'manager':
        return redirect(url_for('login'))
    course_name = request.form['course_name']
    new_id = max(courses.keys()) + 1 if courses else 1
    courses[new_id] = {'name': course_name, 'assigned_to': []}
    save_courses(courses)
    flash('Course added successfully', 'success')
    return redirect(url_for('manager_dashboard'))


@app.route('/assign_course', methods=['POST'])
def assign_course():
    if 'user' not in session or session['role'] != 'manager':
        return redirect(url_for('login'))
    course_id = int(request.form['course_id'])
    employee_name = request.form['employee_name']
    employee_email = next(
        (email for email, data in users.items() if data['name'] == employee_name and data['role'] == 'employee'), None)
    if not employee_email:
        flash('Invalid employee name', 'error')
    elif len(courses[course_id]['assigned_to']) >= 2:
        flash('Course is already full', 'error')
    elif employee_name in courses[course_id]['assigned_to']:
        flash('Employee is already assigned to this course', 'error')
    else:
        courses[course_id]['assigned_to'].append(employee_name)
        save_courses(courses)
        flash('Course assigned successfully', 'success')
    return redirect(url_for('manager_dashboard'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('role', None)
    session.pop('name', None)
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)