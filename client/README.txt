Online Chat Room Client

How to Run:
1. Make sure the server is running first.
2. Open client/client.py
3. Run client.py.
4. Enter a username and password.

Operations:
PM - Send a public message to all users.
DM - Send a direct message to one user.
EX - Exit the chat.

Testing Multiple Clients:

To test multiple clients, the server must be running first. After starting the server, open multiple separate terminals,
command prompts, or IDE run windows and run the client program in each one.

Using a terminal or command prompt:

1. Open a terminal or command prompt.

2. Navigate to the project folder.

3. Run the client:

   python client/client.py

4. Open a second terminal or command prompt.

5. Run the same command again:

   python client/client.py

Each running client represents a different user connected to the chat room.

Using PyCharm:

1. Run server.py first.
2. Open client.py.
3. Enable "Allow multiple instances" in the client run configuration.
4. Run client.py multiple times to simulate different users.

Example Test Users:

Client 1:
Username: alice
Password: pass123

Client 2:
Username: bob
Password: pass456

After both clients are connected, test:

* PM to send a public message.
* DM to send a direct message to another active user.
* EX to exit the chat room.
