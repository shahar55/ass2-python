import os
import random
import socket
import string
import sys
# here we will update a folder that is in the server.
def update(folder, changes):
    return 'update'
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if len(sys.argv) != 2:
        return
    if int(sys.argv[1]) > 65535 or int(sys.argv[1]) < 1:
        print("Port number isn't valid.")
        return
    server.bind(('', sys.argv[1]))
    server.listen()
    folders_dict = dict() # here we save the recent folder of each id.
    updates_dictionary = dict() # here we save the updates that are in the updated folder, but not in the computer of user.

    while True:
        client_socket, client_address = server.accept()
        data = client_socket.recv(200)
        if data.decode() == 'no-id':
            id = ""
            for i in range(128): # give id for new client
                id = id + random.choice(string.digits + string.ascii_letters)
            client_socket.send(id.encode())
            folder = client_socket.recv(1024) # here we recieve the folder from te client.
            folder_copy = "copy" # copy folder.
            folders_dict[id] = folder_copy
            updates_dictionary[id] = {client_address: []}
        else:
            id = data.decode()
            if client_address in updates_dictionary[id]: # if the user is in the server
                client_socket.send(b'yes.' + id.encode())
                changes = client_socket.recv(1024) # here we get the changes that the user made in the file.
                folders_dict[id] = update(folders_dict[id], changes) # here we update the folder in the server.
                for key in updates_dictionary[id].keys():
                    if key == client_address:
                        client_socket.send(b'changes in user list') #here we send the changes that are not in the user folder.
                        updates_dictionary[id][client_address] = [] # clean the list.
                    else: # here we update changes for all users of the client.
                        list = updates_dictionary[id].get(key)
                        list.append(changes.decode())
                        updates_dictionary[id][key] = list
            else: # the client is in the server but the user is not.
                client_socket.send(b'no.' + id.encode())
                client_socket.recv(1024)
                client_socket.send(b'here we send copy of the folder for the computer')
        client_socket.close()
        print('Client disconnected')
if __name__ == '__main__':
    main()
