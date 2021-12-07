import os
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


def send(sock, msg):
    sock.send(msg)
    sock.recv(3)


def read(sock):
    msg = sock.recv(1024)
    sock.send(b'got')
    return msg


def send_path(path, sock):
    send(sock, path.encode('utf-8'))


def receive_path(sock):
    path = fix_path(read(sock).decode('utf-8'))
    return path


def send_file(source_path, dest_path, sock):
    send_path(dest_path, sock)
    f = open(source_path, 'r')
    l = f.read(1024)
    while l:
        send(sock, l.encode('utf-8'))
        l = f.read(1024)
    send(sock, "end".encode('utf-8'))
    f.close()


def receive_file(sock):
    path = receive_path(sock)
    if path == "finish" or path == "end files":
        return -1
    f = open(path, 'w')
    l = read(sock).decode('utf-8')
    while l != "end":
        f.write(l)
        l = read(sock).decode('utf-8')
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


def send_empty_subdirs_to_server(source_path, sock):
    for root, dirs, files in os.walk(source_path):
        for d in dirs:
            dest_path = root.replace(source_path.rsplit(
                os.path.sep, 1)[0] + os.path.sep, "", 1)
            send_path(os.path.join(dest_path, d), sock)
    send(sock, "end sub dirs".encode('utf-8'))


def send_empty_subdirs_to_client(source_path, sock, absolute_path):
    for root, dirs, files in os.walk(source_path):
        for d in dirs:
            relative_root = os.path.relpath(root)
            if os.path.sep in relative_root:
                relative_root = os.path.relpath(root).split(os.path.sep, 1)[1]
            else:
                relative_root = ""
            dest_path = os.path.join(absolute_path, relative_root)
            send_path(os.path.join(dest_path, d), sock)
    send(sock, "end sub dirs".encode('utf-8'))


def send_files_to_server(source_path, sock):
    for root, dirs, files in os.walk(source_path):
        for f in files:
            dest_path = root.replace(source_path.rsplit(
                os.path.sep, 1)[0] + os.path.sep, "", 1)
            send_file(os.path.join(root, f),
                      os.path.join(dest_path, f), sock)
    send(sock, "end files".encode('utf-8'))


def send_files_to_client(source_path, sock, absolute_path):
    for root, dirs, files in os.walk(source_path):
        for f in files:
            relative_root = os.path.relpath(root).split(os.path.sep, 1)[1]
            dest_path = os.path.join(absolute_path, relative_root)
            send_file(os.path.join(root, f),
                      os.path.join(dest_path, f), sock)
    send(sock, "end files".encode('utf-8'))


def send_dir_to_server(source_path, dest_path, sock):
    send_path(dest_path, sock)
    send_empty_subdirs_to_server(source_path, sock)
    send_files_to_server(source_path, sock)


def send_dir_to_client(source_path, sock, absolute_path):
    send_empty_subdirs_to_client(source_path, sock, absolute_path)
    send_files_to_client(source_path, sock, absolute_path)


def receive_empty_subdirs(sock):
    path = receive_path(sock)
    while path != "end sub dirs" and path != "finish":
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
    return path


def send_empty_dir(path, sock):
    send_path(path, sock)


def receive_empty_dir(sock):
    path = receive_path(sock)
    return path


def fix_path(path):
    if os.name == 'nt':
        return path.replace('/', os.path.sep)
    return path.replace('\\', os.path.sep)


def get_name_folder(path):
    return path.rsplit(os.path.sep, 1)[-1]


def send_all_to_client(sock, file_or_directories_lists, absolute_path):
    for list in file_or_directories_lists:
        for src_path in list:
            dest_path = os.path.join(
                absolute_path, src_path.split(os.path.sep, 1)[1])
            type = read(sock).decode('utf-8')
            if type == "remove file" or type == "remove dir":
                send_path(dest_path, sock)
            if type == "add dir":
                send_path(dest_path, sock)
                send_empty_subdirs_to_client(src_path, sock, absolute_path)
            if type == "add file":
                send_file(src_path, dest_path, sock)
        sock.send(b'finish')


def send_all_to_server(sock, file_or_directories_lists, absolute_path, folder_name_server):
    for list in file_or_directories_lists:
        for src_path in list:
            dest_path = str(folder_name_server) + src_path.replace(
                str(absolute_path), "", 1)
            type = read(sock).decode('utf-8')
            if type == "remove file" or type == "remove dir":
                send_path(dest_path, sock)
            if type == "add dir":
                send_path(dest_path, sock)
                send_empty_subdirs_to_server(src_path, sock)
            if type == "add file":
                send_file(src_path, dest_path, sock)
        sock.send(b'finish')


def receive_all_client(sock):
    i = 1
    while i != 5:
        if i == 1:  # remove file
            send(sock, b'remove file')
            path = receive_path(sock)
            if path == "finish":
                i = i + 1
                continue
            remove_file(path)

        if i == 2:  # remove directories
            send(sock, b'remove dir')
            path = receive_empty_dir(sock)

            if path == "finish":
                i = i + 1
                continue
            remove_directory(path)

        if i == 3:  # add directory
            send(sock, b'add dir')
            receive_empty_subdirs(sock)
            i = i + 1
        if i == 4:  # add file
            send(sock, b'add file')
            receive_files(sock)
            i = i + 1


"""
   server handling part:
"""


def receive_empty_subdirs_server(sock, id, user_address, update_client_users_dict):
    path = receive_path(sock)
    while path != "finish":
        os.mkdir(path)
        for key in update_client_users_dict[id].keys():
            if key != user_address:
                update_client_users_dict[id][key]["addDir"].append(
                    path)  # add the path to computer addDir list.
        path = receive_path(sock)


def receive_file_server(sock, id, user_address, update_client_users_dict):
    path = receive_path(sock)
    if path == "finish" or path == "end files":
        return -1
    f = open(path, 'w')
    l = read(sock).decode('utf-8')
    while l != "end":
        f.write(l.encode())
        l = read(sock).decode('utf-8')
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
            send(sock, b'remove file')
            path = receive_path(sock)
            for key in update_client_users_dict[id].keys():
                if key != user_address:
                    update_client_users_dict[id][key]["deleteFile"].append(
                        path)  # add the path to computer delete files list.

            if path == "finish":
                i = i + 1
                continue
            remove_file(path)

        if i == 2:  # remove directories
            send(sock, b'remove dir')
            path = receive_empty_dir(sock)

            for key in update_client_users_dict[id].keys():
                if key != user_address:
                    update_client_users_dict[id][key]["deleteDir"].append(
                        path)  # add the path to computer delete directories list.

            if path == "finish":
                i = i + 1
                continue
            remove_directory(path)

        if i == 3:  # add directory
            send(sock, b'add dir')
            receive_empty_subdirs_server(
                sock, id, user_address, update_client_users_dict)
            i = i + 1
        if i == 4:  # add file
            send(sock, b'add file')
            receive_files_server(sock, id, user_address,
                                 update_client_users_dict)
            i = i + 1


if __name__ == "__main__":
    event_handler = Handler()
    observer = watchdog.observers.Observer()
    observer.schedule(
        event_handler, r'C:\Users\ronen\documents', recursive=True)
    observer.start()
    observer.join()
