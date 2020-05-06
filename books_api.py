import flask
from data import db_session, books
from flask import jsonify

blueprint = flask.Blueprint('news_api', __name__,
                            template_folder='templates')


@blueprint.route('/api/books/<int:books_id>',  methods=['GET'])
def get_one_book(books_id):
    session = db_session.create_session()
    book = session.query(books.Books).get(books_id)
    if not book:
        return jsonify({'error': 'Not found'})
    return jsonify(
        {
            'book': book.to_dict(only=('name', 'author', 'content'))
        }
    )
