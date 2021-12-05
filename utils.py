import socket
import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pathlib
import watchdog as watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

"""
class handler: handle the watch dog part an functions 
"""


class Handler(watchdog.events.PatternMatchingEventHandler):
    def __init__(self):
        watchdog.events.PatternMatchingEventHandler.__init__(self,
                                                             ignore_patterns=None,
                                                             ignore_directories=False, case_sensitive=True)
        self.deleteDirList = list()
        self.deleteFileList = list()
        self.addDirList = list()
        self.addFileList = list()

    def on_created(self, event):
        print(f"File was created at {event.src_path}")
        if os.path.isfile(event.src_path):
            if event.src_path not in self.addFileList:
                self.addFileList.append(event.src_path)

        else:
            if event.src_path not in self.addDirList:
                self.addDirList.append(event.src_path)

    def on_deleted(self, event):
        print(f"File was deleted at {event.src_path}")
        if os.path.isfile(event.src_path):
            if event.src_path not in self.deleteFileList:
                self.deleteFileList.append(event.src_path)

        else:
            if event.src_path not in self.deleteDirList:
                self.deleteDirList.append(event.src_path)

    def on_moved(self, event):
        print(f"File was deleted at {event.src_path} to {event.dest_path}")
        if os.path.isfile(event.src_path):
            if event.src_path not in self.deleteFileList:
                self.add_to_list(3, event.src_path)
                self.add_to_list(1, event.dest_path)

        else:
            if event.src_path not in self.deleteDirList:
                self.add_to_list(4, event.src_path)
                self.add_to_list(2, event.dest_path)

    def on_modified(self, event):
        if event.src_path not in self.deleteFileList and os.path.isfile(event.src_path):
            print(f"File was modified at {event.src_path}")
            self.add_to_list(1, event.src_path)
            self.add_to_list(3, event.src_path)

    def get_add_directory_list(self):
        return self.addDirList

    def get_add_file_list(self):
        return self.addFileList

    def get_delete_file_list(self):
        return self.deleteFileList

    def get_delete_directory_list(self):
        return self.deleteDirList

    def clear_add_directory_list(self):
        self.addDirList = list()

    def clear_add_file_list(self):
        self.addFileList = list()

    def clear_delete_file_list(self):
        self.deleteFileList = list()

    def clear_delete_directory_list(self):
        self.deleteDirList = list()

    def clear_all_list(self):
        self.clear_delete_directory_list()
        self.clear_add_directory_list()
        self.clear_add_file_list()
        self.clear_delete_file_list()

    def add_to_list(self, num_list, path):
        if num_list == 1 and path not in self.addFileList:
            self.addFileList.append(path)
        if num_list == 2 and path not in self.addDirList:
            self.addDirList.append(path)
        if num_list == 3 and path not in self.deleteFileList:
            self.deleteFileList.append(path)
        if num_list == 4 and path not in self.deleteDirList:
            self.deleteDirList.append(path)


"""
Actions that aim at files and folders and transfer them between the server and the user
"""


def send_path(path, sock):
    sock.send(path.encode('utf-8'))
    sock.recv(3)  # here we receive the got.



def receive_path(sock):
    path = sock.recv(1024).decode('utf-8')
    sock.send(b'got')
    return path


def send_file(path, sock):
    send_path(path, sock)
    f = open(path, 'r')
    l = f.read(1)
    while l:
        sock.send(l.encode('utf-8'))
        l = f.read(1)
    sock.send("end".encode('utf-8'))
    f.close()


def receive_file(sock):
    path = fix_path(receive_path(sock))
    if path == "finish" or path == "end files":
        return -1
    f = open(path, 'w')
    l = sock.recv(1).decode('utf-8')
    str_check_end = ""
    while str_check_end != "end":
        if len(str_check_end) != 3:
            str_check_end += l
        else:
            str_check_end = str_check_end.replace(str_check_end[0], '', 1)
            str_check_end += l
        l = l.encode
        f.write(l)
        l = sock.recv(1)
        l = l.decode('utf-8')
    f.close()
    return 0


def remove_file(path):
    if os.path.exists(path):
        os.remove(path)


