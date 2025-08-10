from flask import Flask, render_template, request, redirect, url_for, session, flash
import cx_Oracle
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Oracle DB connection - update host, service_name, user, password
dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XE")
conn = cx_Oracle.connect(user="system", password="daksha", dsn=dsn)

def get_cursor():
    return conn.cursor()

# Function to generate random alphanumeric application ID
def generate_application_id(length=12):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))

@app.route('/')
def home():
    return render_template('home.html')

# Customer Sign Up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', None)  

        cursor = get_cursor()
        cursor.execute("SELECT id FROM customers WHERE username = :u", {"u": username})
        if cursor.fetchone():
            flash("Username already exists")
            return redirect(url_for('signup'))

        pw_hash = generate_password_hash(password)

        cursor.execute(
            "INSERT INTO customers (username, password, email) VALUES (:u, :p, :e)",
            {"u": username, "p": pw_hash, "e": email}
        )
        conn.commit()
        flash("Signup successful, please login.")
        return redirect(url_for('customer_login'))
    return render_template('signup.html')

# Customer Login
@app.route('/customer_login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = get_cursor()
        cursor.execute("SELECT id, password FROM customers WHERE username = :u", {"u": username})
        user = cursor.fetchone()
        if user and check_password_hash(user[1], password):
            session['customer_id'] = user[0]
            session['username'] = username
            return redirect(url_for('customer_dashboard'))
        else:
            flash("Invalid credentials")
    return render_template('customer_login.html')

# Customer Dashboard
@app.route('/customer_dashboard')
def customer_dashboard():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))
    return render_template('customer_dashboard.html', username=session.get('username'))

@app.route('/customer_logout')
def customer_logout():
    session.clear()
    return redirect(url_for('home'))

# New Application
@app.route('/new_application', methods=['GET', 'POST'])
def new_application():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        dob = request.form['dob']
        gender = request.form['gender']
        address = request.form['address']
        phone = request.form['phone']
        customer_id = session['customer_id']

        app_id = generate_application_id()

        cursor = get_cursor()

        cursor.execute("""
            INSERT INTO applications
            (id, customer_id, first_name, last_name, dob, passport_number, status)
            VALUES (:id, :cid, :fn, :ln, TO_DATE(:dob, 'YYYY-MM-DD'), NULL, 'Pending')
        """, {
            "id": app_id,
            "cid": customer_id,
            "fn": first_name,
            "ln": last_name,
            "dob": dob
        })

        conn.commit()

        estimated_days = 15  # example estimate for processing time

        return render_template('application_submitted.html', app_id=app_id, est_days=estimated_days)

    return render_template('new_application.html')

# Update Profile
@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))

    cursor = get_cursor()
    customer_id = session['customer_id']

    if request.method == 'POST':
        email = request.form['email']
        address = request.form['address']
        phone = request.form['phone']
        gender = request.form['gender']
        dob = request.form['dob']  # YYYY-MM-DD

        cursor.execute("""
            UPDATE customers SET email = :e, address = :a, phone = :p, gender = :g, dob = TO_DATE(:d, 'YYYY-MM-DD')
            WHERE id = :id
        """, {"e": email, "a": address, "p": phone, "g": gender, "d": dob, "id": customer_id})

        conn.commit()
        flash("Profile updated successfully.")
        return redirect(url_for('customer_dashboard'))

    else:
        cursor.execute("SELECT username, email, address, phone, gender, TO_CHAR(dob, 'YYYY-MM-DD') FROM customers WHERE id = :id", {"id": customer_id})
        user_data = cursor.fetchone()
        if not user_data:
            flash("User not found.")
            return redirect(url_for('customer_dashboard'))

        user = {
            "username": user_data[0],
            "email": user_data[1] or "",
            "address": user_data[2] or "",
            "phone": user_data[3] or "",
            "gender": user_data[4] or "",
            "dob": user_data[5] or ""
        }
        return render_template('update_profile.html', user=user)

# Change Password
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        cursor = get_cursor()
        cursor.execute("SELECT password FROM customers WHERE id = :id", {"id": session['customer_id']})
        user = cursor.fetchone()

        if not user or not check_password_hash(user[0], current_password):
            flash("Current password is incorrect")
            return redirect(url_for('change_password'))

        if new_password != confirm_password:
            flash("New passwords do not match")
            return redirect(url_for('change_password'))

        # Hash new password and update DB
        new_pw_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE customers SET password = :pw WHERE id = :id", {"pw": new_pw_hash, "id": session['customer_id']})
        conn.commit()

        # Redirect to success page after updating password
        return redirect(url_for('password_updated'))

    return render_template('change_password.html')
@app.route('/password_updated')
def password_updated():
    return render_template('password_updated.html')


# Admin Login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'adminpass':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid admin credentials")
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    cursor = get_cursor()
    cursor.execute("""
        SELECT a.id, c.username, a.first_name, a.last_name, a.status 
        FROM applications a 
        JOIN customers c ON a.customer_id = c.id
        ORDER BY a.id DESC
    """)
    applications = cursor.fetchall()
    return render_template('admin_dashboard.html', applications=applications)

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('home'))

# Check Application Status
@app.route('/check_status', methods=['GET', 'POST'])
def check_status():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))
    if request.method == 'POST':
        app_id = request.form['app_id']
        cursor = get_cursor()
        cursor.execute("SELECT status FROM applications WHERE id = :id", {"id": app_id})
        result = cursor.fetchone()
        if result:
            return render_template('status_result.html', app_id=app_id, status=result[0])
        else:
            flash("Application ID not found")
    return render_template('check_status.html')


# Update Application Status (Admin only)
@app.route('/update_status/<app_id>', methods=['GET', 'POST'])
def update_status(app_id):
    if not session.get('admin'):
        flash("Admin login required")
        return redirect(url_for('admin_login'))

    cursor = get_cursor()

    if request.method == 'POST':
        new_status = request.form['status']
        cursor.execute("UPDATE applications SET status = :s WHERE id = :id", {"s": new_status, "id": app_id})
        conn.commit()
        return render_template('status_updated.html', app_id=app_id)

    # GET method: fetch current status if you want (optional)
    cursor.execute("SELECT status FROM applications WHERE id = :id", {"id": app_id})
    current_status = cursor.fetchone()
    if not current_status:
        flash("Application not found")
        return redirect(url_for('admin_dashboard'))

    return render_template('update_status.html', app_id=app_id, current_status=current_status[0])


if __name__ == '__main__':
    app.run(debug=True)
