import socket
import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def on_created(event):
    print("created")


def on_deleted(event):
    print("deleted")


def on_modified(event):
    print("modified")


def on_moved(event):
    print("moved")


def get_observer(path):
    event_handler = FileSystemEventHandler()
    # calling functions
    event_handler.on_created = on_created
    event_handler.on_deleted = on_deleted
    event_handler.on_modified = on_modified
    event_handler.on_moved = on_moved
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    return observer


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


if __name__ == "__main__":
    observer = get_observer("C:\Program Files")
    observer.start()
    try:
        print("Monitoring")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("Done")
    observer.join()
