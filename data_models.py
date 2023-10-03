from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    birth_date = db.Column(db.Date)
    date_of_death = db.Column(db.Date)

    def __repr__(self):
        return f"<Author(id={self.id}, name='{self.name}')>"

    def __str__(self):
        return f"name = {self.name}"


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(13))
    title = db.Column(db.String(200))
    publication_year = db.Column(db.Integer)

    # Define the foreign key relationship
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))

    # Define a back reference to the Author model
    author = db.relationship('Author', backref='books')

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', author_id={self.author_id})>"

    def __str__(self):
        return f"Title: {self.title}, ISBN: {self.isbn}, Published: {self.publication_year}"
