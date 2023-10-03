import os
from flask import Flask, flash, render_template, request, redirect, url_for
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from data_models import db, Author, Book


app = Flask(__name__)
db_dir = os.path.join(app.root_path, 'data')
os.makedirs(db_dir, exist_ok=True)
db_file_path = os.path.join(db_dir, 'library.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_file_path}'

db.init_app(app)


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        author_name = request.form.get('name')
        birth = request.form.get('birth_date')
        death_date = request.form.get('date_of_death')

        if not author_name or not birth:
            # Handle missing name or birth date
            error_message = 'Please provide both name and birth date.'
            return render_template('add_author.html', error_message=error_message)

        try:
            birth_date = datetime.strptime(birth, '%Y-%m-%d').date()
        except ValueError:
            error_message = 'Invalid birth date format. Please use YYYY-MM-DD format for dates.'
            return render_template('add_author.html', error_message=error_message)

        date_of_death = None
        if death_date:
            try:
                date_of_death = datetime.strptime(death_date, '%Y-%m-%d').date()
            except ValueError:
                error_message = 'Invalid date of death format. Please use YYYY-MM-DD format for dates.'
                return render_template('add_author.html', error_message=error_message)

        try:
            new_author = Author(name=author_name, birth_date=birth_date, date_of_death=date_of_death)
            db.session.add(new_author)
            db.session.commit()
            return render_template('add_author.html', message='Author added successfully!')

        except SQLAlchemyError as e:
            # Handle database-related errors
            error_message = 'An unexpected error occurred. Please try again later.'
            return render_template('add_author.html', error_message=error_message)

    return render_template('add_author.html')


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    authors = Author.query.all()

    if request.method == 'POST':
        isbn = request.form.get('isbn')
        title = request.form.get('title')
        publication_year = request.form.get('publication_year')
        author_id = request.form.get('author_id')

        if not isbn or not title or not publication_year or not author_id:
            error_message = 'Please provide all required fields.'
            return render_template('add_book.html', error_message=error_message, authors=authors)

        if not publication_year.isdigit() or len(publication_year) != 4:
            error_message = 'Invalid publication year format. Please provide a valid year.'
            return render_template('add_book.html', error_message=error_message, authors=authors)

        publication_year = int(publication_year)

        try:
            # Create a new Book record in the database
            new_book = Book(isbn=isbn, title=title, publication_year=publication_year, author_id=author_id)
            db.session.add(new_book)
            db.session.commit()

            return render_template('add_book.html', message='Book added successfully!', authors=authors)

        except SQLAlchemyError as e:
            # Handle database-related errors
            error_message = 'An unexpected error occurred. Please try again later.'
            return render_template('add_book.html', error_message=error_message, authors=authors)

    return render_template('add_book.html', authors=authors)


@app.route('/home', methods=['GET', 'POST'])
def home():
    # Get the sorting parameter from the form or use a default value
    sort_by = request.args.get('sort', default='title')
    search_query = request.form.get('search_query', default='')

    # Initialize the base query
    base_query = Book.query

    # Determine the sorting criteria based on user choice
    if sort_by == 'author':
        # Sort by author's name by joining Author table
        base_query = base_query.join(Author).order_by(Author.name)
    else:
        # Sort by title
        base_query = base_query.order_by(Book.title)

    # Perform a search query based on the input (if search_query is provided)
    if search_query:
        books = (
            base_query
            .filter(or_(Book.title.ilike(f'%{search_query}%'),
                        Author.name.ilike(f'%{search_query}%')))
            .all()
        )
        message = f'Search results for "{search_query}":' if books else 'No books found that match the search criteria.'
    else:
        # No search query provided, use the base query for sorting
        books = base_query.all()
        message = 'All books:'

    return render_template('home.html', books=books, message=message)


@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    if request.method == 'POST':
        book = Book.query.get_or_404(book_id)
        if not book:
            return redirect(url_for('home'))

        author = Author.query.get(book.author_id)
        try:
            # Delete the book from the database
            db.session.delete(book)

            # Check if the author has any other books in the library
            other_books_by_author = Book.query.filter_by(author_id=author.id).filter(Book.id != book_id).count()

            if other_books_by_author == 0:
                # If the author has no other books, delete the author from the database
                db.session.delete(author)

            db.session.commit()

            return redirect(url_for('home'))

        except SQLAlchemyError as e:
            # Handle database-related errors
            db.session.rollback()  # Roll back the transaction
            error_message = 'An unexpected error occurred while accessing the database. Please try again later.'
            app.logger.exception(e)
            flash(error_message, 'error')
            return redirect(url_for('home'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message="Page not found"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_message="Internal Server Error"), 500


@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', error_code=403, error_message="Forbidden"), 403


if __name__ == '__main__':
    app.run(debug=True)

# with app.app_context():
#     db.create_all()
