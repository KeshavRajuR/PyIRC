import socket
import select   #OS-level monitoring operations for everything including sockets

HEADER_LENGTH = 10

#Server details
IP = "127.0.0.1"
PORT = 1234

#Initial setup of socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Overcome "Address already in use" when building programs. Allows reuse of address
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

#Bind and listen
server_socket.bind((IP, PORT))
server_socket.listen()

#List of sockets for select.select()
sockets_list = [server_socket]

#List of connected clients - socket as a key, user header and name as data
clients = {}

#Debugging info
print(f'Listening for connections on {IP}:{PORT}...')

#Receiving messages
def receive_message(client_socket):
    try:
        #Receiving the message header
        message_header = client_socket.recv(HEADER_LENGTH)
        
        #Client closes connection correctly
        if not len(message_header):
            return False
        
        #Getting message length
        message_length = int(message_header.decode('utf-8').strip())

        #Returning data
        return {'header': message_header, 'data': client_socket.recv(message_length)}
    except:
        #Something went wrong like empty message or client exited abruptly.
        return False

while True:
    #Calls Unix select() system call or Windows select() WinSock call with three parameters:
    #   - rlist - sockets to be monitored for incoming data
    #   - wlist - sockets for data to be send to (checks if for example buffers are not full and socket is ready to send some data)
    #   - xlist - sockets to be monitored for exceptions (we want to monitor all sockets for errors, so we can use rlist)
    #Returns lists:
    #   - reading - sockets we received some data on (that way we don't have to check sockets manually)
    #   - writing - sockets ready for data to be send thru them
    #   - errors  - sockets with some exceptions
    #This is a blocking call, code execution will "wait" here and "get" notified in case any action should be taken
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
    
    #Iterating over read_sockets list to read data
    for notified_socket in read_sockets:

        #If new notified_socket is server, this means it is a new connection
        if notified_socket == server_socket:

            #Getting client details. Unique client socket and address
            client_socket, client_address = server_socket.accept()
            user = receive_message(client_socket)

            #If client closes connection, then just leave it and move on
            if user is False:
                continue

            #Appending the client to the sockets_list and saving the client details
            sockets_list.append(client_socket)
            clients[client_socket] = user
            print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))
        
        #If new notified_socket is not server, this means we have to read message
        else:
            message = receive_message(notified_socket)

            #Make sure message exists before we try to read it
            if message is False:
                print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                continue
            user = clients[notified_socket]
            print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')
            
            #Broadcasting message out to every connected client
            for client_socket in clients:

                #Don't want to send it back to sender
                if client_socket != notified_socket:
                    client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
    
    #Handling errors/exceptions in sockets
    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]
