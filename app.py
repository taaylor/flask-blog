from turtle import title
from flask import Flask, request, render_template, flash, redirect, session
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
import yaml, os
from werkzeug.security import generate_password_hash, check_password_hash
import flask_wtf


app = Flask(__name__)
Bootstrap(app)

# DB configurate
db = yaml.full_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = os.urandom(30) 
mysql = MySQL(app)

@app.route('/')
def index():
    cursor = mysql.connection.cursor() 
    res = cursor.execute("SELECT * FROM blog")
    if res > 0:
        post = cursor.fetchall()
        cursor.close()
        return render_template('index.html', post=post)
    return render_template('index.html', post=None)


@app.route('/about/')
def about():
    return render_template('about.html')


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form_data = request.form
        if (form_data['password'] != form_data['confirm_password']):
            flash('Password do not match! Try again!', 'danger')
            return render_template('register.html')
        elif (form_data['first_name'].isalpha() == False) or (form_data['last_name'].isalpha() == False):
            flash('Invalid name format!', 'danger')
            return render_template('register.html')
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        psw = request.form['password']
        username = request.form['username']
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO user(first_name, last_name, username, email, password) VALUES(%s, %s, %s, %s, %s)",
        (first_name, last_name, username, email, generate_password_hash(psw)))
        mysql.connection.commit()
        cursor.close()
        flash('Registration successful! Please login!', 'success')
        return redirect('/login')
    return render_template('register.html')    


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        result_value = cursor.execute('SELECT * FROM user WHERE username=%s', ([username]))
        if result_value > 0:
            user = cursor.fetchone()
            if check_password_hash(user['password'], password):
                session['login'] = True
                session['first_name'] = user['first_name']
                session['last_name'] = user['last_name']
                flash(f"Welcome {session['first_name']}! You have been successfully logged in!", 'success')
            else:
                cursor.close()
                flash(f"This password is incorrect!", 'danger')
                return render_template('login.html')
        else:
            cursor.close()
            flash(f"User does not exist!", 'danger')    
            return render_template('login.html')  
        cursor.close()
        return redirect('/')
    return render_template('login.html')


@app.route('/blogs/<int:id>/')
def blogs(id):
    with mysql.connection.cursor() as cursor:
        res = cursor.execute("SELECT * FROM blog WHERE blog_id = {}".format(id))
        if res > 0:
            post = cursor.fetchone()
            return render_template('blogs.html', post=post)
    return 'Blog is not found'


@app.route('/write-blog/', methods=['GET', 'POST'])
def write_blog():
    if request.method == 'POST':
        blogpost = request.form
        title = blogpost['title']
        body = blogpost['body']
        author = session['first_name'] + ' ' + session['last_name']
        with mysql.connection.cursor() as cursor:
            cursor.execute("INSERT INTO blog(title, body, author) VALUES(%s, %s, %s)", (title, body, author))
            mysql.connection.commit()
        flash("Your blogpost is successfully posted!", 'success')  
        return redirect('/') 
    return render_template('write-blog.html')


@app.route('/my-blogs/')
def my_blogs():
    author = f"{session['first_name']} {session['last_name']}"
    with mysql.connection.cursor() as cursor:
        result_val = cursor.execute(" SELECT * FROM blog WHERE author = %s", ([author]))
        if result_val > 0:
            my_blogs = cursor.fetchall()
            return render_template('my-blogs.html', my_blogs=my_blogs)
        else:            
            return render_template('my-blogs.html', my_blogs=None)
    

@app.route('/edit-blog/<int:id>', methods=['GET', 'POST'])
def edit_blog(id):
    if request.method == 'POST':
        with mysql.connection.cursor() as cursor:
            title = request.form['title']
            body = request.form['body']
            cursor.execute("UPDATE blog SET title = %s, body = %s WHERE blog_id = %s", (title, body, id) )
            mysql.connection.commit()
        flash('Blog is updated successfully!', 'success')
        return redirect('/blogs/{}'.format(id))
    with mysql.connection.cursor() as cursor:
        res_val = cursor.execute("SELECT * FROM blog WHERE blog_id={}".format(id))
        if res_val > 0:
            blog = cursor.fetchone()
            blog_form = {}
            blog_form['title'] = blog['title']
            blog_form['body'] = blog['body']
            return render_template('edit-blog.html', blog_form = blog_form)


@app.route('/delete-blog/<int:id>/')
def delete_blog(id):
    with mysql.connection.cursor() as cursor:
        cursor.execute("DELETE FROM blog WHERE blog_id = {}".format(id))
        mysql.connection.commit()
        flash('Success delete', 'success')
        return redirect('/my-blogs')
    

@app.route('/logout/')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)