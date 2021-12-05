import socket
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
    emptyPath = 0
    if len(sys.argv) != 5 or len(sys.argv) != 6:
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
    id = ""
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
            s.send(b'no-id')
            data = s.recv(128)
            id = data.decode()
            if len(id) != 128:
                return
            dest_path = utils.get_name_folder(path)
            utils.send_dir(path, dest_path, s)
            utils.send_path(path)
        else:
            s.send(sys.argv[5].encode())
            data = s.recv(200)
            # check if that is a new computer.
            flag, id = data.decode().split('.')
            if id != sys.argv[5]:
                return
            if flag == 'no':  # if the client is exist but the computer is new.
                utils.send_path(path, s)
                utils.receive_dir(s)
            else:   # here that's the part of of checking changes in the folder.
                utils.send_all(
                    s, [deleteFileList, deleteDirList, addDirList, addFileList])
                # here we get the files we need to change.
                utils.receive_all_client(s)
                # this is the part when we change the files and save them.
        s.close()
        emptyPath = emptyPath + 1
        # we will play the watch dog after the directory was given to us by the server first, or if this a new client,
        # after we gave it to the server.
        if emptyPath == 1:
            observer = watchdog.observers.Observer()
            observer.schedule(
                event_handler, r'C:\Users\shahar\documents', recursive=True)
            observer.start()
            observer.join()
        event_handler.clear_all_list()  # clear all the path's lists.
        time.sleep(int(sys.argv[4]))


if __name__ == '__main__':
    main()
