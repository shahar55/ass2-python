import random
import socket
import string
import sys
import utils


def new_client(update_folders, update_all_dict, id, client_number, folder_path, client_path):
    update_folders[id] = folder_path
    update_all_dict[id] = {client_number: [
        {"deleteDir": [], "deleteFile": [], "addDir": [], "addFile": []}, client_path]}


def clear_computer(update_all_dict, id, client_number, client_path):
    update_all_dict[id][client_number] = [
        {"deleteDir": [], "deleteFile": [], "addDir": [], "addFile": []}, client_path]


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if len(sys.argv) != 2:
        print("Number of arguments is invalid.")
        return
    if int(sys.argv[1]) > 65535 or int(sys.argv[1]) < 1:
        print("Port number isn't valid.")
        return
    server.bind(('', int(sys.argv[1])))
    server.listen()
    folders_dict = dict()  # here we save the recent folder of each id.

    # here we save the updates that are in the updated folder, but not in the computer of user.
    updates_dictionary = dict()

    while True:
        sock, client_address = server.accept()
        data = utils.read(sock).decode()
        data2 = utils.read(sock).decode()

        # if the client does not have an id:
        # here we send an id to him and he sand as the folder, we create him, and save the path.

        if data == 'no_id':
            id = ""
            for i in range(128):  # give id for new client
                id = id + random.choice(string.digits + string.ascii_letters)
            print(id)
            utils.send(sock, id.encode())
            client_num = 1
            # here we receive the folder from the client.
            path = utils.receive_dir(sock)
            client_path = utils.receive_path(sock)
            new_client(folders_dict, updates_dictionary,
                       id, client_num, path, client_path)

        # if the client have an id:

        else:
            id = data
            client_num = int(data2)
            # if the user is in the server
            if client_num in updates_dictionary[id].keys():
                utils.send(sock, folders_dict[id].encode())
                # here we get the changes that the user made in the file.
                utils.receive_all_server(
                    sock, id, client_num, updates_dictionary)
                # here we send the changes that the user need to do.
                send_changes_list = [updates_dictionary[id][client_num][0]["deleteFile"],
                                     updates_dictionary[id][client_num][0]["deleteDir"],
                                     updates_dictionary[id][client_num][0]["addDir"],
                                     updates_dictionary[id][client_num][0]["addFile"]]

                utils.send_all_to_client(
                    sock, send_changes_list, updates_dictionary[id][client_num][1])

                # clear computer changes list
                clear_computer(updates_dictionary, id, client_num,
                               updates_dictionary[id][client_num][1])

            else:  # the client is in the server but the user is not.
                utils.send(sock, b'no.')
                path = utils.receive_path(sock)
                utils.send_dir_to_client(folders_dict[id], sock, path)
                client_num = max(updates_dictionary[id].keys()) + 1
                utils.send(sock, str(client_num).encode())
                # set empty computer changes list
                clear_computer(updates_dictionary, id,
                               client_num, path)
        sock.close()
        print('Client disconnected')


if __name__ == '__main__':
    main()