def remove_directory(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            os.rmdir(os.path.join(root, d))
    os.rmdir(path)


def send_empty_subdirs(path, sock):
    for root, dirs, files in os.walk(path):
        for d in dirs:
            send_path(os.path.join(root, d), sock)
    sock.send("end sub dirs".encode('utf-8'))


def send_files(path, sock):
    for root, dirs, files in os.walk(path):
        for f in files:
            send_file(os.path.join(root, f), sock)
    sock.send("end files".encode('utf-8'))


def send_dir(path, sock):
    send_path(path, sock)
    send_empty_subdirs(path, sock)
    send_files(path, sock)


def receive_empty_subdirs(sock):
    path = fix_path(receive_path(sock))
    while path != "finish":
        os.mkdir(path)
        path = fix_path(receive_path(sock))


def receive_files(sock):
    while receive_file(sock) != -1:
        pass


def receive_dir(sock):
    path = receive_path(sock)
    os.mkdir(path)
    receive_empty_subdirs(sock)
    receive_files(sock)


def send_empty_dir(path, sock):
    send_path(path, sock)


def receive_empty_dir(sock):
    path = receive_path(sock)
    return path


def fix_path(path):
    if os.name == 'nt':
        return path.replace('/', os.path.sep)
    return path.replace('\\', os.path.sep)


def send_all(sock, file_or_directories_lists):
    for list in file_or_directories_lists:
        for send_path in list:
            send_path(send_path, sock)
            if os.path.isfile(send_path):
                send_file(send_path, sock)
            send_dir(send_path, sock)
        sock.send(b'finish')


def receive_all_client(sock):
    i = 1
    while i != 5:
        if i == 1:  # remove file
            path = fix_path(receive_path(sock))
            if path == "finish":
                i = i + 1
                continue
            remove_file(path)

        if i == 2:  # remove directories
            path = fix_path(receive_empty_dir(sock))

            if path == "finish":
                i = i + 1
                continue
            remove_directory(path)

        if i == 3:  # add directory
            receive_empty_subdirs(sock)
            i = i + 1
        if i == 4:  # add file
            receive_files(sock)
            i = i + 1


"""
   server handling part:
"""


def receive_empty_subdirs_server(sock, id, user_address, update_client_users_dict):
    path = fix_path(receive_path(sock))
    while path != "finish":
        os.mkdir(path)
        for key in update_client_users_dict[id].keys():
            if key != user_address:
                update_client_users_dict[id][key]["addDir"].append(
                    path)  # add the path to computer addDir list.
        path = fix_path(receive_path(sock))


def receive_file_server(sock, id, user_address, update_client_users_dict):
    path = fix_path(receive_path(sock))
    if path == "finish" or path == "end files":
        return -1
    f = open(path, 'w')
    l = sock.recv(1).decode('utf-8')
    while l != "end":
        f.write(l)
        l = sock.recv(1)
    f.close()
    for key in update_client_users_dict[id].keys():
        if key != user_address:
            update_client_users_dict[id][key]["addFile"].append(
                path)  # add the path to computer add files list.
    return 0


def receive_files_server(sock, id, user_address, update_client_users_dict):
    while receive_file_server(sock, id, user_address, update_client_users_dict) != -1:
        pass


def receive_all_server(sock, id, user_address, update_client_users_dict):
    i = 1
    while i != 5:
        if i == 1:  # remove file
            path = fix_path(receive_path(sock))
            for key in update_client_users_dict[id].keys():
                if key != user_address:
                    update_client_users_dict[id][key]["deleteFile"].append(
                        path)  # add the path to computer delete files list.

            if path == "finish":
                i = i + 1
                continue
            remove_file(path)

        if i == 2:  # remove directories
            path = fix_path(receive_empty_dir(sock))

            for key in update_client_users_dict[id].keys():
                if key != user_address:
                    update_client_users_dict[id][key]["deleteDir"].append(
                        path)  # add the path to computer delete directories list.

            if path == "finish":
                i = i + 1
                continue
            remove_directory(path)

        if i == 3:  # add directory
            receive_empty_subdirs_server(sock, id, user_address, update_client_users_dict)
            i = i + 1
        if i == 4:  # add file
            receive_files_server(sock, id, user_address, update_client_users_dict)
            i = i + 1


if __name__ == "__main__":
    event_handler = Handler()
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, r'C:\Users\shahar\documents', recursive=True)
    observer.start()
    observer.join()
