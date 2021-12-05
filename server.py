import os
import random
import socket
import string
import sys
import utils


def new_client(update_folders, update_all_dict, id, address, folder_path):
    update_folders[id] = folder_path
    update_all_dict[id] = {address: {"deleteDir": [],
                                     "deleteFile": [], "addDir:": [], "addFile": []}}


def clear_computer(update_all_dict, id, address):
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

        # if the client does not have an id:
        # here we send an id to him and he sand as the folder, we create him, and save the path.

        if data.decode() == 'no-id':
            id = ""
            for i in range(128):  # give id for new client
                id = id + random.choice(string.digits + string.ascii_letters)
            print(id)
            sock.send(id.encode())
            # here we receive the folder from the client.
            path = utils.receive_dir(sock)
            new_client(folders_dict, updates_dictionary, id, client_address, path)

        # if the client have an id:

        else:
            id = data.decode()
            # if the user is in the server
            if client_address in updates_dictionary[id]:
                sock.send(b'yes.' + id.encode())
                # here we get the changes that the user made in the file.
                utils.receive_all_server(sock, id, client_address, updates_dictionary)
                # here we send the changes that the user need to do.
                send_changes_list = [updates_dictionary[id][client_address]["deleteFile"],
                                     updates_dictionary[id][client_address]["deleteDir"],
                                     updates_dictionary[id][client_address]["addDir"],
                                     updates_dictionary[id][client_address]["addFile"]]

                utils.send_all(sock, send_changes_list)

                # clear computer changes list
                clear_computer(updates_dictionary, id, client_address)

            else:  # the client is in the server but the user is not.
                sock.send(b'no.' + id.encode())
                path = utils.receive_path(sock)
                utils.send_dir(folders_dict[id], path, sock)

                # set empty computer changes list
                clear_computer(updates_dictionary, id, client_address)
        sock.close()
        print('Client disconnected')


if __name__ == '__main__':
    main()
