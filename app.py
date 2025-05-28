from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

# Database connection
db = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="chinni",
    password="aalokhya8",
    database="microdebt"
)

cursor = db.cursor(dictionary=True)

@app.route('/')
def index():
    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()
    return render_template("index.html", users=users)

@app.route('/add-user', methods=['POST'])
def add_user():
    name = request.form['name'].strip()
    if name:
        cursor.execute("INSERT INTO Users (name) VALUES (%s)", (name,))
        db.commit()
    return redirect('/')

@app.route('/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    # Delete splits related to expenses paid by this user
    cursor.execute("""
        DELETE s FROM Splits s
        JOIN Expenses e ON s.expense_id = e.expense_id
        WHERE e.paid_by = %s
    """, (user_id,))

    # Delete expenses paid by this user
    cursor.execute("DELETE FROM Expenses WHERE paid_by = %s", (user_id,))

    # Delete splits where user is involved
    cursor.execute("DELETE FROM Splits WHERE user_id = %s", (user_id,))

    # Finally, delete the user
    cursor.execute("DELETE FROM Users WHERE user_id = %s", (user_id,))

    db.commit()
    return redirect('/')

@app.route('/expenses')
def expenses():
    cursor.execute("SELECT * FROM Users")
    users = cursor.fetchall()
    return render_template("expenses.html", users=users)

@app.route('/add-expense', methods=['POST'])
def add_expense():
    description = request.form['description']
    amount = float(request.form['amount'])
    paid_by = int(request.form['paid_by'])
    involved_users = request.form.getlist('involved_users')

    cursor.execute("INSERT INTO Expenses (description, amount, paid_by) VALUES (%s, %s, %s)",
                   (description, amount, paid_by))
    expense_id = cursor.lastrowid

    share_per_user = round(amount / len(involved_users), 2)
    for user_id in involved_users:
        cursor.execute("INSERT INTO Splits (expense_id, user_id, share) VALUES (%s, %s, %s)",
                       (expense_id, int(user_id), share_per_user))

    db.commit()
    return redirect('/expenses')

@app.route('/balances')
def balances():
    cursor.execute("""
        SELECT
            u1.name AS lender,
            u2.name AS borrower,
            SUM(s.share) AS amount_owed
        FROM Expenses e
        JOIN Splits s ON e.expense_id = s.expense_id
        JOIN Users u1 ON e.paid_by = u1.user_id
        JOIN Users u2 ON s.user_id = u2.user_id
        WHERE e.paid_by != s.user_id
        GROUP BY e.paid_by, s.user_id
        ORDER BY lender, borrower
    """)
    balances = cursor.fetchall()
    return render_template("balance.html", balances=balances)

@app.route('/summary')
def summary():
    cursor.execute("""
        SELECT
            u.user_id,
            u.name,
            IFNULL(paid.total_paid,0) AS total_paid,
            IFNULL(owed.total_owed,0) AS total_owed,
            (IFNULL(paid.total_paid,0) - IFNULL(owed.total_owed,0)) AS net_balance
        FROM Users u
        LEFT JOIN (
            SELECT paid_by, SUM(amount) AS total_paid
            FROM Expenses
            GROUP BY paid_by
        ) paid ON u.user_id = paid.paid_by
        LEFT JOIN (
            SELECT s.user_id, SUM(s.share) AS total_owed
            FROM Splits s
            GROUP BY s.user_id
        ) owed ON u.user_id = owed.user_id
        ORDER BY net_balance DESC
    """)
    summary = cursor.fetchall()
    return render_template("summary.html", summary=summary)

@app.route('/edit-summary/<int:user_id>', methods=['GET', 'POST'])
def edit_summary(user_id):
    if request.method == 'POST':
        new_name = request.form['name'].strip()
        if new_name:
            cursor.execute("UPDATE Users SET name = %s WHERE user_id = %s", (new_name, user_id))
            db.commit()
        return redirect('/summary')
    else:
        cursor.execute("SELECT * FROM Users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return redirect('/summary')
        return render_template('edit_summary.html', user=user)

@app.route('/user-expenses/<int:user_id>')
def user_expenses(user_id):
    cursor.execute("SELECT * FROM Users WHERE user_id=%s", (user_id,))
    user = cursor.fetchone()
    if not user:
        return redirect('/summary')

    cursor.execute("""
        SELECT e.expense_id, e.description, e.amount
        FROM Expenses e
        WHERE e.paid_by = %s
        ORDER BY e.expense_id DESC
    """, (user_id,))
    expenses = cursor.fetchall()

    return render_template('user_expenses.html', user=user, expenses=expenses)

@app.route('/edit-expense/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        paid_by = int(request.form['paid_by'])
        involved_users = request.form.getlist('involved_users')

        cursor.execute("UPDATE Expenses SET description=%s, amount=%s, paid_by=%s WHERE expense_id=%s",
                       (description, amount, paid_by, expense_id))
        cursor.execute("DELETE FROM Splits WHERE expense_id=%s", (expense_id,))

        share_per_user = round(amount / len(involved_users), 2)
        for user_id in involved_users:
            cursor.execute("INSERT INTO Splits (expense_id, user_id, share) VALUES (%s, %s, %s)",
                           (expense_id, int(user_id), share_per_user))

        db.commit()
        return redirect('/expenses')
    else:
        cursor.execute("SELECT * FROM Expenses WHERE expense_id=%s", (expense_id,))
        expense = cursor.fetchone()
        if not expense:
            return redirect('/expenses')

        cursor.execute("SELECT * FROM Users")
        users = cursor.fetchall()

        cursor.execute("SELECT user_id FROM Splits WHERE expense_id=%s", (expense_id,))
        involved = cursor.fetchall()
        involved_user_ids = [u['user_id'] for u in involved]

        return render_template('edit_expense.html', expense=expense, users=users, involved_user_ids=involved_user_ids)

if __name__ == '__main__':
    app.run(debug=True)
