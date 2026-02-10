from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


room_users = db.Table(
    'room_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('room_id', db.Integer, db.ForeignKey('room.id'))
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(200))


class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    owner_id = db.Column(db.Integer)

    users = db.relationship(
        'User',
        secondary=room_users,
        backref='rooms'
    )
