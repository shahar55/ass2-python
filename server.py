import os
import random
import socket
import string
import sys
import utils


def new_client(update_folders, update_all_dict, id, address, folder_path, client_path):
    update_folders[id] = folder_path
    update_all_dict[id] = {address: [
        {"deleteDir": [], "deleteFile": [], "addDir:": [], "addFile": []}, client_path]}


def clear_computer(update_all_dict, id, address, client_path):
    update_all_dict[id][address] = [
        {"deleteDir": [], "deleteFile": [], "addDir:": [], "addFile": []}, client_path]


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
        data = utils.read(sock)

        # if the client does not have an id:
        # here we send an id to him and he sand as the folder, we create him, and save the path.

        if data.decode() == 'no-id':
            id = ""
            for i in range(128):  # give id for new client
                id = id + random.choice(string.digits + string.ascii_letters)
            print(id)
            utils.send(sock, id.encode())
            # here we receive the folder from the client.
            path = utils.receive_dir(sock)
            client_path = utils.receive_path(sock).rsplit(os.path.sep, 1)[0]
            new_client(folders_dict, updates_dictionary,
                       id, client_address, path, client_path)

        # if the client have an id:

        else:
            id = data.decode()
            # if the user is in the server
            if client_address in updates_dictionary[id]:
                utils.send(sock, b'yes.')
                # here we get the changes that the user made in the file.
                utils.receive_all_server(
                    sock, id, client_address, updates_dictionary)
                # here we send the changes that the user need to do.
                send_changes_list = [updates_dictionary[id][client_address][0]["deleteFile"],
                                     updates_dictionary[id][client_address][0]["deleteDir"],
                                     updates_dictionary[id][client_address][0]["addDir"],
                                     updates_dictionary[id][client_address][0]["addFile"]]

                utils.send_all_to_client(
                    sock, send_changes_list, updates_dictionary[id][client_address][1])

                # clear computer changes list
                clear_computer(updates_dictionary, id, client_address,
                               updates_dictionary[id][client_address][1])

            else:  # the client is in the server but the user is not.
                utils.send(sock, b'no.')
                path = utils.receive_path(sock)
                utils.send_dir(folders_dict[id], path, sock)

                # set empty computer changes list
                clear_computer(updates_dictionary, id,
                               client_address, path.rsplit(os.path.sep, 1)[0])
        sock.close()
        print('Client disconnected')


if __name__ == '__main__':
    main()
