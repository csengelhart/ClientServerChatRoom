import socket
import threading
import json
import os

HOST = "127.0.0.1"
PORT =  12345
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")

active_clients = {}
clients_lock = threading.Lock()
users_lock = threading.Lock()


def load_users():
    """
    Loads registered users from users.json.
    If the file does not exist, create an empty dictionary.
    """
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as file:
            json.dump({}, file)

    with open(USERS_FILE, "r") as file:
        return json.load(file)

def save_users(users):
    """
    Saves the users dictionary to users.json.
    """
    with open(USERS_FILE, "w") as file:
        json.dump(users, file, indent=4)

def send_json(client_socket, message):
    """
    Sends a JSON message followed by a newline.
    TCP doesn't know where the JSON message ends, newline is used as a mark for end of message.
    """
    try:
        data = json.dumps(message) + "\n"
        client_socket.sendall(data.encode("utf-8"))
    except OSError:
        pass

def receive_json(client_socket):
    """
    Receives one JSON message from the socket.
    Reads until it sees a newline.
    """
    buffer = ""

    while True:
        data = client_socket.recv(1024)

        if not data:
            return None

        buffer += data.decode("utf-8")

        if "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            return json.loads(line)

def broadcast(message, exclude_username=None):
    """
    Sends a message to all active clients.
    argument included to exclude one user, intended to exclude the sender.
    """
    with clients_lock:
        for username, client_socket in active_clients.items():
            if username != exclude_username:
                send_json(client_socket, message)


def send_active_users_update():
    """
    Sends the current active user list to all connected clients.
    """
    with clients_lock:
        users = list(active_clients.keys())

    update_message = {
        "type": "active_users",
        "users": users
    }

    broadcast(update_message)


def handle_login(client_socket):
    """
    Handles the login and registration process.
    A new username is automatically registered.
    Existing usernames must provide the correct password.
    """
    login_message = receive_json(client_socket)

    if login_message is None:
        return None

    if login_message.get("command") != "login":
        send_json(client_socket, {
            "type": "error",
            "message": "First message must be a login command."
        })
        return None

    username = login_message.get("username")
    password = login_message.get("password")

    if not username or not password:
        send_json(client_socket, {
            "type": "error",
            "message": "Username and password are required."
        })
        return None

    with users_lock:
        users = load_users()

        if username in users:
            if users[username] != password:
                send_json(client_socket, {
                    "type": "error",
                    "message": "Invalid password."
                })
                return None
        else:
            users[username] = password
            save_users(users)

    with clients_lock:
        if username in active_clients:
            send_json(client_socket, {
                "type": "error",
                "message": "This user is already logged in."
            })
            return None

        active_clients[username] = client_socket

    send_json(client_socket, {
        "type": "login_success",
        "message": f"Welcome, {username}!",
        "active_users": list(active_clients.keys())
    })

    print(f"{username} logged in.")

    send_active_users_update()

    return username

def handle_client(client_socket, client_address):
    """
    Handles one connected client.
    This function runs inside its own thread.
    """
    username = None

    try:
        username = handle_login(client_socket)

        if username is None:
            client_socket.close()
            return

        while True:
            message = receive_json(client_socket)

            if message is None:
                break

            command = message.get("command")

            if command == "PM":
                text = message.get("message", "")

                if not text:
                    send_json(client_socket, {
                        "type": "error",
                        "message": "Public message cannot be empty."
                    })
                    continue

                broadcast_message = {
                    "type": "broadcast",
                    "from": username,
                    "message": text
                }

                broadcast(broadcast_message, exclude_username=username)

                send_json(client_socket, {
                    "type": "info",
                    "message": "Public message sent."
                })

            elif command == "DM":
                target_user = message.get("to")
                text = message.get("message", "")

                if not target_user or not text:
                    send_json(client_socket, {
                        "type": "error",
                        "message": "Direct message requires a target user and message."
                    })
                    continue

                with clients_lock:
                    target_socket = active_clients.get(target_user)

                if target_socket is None:
                    send_json(client_socket, {
                        "type": "error",
                        "message": f"User '{target_user}' is not online."
                    })
                    continue

                direct_message = {
                    "type": "direct",
                    "from": username,
                    "message": text
                }

                send_json(target_socket, direct_message)

                send_json(client_socket, {
                    "type": "info",
                    "message": f"Direct message sent to {target_user}."
                })

            elif command == "EX":
                send_json(client_socket, {
                    "type": "info",
                    "message": "Goodbye!"
                })
                break

            else:
                send_json(client_socket, {
                    "type": "error",
                    "message": "Invalid command. Use PM, DM, or EX."
                })

    except ConnectionResetError:
        print(f"Connection reset by {client_address}")

    except json.JSONDecodeError:
        print(f"Invalid JSON received from {client_address}")

    finally:
        if username:
            with clients_lock:
                active_clients.pop(username, None)

            print(f"{username} logged out.")
            send_active_users_update()

        client_socket.close()


def start_server():
    """
    Starts the TCP server.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"Server running on {HOST}:{PORT}")
    print("Waiting for clients...")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"New connection from {client_address}")

        client_thread = threading.Thread(
            target=handle_client,
            args=(client_socket, client_address)
        )

        client_thread.daemon = True
        client_thread.start()


if __name__ == "__main__":
    start_server()