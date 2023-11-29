from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO

app = Flask(__name__)
app.config["SECRET_KEY"] = "FioraKing"
socketio = SocketIO(app)

# Usar codigo fixo para a sala
fixed_room_code = "your_fixed_room_code"
rooms = {fixed_room_code: {"members": 0, "messages": []}}

# Update da rota para redirecionar para a sala
@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        name = request.form.get("name")

        if not name:
            return render_template("home.html", error="Porfavor Adiciona Nome.")

        session["room"] = fixed_room_code
        session["name"] = name
        return redirect(url_for("room"))

    # verificar se o nome e a sala estão na sessão
    if "name" in session and "room" in session:
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    name = session.get("name")
    if room is None or name is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return

    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect():
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return

    join_room(room)
    send({"name": name, "message": "entrou na sala"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

# Update da rota para sair da sala
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    send({"name": name, "message": "saiu da sala"}, to=room)
    leave_room(room)
    print(f"{name} has left the room {room}")

    # apagar a sessão
    session.pop("room", None)
    session.pop("name", None)


@app.route("/leave_session", methods=["POST"])
def leave_session():
    session.clear()
    return redirect(url_for("home"))



if __name__ == "__main__":
    socketio.run(app, debug=True)
