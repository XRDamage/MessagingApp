import socket
import threading

# Create a socket object
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Get local machine name
host = socket.gethostname()

# Set port number
port = 9999

server.bind((host, port))
server.listen()

clients = {}
nicknames = {}
chat_rooms = {}  # Dictionary to track private chat rooms

def broadcast(message):
    for client in clients:
        client.send(message)

def handle(client):
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message.startswith('@'):
                recipient, message = message[1:].split(':', 1)
                recipient_client = nicknames.get(recipient)
                if recipient_client:
                    recipient_client.send(f"@{nicknames[client]}: {message}".encode('utf-8'))
            elif message == '/online':
                online_users = ', '.join(nicknames.values())
                client.send(f"Online users: {online_users}".encode('utf-8'))
            elif message.startswith('@start_individual_chat'):
                recipient = message.replace('@start_individual_chat:', '', 1)
                recipient_client = nicknames.get(recipient)
                if recipient_client:
                    chat_room_id = f"{nicknames[client]}_{nicknames[recipient_client]}"
                    chat_rooms[chat_room_id] = [client, recipient_client]
                    recipient_client.send(f"@{nicknames[client]}: Private chat started.".encode('utf-8'))
                    client.send(f"@{recipient}: Private chat started.".encode('utf-8'))
                    # Continue handling individual chat between the two clients
                    handle_individual_chat(client, recipient_client, chat_room_id)
            else:
                broadcast(f"{nicknames[client]}: {message}".encode('utf-8'))
        except:
            del clients[client]
            nickname = nicknames[client]
            del nicknames[client]
            broadcast(f'{nickname} left the chat!\n'.encode('utf-8'))
            print(f'Lost connection with {nickname}')
            break

def handle_individual_chat(sender, recipient, chat_room_id):
    while True:
        try:
            message = sender.recv(1024).decode('utf-8')
            if message.startswith('@individual_chat:') and chat_room_id in chat_rooms:
                recipient_message = message.split(':', 1)[1]
                for participant in chat_rooms[chat_room_id]:
                    participant.send(f"@{nicknames[sender]}: {recipient_message}".encode('utf-8'))
            else:
                break
        except:
            break

def receive():
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")

        client.send('NICK'.encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        nicknames[client] = nickname
        clients[client] = address[0]

        # Send the list of nicknames to the client
        client.send(f"NICKLIST:{','.join(nicknames.values())}".encode('utf-8'))

        print(f'Nickname of the client is {nickname}!')
        broadcast(f'{nickname} joined the chat!\n'.encode('utf-8'))
        client.send('Connected to the server\n'.encode('utf-8'))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

if __name__ == '__main__':
    print("Server running...")
    receive()
