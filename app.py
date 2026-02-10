import os
import random
from datetime import datetime

from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, join_room, leave_room, emit
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Room


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'

db.init_app(app)

socketio = SocketIO(app)

LOG_DIR = "logs"


# ---------------- INIT ----------------

with app.app_context():
    db.create_all()

if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)


# ---------------- HELPERS ----------------

def random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))


def write_log(room, user, text):
    filename = f"{LOG_DIR}/{room}.log"

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"[{time}] {user}: {text}\n")


# ---------------- AUTH ----------------

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        # Реєстрація
        if not user:

            hash_pw = generate_password_hash(password)

            user = User(
                username=username,
                password_hash=hash_pw
            )

            db.session.add(user)
            db.session.commit()

        # Вхід
        else:
            if not check_password_hash(user.password_hash, password):
                return "Wrong password!"

        session["user"] = username
        session["color"] = random_color()

        return redirect("/chat")

    return render_template("login.html")


# ---------------- CHAT ----------------

@app.route("/chat")
def chat():

    if "user" not in session:
        return redirect("/")

    rooms = Room.query.all()

    return render_template(
        "chat.html",
        user=session["user"],
        color=session["color"],
        rooms=rooms
    )


@app.route("/create_room", methods=["POST"])
def create_room():

    name = request.form["name"]
    owner = session["user"]

    user = User.query.filter_by(username=owner).first()

    room = Room(
        name=name,
        owner_id=user.id
    )

    room.users.append(user)

    db.session.add(room)
    db.session.commit()

    return redirect("/chat")


@app.route("/invite", methods=["POST"])
def invite():

    room_id = request.form["room"]
    username = request.form["user"]

    room = Room.query.get(room_id)
    user = User.query.filter_by(username=username).first()

    if user:
        room.users.append(user)
        db.session.commit()

    return redirect("/chat")


# ---------------- SOCKET ----------------

@socketio.on("join")
def on_join(data):

    room = data["room"]
    user = session["user"]

    join_room(room)

    emit(
        "message",
        {
            "user": "SYSTEM",
            "text": f"{user} joined",
            "color": "#888"
        },
        room=room
    )


@socketio.on("leave")
def on_leave(data):

    room = data["room"]
    user = session["user"]

    leave_room(room)

    emit(
        "message",
        {
            "user": "SYSTEM",
            "text": f"{user} left",
            "color": "#888"
        },
        room=room
    )


@socketio.on("send")
def send_message(data):

    room = data["room"]
    text = data["text"]

    user = session["user"]
    color = session["color"]

    write_log(room, user, text)

    emit(
        "message",
        {
            "user": user,
            "text": text,
            "color": color
        },
        room=room
    )


# ---------------- RUN ----------------

if __name__ == "__main__":
    socketio.run(app, debug=True)
