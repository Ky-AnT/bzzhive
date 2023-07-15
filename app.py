from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, url_for
import sqlite3
from config import SECRET_KEY
from markupsafe import Markup
import re

app = Flask(__name__)
app.secret_key = SECRET_KEY



def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('home.html')



@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        # Retrieve the form data
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and user['password'] == password:
            session['username'] = user['username']
            session['note'] = user['notes'] if user and 'notes' in user else ''

            conn.close()
            return redirect(url_for('dashboard'))
        else:
            conn.close()
            return render_template('signin.html', error='Invalid credentials')

    return render_template('signin.html', error='')





@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate username
        if not re.match(r'^(?=.*[A-Z])[A-Za-z]{8,15}$', username):
            error = 'Invalid username. It should have 8-15 letters and at least one capital letter.'
            return render_template('register.html', error=error)

        # Validate password
        if not re.match(r'^(?=.*[A-Z!])[A-Za-z0-9.!]{8,15}$', password):
            error = 'Invalid password. It should have 8-15 characters, at least one capital letter, and may contain letters, numbers, full stops, and exclamation marks.'
            return render_template('register.html', error=error)

        conn = get_db_connection()

        # Check if the username already exists in the database
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            error = 'Username already exists. Please choose a different username.'
            return render_template('register.html', error=error)

        # Insert the user into the database
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()

        session['username'] = username
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' in session:
        username = session['username']
        conn = get_db_connection()

        if request.method == 'POST':
            # Create a new document for the current user
            title = request.form['title'].strip()  # Remove leading/trailing whitespace
            content = ''  # Initial content for a new document

            # Set default title if empty or contains only whitespace
            if not title:
                title = 'Untitled Note'

            conn.execute('INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)', (username, title, content))
            conn.commit()

        # Retrieve personal notes for the current user from the database
        personal_notes = conn.execute('SELECT * FROM notes WHERE user_id = ? AND shared = 0', (username,)).fetchall()
        
        # Retrieve shared notes for the current user from the database
        shared_notes = conn.execute('''
            SELECT notes.*
            FROM notes
            JOIN shared_notes ON notes.id = shared_notes.note_id
            WHERE shared_notes.shared_with = ?
        ''', (username,)).fetchall()

        debug.debug()
        conn.close()

        return render_template('dashboard.html', username=username, personal_notes=personal_notes, shared_notes=shared_notes)
    else:
        return redirect(url_for('signin'))














@app.route('/note/<int:note_id>', methods=['GET', 'POST'])
def view_note(note_id):
    conn = get_db_connection()
    username = session.get('username')

    if request.method == 'POST':
        # Get the updated title and content from the form
        updated_title = request.form.get('title')
        updated_content = request.form.get('content')

        # Update the note title and content in the database if the note belongs to the user
        conn.execute('UPDATE notes SET title = ?, content = ? WHERE id = ? AND (user_id = ? OR shared = 1)',
                     (updated_title, updated_content, note_id, username))
        conn.commit()

        # Retrieve the shared users from the form
        shared_users = request.form.getlist('shared_with[]')

        # Remove existing shared users for the note
        conn.execute('DELETE FROM shared_notes WHERE note_id = ?', (note_id,))

        # Add the updated shared users to the shared_notes table
        for user in shared_users:
            conn.execute('INSERT INTO shared_notes (note_id, shared_with) VALUES (?, ?)', (note_id, user))
        conn.commit()

    # Retrieve the note from the database based on the note ID
    note = conn.execute('SELECT * FROM notes WHERE id = ? AND (user_id = ? OR shared = 1)', (note_id, username)).fetchone()

    # Retrieve the shared users for the note
    shared_users = conn.execute('SELECT shared_with FROM shared_notes WHERE note_id = ?', (note_id,)).fetchall()

    shared_with = [user['shared_with'] for user in shared_users] if shared_users else []

    # Check if the note exists and belongs to the user or is shared
    if note:
        conn.close()
        return render_template('note.html', note=note, shared_with=shared_with)
    else:
        conn.close()
        return abort(404)



