import socket
import threading
import json

HOST = "127.0.0.1"
PORT = 12345

running = True


def send_json(client_socket, message):
    """
    Sends a JSON message followed by a newline.
    """
    data = json.dumps(message) + "\n"
    client_socket.sendall(data.encode("utf-8"))


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


def listen_for_messages(client_socket):
    """
    Continuously listens for incoming messages from the server.
    Note: this runs in a separate thread.
    """
    global running

    while running:
        try:
            message = receive_json(client_socket)

            if message is None:
                print("\nDisconnected from server.")
                running = False
                break

            message_type = message.get("type")

            if message_type == "broadcast":
                print(f"\n[Public] {message.get('from')}: {message.get('message')}")

            elif message_type == "direct":
                print(f"\n[DM from {message.get('from')}] {message.get('message')}")

            elif message_type == "active_users":
                users = ", ".join(message.get("users", []))
                print(f"\n[Active Users] {users}")

            elif message_type == "login_success":
                print(f"\n{message.get('message')}")
                users = ", ".join(message.get("active_users", []))
                print(f"[Active Users] {users}")

            elif message_type == "info":
                print(f"\n[Info] {message.get('message')}")

            elif message_type == "error":
                print(f"\n[Error] {message.get('message')}")

            else:
                print(f"\n[Server] {message}")

        except OSError:
            running = False
            break

        except json.JSONDecodeError:
            print("\nReceived invalid JSON from server.")

        print("\nEnter operation: PM, DM, or EX")


def handle_user_input(client_socket):
    """
    Handles user commands.
    Note: This runs in a separate thread.
    """
    global running

    while running:
        operation = input("Enter operation: PM, DM, or EX: ").strip().upper()

        if operation == "PM":
            text = input("Enter public message: ").strip()

            message = {
                "command": "PM",
                "message": text
            }

            send_json(client_socket, message)

        elif operation == "DM":
            target_user = input("Enter username to message: ").strip()
            text = input("Enter direct message: ").strip()

            message = {
                "command": "DM",
                "to": target_user,
                "message": text
            }

            send_json(client_socket, message)

        elif operation == "EX":
            message = {
                "command": "EX"
            }

            send_json(client_socket, message)
            running = False
            break

        else:
            print("Invalid operation. Please enter PM, DM, or EX.")

    client_socket.close()


def login(client_socket):
    """
    Prompts the user for username and password.
    Sends login request to the server.
    """
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    login_message = {
        "command": "login",
        "username": username,
        "password": password
    }

    send_json(client_socket, login_message)


def start_client():
    """
    Starts the client and connects to the server.
    """
    global running

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((HOST, PORT))
        print(f"Connected to server at {HOST}:{PORT}")

        login(client_socket)

        listener_thread = threading.Thread(
            target=listen_for_messages,
            args=(client_socket,)
        )

        input_thread = threading.Thread(
            target=handle_user_input,
            args=(client_socket,)
        )

        listener_thread.daemon = True
        input_thread.daemon = True

        listener_thread.start()
        input_thread.start()

        input_thread.join()

    except ConnectionRefusedError:
        print("Could not connect to server. Make sure the server is running.")

    except OSError:
        print("Connection closed.")

    finally:
        running = False
        client_socket.close()


if __name__ == "__main__":
    start_client()