import os
import random
import socket
import string
import sys
import utils
# here we will update a folder that is in the server.


def update(folder, changes):
    return 'update'


def new_client(update_folders, update_all_dict, id, address, folder_path):
    update_folders[id] = folder_path
    update_all_dict[id] = {address: {"deleteDir": [],
                                     "deleteFile": [], "addDir:": [], "addFile": []}}


def new_computer(update_all_dict, id, address):
    update_all_dict[id][address] = {
        "deleteDir": [], "deleteFile": [], "addDir:": [], "addFile": []}


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if len(sys.argv) != 2:
        return
    if int(sys.argv[1]) > 65535 or int(sys.argv[1]) < 1:
        print("Port number isn't valid.")
        return
    server.bind(('', sys.argv[1]))
    server.listen()
    folders_dict = dict()  # here we save the recent folder of each id.
    # here we save the updates that are in the updated folder, but not in the computer of user.
    updates_dictionary = dict()

    while True:
        sock, client_address = server.accept()
        data = sock.recv(200)
        if data.decode() == 'no-id':
            id = ""
            for i in range(128):  # give id for new client
                id = id + random.choice(string.digits + string.ascii_letters)
            sock.send(id.encode())
            # here we recieve the folder from the client.
            path = utils.receive_dir(sock)
            folders_dict[id] = path
            dest_path = utils.receive_path(sock)
            updates_dictionary[id] = {client_address: [{
                "deleteDir": [], "deleteFile": [], "addDir:": [], "addFile": []}, dest_path]}
        else:
            id = data.decode()
            # if the user is in the server
            if client_address in updates_dictionary[id]:
                sock.send(b'yes.' + id.encode())
                # here we get the changes that the user made in the file.
                changes = sock.recv(1024)
                # here we update the folder in the server.
                folders_dict[id] = update(folders_dict[id], changes)
                for key in updates_dictionary[id].keys():
                    if key == client_address:
                        # here we send the changes that are not in the user folder.
                        sock.send(b'changes in user list')
                        # clean the list.
                        updates_dictionary[id][client_address] = []
                    else:  # here we update changes for all users of the client.
                        list = updates_dictionary[id].get(key)
                        list.append(changes.decode())
                        updates_dictionary[id][key] = list
            else:  # the client is in the server but the user is not.
                sock.send(b'no.' + id.encode())
                path = utils.receive_path(sock)
                utils.send_dir(folders_dict[id], path, sock)
        sock.close()
        print('Client disconnected')


if __name__ == '__main__':
    main()
