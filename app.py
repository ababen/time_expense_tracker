
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import TimeEntry, ExpenseEntry, Client, User
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from forms import RegistrationForm, LoginForm
from werkzeug.middleware.proxy_fix import ProxyFix
from db import db
import os, psycopg2

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
# app.config['SQLALCHEMY_DATABASE_URI'] =  'postgresql+psycopg2://expenseuser:Z0CWXZJG17Wgzwmo1xBm@localhost/time_expense_tracker_db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tracker.db'  # SQLite database
db.init_app(app)
migrate = Migrate(app, db)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirects to the login page if not authenticated

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    time_entries = TimeEntry.query.order_by(TimeEntry.date.desc()).all()
    expense_entries = ExpenseEntry.query.order_by(ExpenseEntry.date.desc()).all()
    return render_template('index.html', time_entries=time_entries, expense_entries=expense_entries)

@app.route('/add_time', methods=['GET', 'POST'])
@login_required
def add_time():
    clients = Client.query.all()
    if request.method == 'POST':
        task = request.form['task']
        duration = request.form['duration']
        date = request.form['date']
        client_id = request.form['client_id']
        new_entry = TimeEntry(
            task=task,
            duration=duration,
            date=datetime.strptime(date, '%Y-%m-%d'),
            client_id=client_id
        )
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_time.html', clients=clients)

@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    clients = Client.query.all()
    if request.method == 'POST':
        item = request.form['item']
        amount = request.form['amount']
        date = request.form['date']
        client_id = request.form['client_id']
        new_expense = ExpenseEntry(
            item=item,
            amount=amount,
            date=datetime.strptime(date, '%Y-%m-%d'),
            client_id=client_id
        )
        db.session.add(new_expense)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_expense.html', clients=clients)

@app.route('/add_client', methods=['GET', 'POST'])
@login_required
def add_client():
    if request.method == 'POST':
        name = request.form['name']
        new_client = Client(name=name)
        db.session.add(new_client)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_client.html')

@app.route('/clients')
@login_required
def clients():
    clients = Client.query.order_by(Client.name).all()
    return render_template('clients.html', clients=clients)

@app.route('/client/<int:client_id>')
@login_required
def view_client_details(client_id):
    client = Client.query.get_or_404(client_id)
    time_entries = TimeEntry.query.filter_by(client_id=client_id).order_by(TimeEntry.date.desc()).all()
    expense_entries = ExpenseEntry.query.filter_by(client_id=client_id).order_by(ExpenseEntry.date.desc()).all()
    return render_template('client_details.html', client=client, time_entries=time_entries, expense_entries=expense_entries)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
