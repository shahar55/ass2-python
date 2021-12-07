import sys
import socket
import time
import utils
import os
from watchdog.observers import Observer
from utils import Handler
import watchdog


def main():
    # validation of the arguments
    if len(sys.argv) != 5 and len(sys.argv) != 6:
        print("Number of arguments isn't correct.")
        return
    if int(sys.argv[2]) > 65535 or int(sys.argv[2]) < 1:
        print("Port number isn't valid.")
        return
    ipNums = sys.argv[1].split('.')
    if len(ipNums) != 4:
        print("IP address isn't valid.")
        return
    if int(sys.argv[4]) <= 0:
        print("time isn't valid")
        return
    for num in ipNums:
        if int(num) > 255 or int(num) < 0:
            print("IP address isn't valid.")
            return

    ipNum = sys.argv[1]
    portNum = int(sys.argv[2])
    path = utils.fix_path(sys.argv[3])
    emptyPath = 0
    if len(sys.argv) == 5:
        id = ""
    else:
        id = sys.argv[5]
    event_handler = Handler()
    while True:
        deleteDirList = event_handler.get_delete_directory_list()
        deleteFileList = event_handler.get_delete_file_list()
        addFileList = event_handler.get_add_file_list()
        addDirList = event_handler.get_add_directory_list()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ipNum, portNum))
        # the client first connection to the server.
        if len(sys.argv) == 5 and id == "":
            utils.send(s, b'no-id')
            data = utils.read(s)
            id = data.decode()
            if len(id) != 128:
                return
            dest_path = utils.get_name_folder(path)
            utils.send_dir_to_server(path, dest_path, s)
            utils.send_path(path, s)
        else:
            utils.send(s, id.encode())
            data = utils.read(s)
            # check if that is a new computer.
            flag = data.decode()
            if flag == 'no.':  # if the client is exist but the computer is new.
                os.mkdir(path)
                utils.send_path(path, s)
                utils.receive_dir(s)
            else:  # here that's the part of checking changes in the folder.
                utils.send_all_to_server(
                    s, [deleteFileList, deleteDirList, addDirList, addFileList], path, flag)
                # here we get the files we need to change.
                utils.receive_all_client(s)
                # this is the part when we change the files and save them.
        s.close()
        event_handler.clear_all_list()  # clear all the path's lists.
        emptyPath = emptyPath + 1
        # we will play the watch dog after the directory was given to us by the server first, or if this a new client,
        # after we gave it to the server.
        if emptyPath == 1:
            observer = watchdog.observers.Observer()
            observer.schedule(
                event_handler, path, recursive=True)
            observer.start()
            observer.join()
        time.sleep(int(sys.argv[4]))


if __name__ == '__main__':
    main()
