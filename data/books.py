import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Books(SqlAlchemyBase):
    __tablename__ = 'all_books'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    who_added = sqlalchemy.Column(sqlalchemy.Integer,
                                  sqlalchemy.ForeignKey("users.id"))
    name = sqlalchemy.Column(sqlalchemy.String)
    author = sqlalchemy.Column(sqlalchemy.String)
    categories = sqlalchemy.Column(sqlalchemy.String)
    content = sqlalchemy.Column(sqlalchemy.String)
    users = orm.relation('User', back_populates='books')
