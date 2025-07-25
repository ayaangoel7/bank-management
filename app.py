from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DATABASE = 'bank.db'


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed = generate_password_hash(password)

        db = get_db()
        cur = db.cursor()
        cur.execute('SELECT * FROM users WHERE email = ?', (email,))
        if cur.fetchone():
            flash("Email already registered", "error")
            return redirect(url_for('register'))

        cur.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, hashed))
        db.commit()
        db.close()
        flash("Account created successfully. Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']
        password = request.form['password']

        db = get_db()
        cur = db.cursor()
        cur.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cur.fetchone()
        db.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash("Login successful", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password", "error")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cur = db.cursor()

    # Get user info
    cur.execute('SELECT name, email, id FROM users WHERE id = ?', (session['user_id'],))
    user = cur.fetchone()

    # Compute balance from transactions
    cur.execute('''
        SELECT
            SUM(CASE
                WHEN type = "deposit" THEN amount
                WHEN type = "received" THEN amount
                WHEN type = "withdraw" THEN -amount
                WHEN type = "transfer" THEN -amount
                ELSE 0
            END) AS balance
        FROM transactions
        WHERE user_id = ?
    ''', (session['user_id'],))
    result = cur.fetchone()
    balance = result['balance'] if result['balance'] is not None else 0.0

    db.close()
    return render_template('dashboard.html', user=user, balance=balance)

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        amount = float(request.form['amount'])
        if amount <= 0:
            flash("Amount must be greater than zero", "error")
            return redirect(url_for('deposit'))

        db = get_db()
        cur = db.cursor()
        cur.execute('INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)', (session['user_id'], 'deposit', amount))
        db.commit()
        db.close()
        flash("Deposit successful", "success")
        return redirect(url_for('dashboard'))

    return render_template('deposit.html')


@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        amount = float(request.form['amount'])

        db = get_db()
        cur = db.cursor()
        cur.execute('''
            SELECT
                SUM(CASE
                    WHEN type = "deposit" THEN amount
                    WHEN type = "received" THEN amount
                    WHEN type = "withdraw" THEN -amount
                    WHEN type = "transfer" THEN -amount
                    ELSE 0
                END) AS balance
            FROM transactions
            WHERE user_id = ?
        ''', (session['user_id'],))
        balance = cur.fetchone()['balance'] or 0.0

        if amount <= 0:
            flash("Amount must be greater than zero", "error")
        elif amount > balance:
            flash("Insufficient funds", "error")
        else:
            cur.execute('INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)', (session['user_id'], 'withdraw', amount))
            db.commit()
            flash("Withdrawal successful", "success")

        db.close()
        return redirect(url_for('dashboard'))

    return render_template('withdraw.html')


@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        recipient_id = int(request.form['recipient_id'])
        amount = float(request.form['amount'])

        if recipient_id == session['user_id']:
            flash("Cannot transfer to yourself", "error")
            return redirect(url_for('transfer'))

        db = get_db()
        cur = db.cursor()

        # Get current balance
        cur.execute('''
            SELECT
                SUM(CASE
                    WHEN type = "deposit" THEN amount
                    WHEN type = "received" THEN amount
                    WHEN type = "withdraw" THEN -amount
                    WHEN type = "transfer" THEN -amount
                    ELSE 0
                END) AS balance
            FROM transactions
            WHERE user_id = ?
        ''', (session['user_id'],))
        result = cur.fetchone()
        balance = result['balance'] if result['balance'] is not None else 0.0

        # Check recipient exists
        cur.execute('SELECT * FROM users WHERE id = ?', (recipient_id,))
        recipient = cur.fetchone()

        if not recipient:
            flash("Recipient not found", "error")
        elif amount <= 0:
            flash("Amount must be greater than zero", "error")
        elif amount > balance:
            flash("Insufficient funds", "error")
        else:
            cur.execute('INSERT INTO transactions (user_id, type, amount, recipient_id) VALUES (?, "transfer", ?, ?)', (session['user_id'], amount, recipient_id))
            cur.execute('INSERT INTO transactions (user_id, type, amount, recipient_id) VALUES (?, "received", ?, ?)', (recipient_id, amount, session['user_id']))
            db.commit()
            flash("Transfer successful", "success")

        db.close()
        return redirect(url_for('dashboard'))

    return render_template('transfer.html')



@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT type, amount, recipient_id, timestamp FROM transactions WHERE user_id = ? ORDER BY timestamp DESC', (session['user_id'],))
    transactions = cur.fetchall()
    db.close()

    return render_template('history.html', transactions=transactions)


if __name__ == '__main__':
    app.run(debug=True)
