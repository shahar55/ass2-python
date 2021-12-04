import socket
import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import watchdog as watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


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
                self.deleteFileList.append(event.src_path)
                self.addFileList.append(event.dest_path)

        else:
            if event.src_path not in self.deleteDirList:
                self.deleteDirList.append(event.src_path)
                self.addDirList.append(event.dest_path)

    def on_modified(self, event):
        if event.src_path not in self.deleteFileList:
            print(f"File was modified at {event.src_path}")
            self.deleteFileList.append(event.src_path)
            self.addFileList.append(event.src_path)

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



def send_path(path, sock):
    sock.send(path.encode('utf-8'))


def receive_path(sock):
    return sock.recv(1024).decode('utf-8')


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
    path = receive_path(sock)
    if path == "finish" or path == "end files":
        return -1
    f = open(path, 'w')
    l = sock.recv(1).decode('utf-8')
    while l != "end":
        f.write(l)
        l = sock.recv(1)
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
    path = receive_path(sock)
    while path != "end sub dirs":
        os.mkdir(path)
        path = receive_path(sock)


def receive_files(sock):
    while receive_file(sock) != -1:
        pass


def receive_dir(sock):
    path = receive_path(sock)
    os.mkdir(path)
    receive_empty_subdirs(sock)
    receive_files(sock)
    
    
def fix_path(path):
    if os.name == 'nt':
        return path.replace('/', os.path.sep)
    return path.replace('\\', os.path.sep)


if __name__ == "__main__":
    event_handler = Handler()
observer = watchdog.observers.Observer()
observer.schedule(event_handler, r'C:\Users\shahar\documents', recursive=True)
observer.start()
observer.join()