def is_note_shared_with_user(note_id, username):
    conn = get_db_connection()
    note = conn.execute('SELECT * FROM notes WHERE id = ?', (note_id,)).fetchone()
    conn.close()

    if note:
        shared_users = note['shared_with']
        return username in shared_users.split(',') if shared_users else False

    return False

@app.route('/shared_note/<int:note_id>')
def view_shared_note(note_id):
    if 'username' in session:
        username = session['username']
        conn = get_db_connection()

        # Check if the note is shared with the current user
        shared_note = conn.execute('SELECT * FROM shared_notes WHERE note_id = ? AND shared_with = ?', (note_id, username)).fetchone()
        if shared_note:
            # Retrieve the shared note content from the database based on the note ID
            note = conn.execute('SELECT * FROM notes WHERE id = ?', (note_id,)).fetchone()
            conn.close()
            return render_template('note.html', note=note, shared_doc=True)

        conn.close()
        return abort(404)
    else:
        return redirect(url_for('signin'))







@app.route('/note/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    conn = get_db_connection()
    username = session.get('username')

    if request.method == 'POST':
        # Get the updated title and content from the form
        updated_title = request.form.get('title')
        updated_content = request.form.get('content')

        # Update the note title and content in the database if the note belongs to the user
        conn.execute('UPDATE notes SET title = ?, content = ? WHERE id = ? AND (user_id = ? OR shared = 1)',
                     (updated_title, updated_content, note_id, username))
        conn.commit()

    # Retrieve the note from the database based on the note ID
    note = conn.execute('SELECT * FROM notes WHERE id = ? AND (user_id = ? OR shared = 1)', (note_id, username)).fetchone()

    # Check if the note exists and belongs to the user or is shared
    if note:
        conn.close()
        return render_template('note.html', note=note)
    else:
        conn.close()
        return abort(404)




@app.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    conn = get_db_connection()

    # Delete the note from the database based on the note ID
    conn.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()

    conn.close()

    return redirect(url_for('dashboard'))  # Redirect back to the dashboard after deleting the note

@app.route('/share_note/<int:note_id>', methods=['POST'])
def share_note(note_id):
    conn = get_db_connection()

    # Retrieve the note from the database based on the note ID
    note = conn.execute('SELECT * FROM notes WHERE id = ?', (note_id,)).fetchone()

    if note:
        # Retrieve the username to share the note with
        shared_with = request.form['shared_with']

        # Check if the user exists in the database
        user = conn.execute('SELECT * FROM users WHERE username = ?', (shared_with,)).fetchone()

        if user:
            # Check if the note is already shared with the user
            existing_shared_note = conn.execute('SELECT * FROM shared_notes WHERE note_id = ? AND shared_with = ?', (note_id, shared_with)).fetchone()
            if not existing_shared_note:
                # Insert the shared note into the shared_notes table
                conn.execute('INSERT INTO shared_notes (note_id, shared_with) VALUES (?, ?)', (note_id, shared_with))
                conn.commit()
            conn.close()
            return redirect(url_for('view_note', note_id=note_id))
        else:
            conn.close()
            return redirect(url_for('view_note', note_id=note_id))
    else:
        conn.close()
        return render_template('404.html')




@app.route('/remove_shared_user/<int:note_id>', methods=['POST'])
def remove_shared_user(note_id):
    if 'username' in session:
        username = session['username']
        shared_with = request.form['username']

        conn = get_db_connection()

        # Check if the note exists and is shared by the current user
        note = conn.execute('SELECT * FROM notes WHERE id = ? AND (user_id = ? OR shared = 1)', (note_id, username)).fetchone()

        if note:
            # Remove the shared user from the shared_notes table
            conn.execute('DELETE FROM shared_notes WHERE note_id = ? AND shared_with = ?', (note_id, shared_with))
            conn.commit()

        conn.close()

    return redirect(url_for('view_note', note_id=note_id))




















@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404



@app.route('/signout')
def signout():
    session.pop('username', None)
    return redirect(url_for('signin'))

if __name__ == '__main__':
    app.run(debug=True)
