import socket
import sys
import select
import errno

HEADER_LENGTH = 10

#Client details
IP = "127.0.0.1"
PORT = 1234
my_username = input("Username: ")

#Initial setup of socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Connect to the server
client_socket.connect((IP, PORT))

#Set revc method to not block
client_socket.setblocking(False)

#Setting the username on the server side
username = my_username.encode('utf-8')
username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
client_socket.send(username_header + username)

while True:
    #Getting the message from the user
    message = input(f'{my_username} > ')
    
    #Making sure to not send empty messages
    if message:

        #Encode message to bytes, prepare head and convert to bytes
        message = message.encode('utf-8')
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
        client_socket.send(message_header + message)

    try:
        #Receive messages and print
        while True:
            username_header = client_socket.recv(HEADER_LENGTH)

            #If server has closed the connection properly
            if not len(username_header):
                print('Connection closed by the server')
                sys.exit()

            #Getting the username
            username_length = int(username_header.decode('utf-8').strip())
            username = client_socket.recv(username_length).decode('utf-8')

            #Getting the message
            message_header = client_socket.recv(HEADER_LENGTH)
            message_length = int(message_header.decode('utf-8').strip())
            message = client_socket.recv(message_length).decode('utf-8')

            #Output the username and message in IRC chat format
            print(f"{username} > {message}")
    
    except IOError as e:
        # This is normal on non blocking connections - when there are no incoming data, error is going to be raised
        # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
        # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
        # If we got different error code - something happened
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print("Reading error: {}".format(str(e)))
            sys.exit()
        
        #Not considered as an error. Nothing received
        continue

    except Exception as e:
        #Printing any other form of errors
        print("Reading error: {}".format(str(e)))
        sys.exit()