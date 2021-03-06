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
        if os.path.isfile(event.src_path):
            if event.src_path not in self.addFileList:
                self.addFileList.append(event.src_path)

        elif os.path.isdir(event.src_path):
            if event.src_path not in self.addDirList:
                self.addDirList.append(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            if event.src_path not in self.deleteFileList:
                self.deleteFileList.append(event.src_path)

        else:
            if event.src_path not in self.deleteDirList:
                self.deleteDirList.append(event.src_path)

    def on_moved(self, event):
        if os.path.isfile(event.dest_path):
            if event.src_path not in self.deleteFileList:
                self.add_to_list(3, event.src_path)
                self.add_to_list(1, event.dest_path)

        elif os.path.isdir(event.dest_path):
            if event.src_path not in self.deleteDirList:
                self.add_to_list(4, event.src_path)
                self.add_to_list(2, event.dest_path)

    def on_modified(self, event):
        if event.src_path not in self.deleteFileList and os.path.isfile(event.src_path):
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
    if os.path.isfile(source_path):
        send_path(dest_path, sock)
        f = open(source_path, 'rb')
        l = f.read(1024)
        while l:
            send(sock, l)
            l = f.read(1024)
        send(sock, "end".encode('utf-8'))
        f.close()


def receive_file(sock, old_path="", new_path=""):
    path = receive_path(sock)
    if path == "finish" or path == "end files":
        return -1
    if old_path != "":
        path = path.replace(old_path, new_path, 1)
    if os.path.isdir(path.rsplit(os.path.sep, 1)[0]):
        f = open(path, 'wb')
        l = read(sock)
        while l != "end".encode():
            f.write(l)
            l = read(sock)
        f.close()
    return 0


def remove_file(path):
    if os.path.isfile(path):
        os.remove(path)


def remove_directory(path):
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        os.rmdir(path)


def remove_path(path):
    remove_file(path)
    remove_directory(path)


def send_empty_subdirs_to_server(source_path, sock):
    if os.path.isdir(source_path):
        for root, dirs, files in os.walk(source_path):
            for d in dirs:
                dest_path = root.replace(source_path.rsplit(
                    os.path.sep, 1)[0] + os.path.sep, "", 1)
                send_path(os.path.join(dest_path, d), sock)
    send(sock, "end sub dirs".encode('utf-8'))


def send_empty_subdirs_to_client(source_path, sock, absolute_path):
    if os.path.isdir(source_path):
        for root, dirs, files in os.walk(source_path):
            for d in dirs:
                relative_root = os.path.relpath(root)
                if os.path.sep in relative_root:
                    relative_root = os.path.relpath(
                        root).split(os.path.sep, 1)[1]
                else:
                    relative_root = ""
                dest_path = os.path.join(absolute_path, relative_root)
                send_path(os.path.join(dest_path, d), sock)
    send(sock, "end sub dirs".encode('utf-8'))


def send_files_to_server(source_path, sock):
    if os.path.isdir(source_path):
        for root, dirs, files in os.walk(source_path):
            for f in files:
                dest_path = root.replace(source_path.rsplit(
                    os.path.sep, 1)[0] + os.path.sep, "", 1)
                send_file(os.path.join(root, f),
                          os.path.join(dest_path, f), sock)
    send(sock, "end files".encode('utf-8'))


def send_files_to_client(source_path, sock, absolute_path):
    if os.path.isdir(source_path):
        for root, dirs, files in os.walk(source_path):
            for f in files:
                relative_root = os.path.relpath(root)
                if os.path.sep in relative_root:
                    relative_root = os.path.relpath(
                        root).split(os.path.sep, 1)[1]
                else:
                    relative_root = ""
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


def receive_empty_subdirs(sock, old_path="", new_path=""):
    path = receive_path(sock)
    while path != "end sub dirs" and path != "finish":
        if old_path != "":
            path = path.replace(old_path, new_path, 1)
        if os.path.isdir(path.rsplit(os.path.sep, 1)[0]):
            os.mkdir(path)
        path = receive_path(sock)


def receive_files(sock, old_path="", new_path=""):
    while receive_file(sock, old_path, new_path) != -1:
        pass


def receive_dir(sock):
    path = receive_path(sock)
    new_path = path
    i = 1
    while os.path.isdir(new_path):
        new_path = path + "_" + str(i)
        i = i + 1
    os.mkdir(new_path)
    receive_empty_subdirs(sock, path, new_path)
    receive_files(sock, path, new_path)
    return new_path


def send_empty_dir(src_path, dest_path, sock):
    if os.path.isdir(src_path):
        send_path(dest_path, sock)


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
    i = 1
    for list in file_or_directories_lists:
        for src_path in list:
            dest_path = os.path.join(
                absolute_path, src_path.split(os.path.sep, 1)[1])
            if i == 1 or i == 2:
                send_path(dest_path, sock)
            if i == 3:
                send_empty_dir(src_path, dest_path, sock)
            if i == 4:
                send_file(src_path, dest_path, sock)
        send(sock, b'finish')
        i = i + 1


def send_all_to_server(sock, file_or_directories_lists, absolute_path, folder_name_server):
    i = 1
    for list in file_or_directories_lists:
        for src_path in list:
            dest_path = str(folder_name_server) + src_path.replace(
                str(absolute_path), "", 1)
            if i == 1 or i == 2:
                send_path(dest_path, sock)
            if i == 3:
                send_empty_dir(src_path, dest_path, sock)
            if i == 4:
                send_file(src_path, dest_path, sock)
        send(sock, b'finish')
        i = i + 1


def receive_all_client(sock):
    i = 1
    while i != 5:
        if i == 1:  # remove file
            path = receive_path(sock)
            if path == "finish":
                i = i + 1
                continue
            remove_path(path)
        if i == 2:  # remove directories
            path = receive_empty_dir(sock)
            if path == "finish":
                i = i + 1
                continue
            remove_path(path)
        if i == 3:  # add directory
            receive_empty_subdirs(sock)
            i = i + 1
        if i == 4:  # add file
            receive_files(sock)
            i = i + 1


"""
   server handling part:
"""


def receive_empty_subdirs_server(sock, id, client_num, update_client_users_dict):
    path = receive_path(sock)
    while path != "finish":
        if os.path.isdir(path.rsplit(os.path.sep, 1)[0]):
            os.mkdir(path)
            for key in update_client_users_dict[id].keys():
                if key != client_num:
                    update_client_users_dict[id][key][0]["addDir"].append(
                        path)  # add the path to computer addDir list.
        path = receive_path(sock)


def receive_file_server(sock, id, client_num, update_client_users_dict):
    path = receive_path(sock)
    if path == "finish" or path == "end files":
        return -1
    if os.path.isdir(path.rsplit(os.path.sep, 1)[0]):
        f = open(path, 'wb')
        l = read(sock)
        while l != "end".encode():
            f.write(l)
            l = read(sock)
        f.close()
        for key in update_client_users_dict[id].keys():
            if key != client_num:
                update_client_users_dict[id][key][0]["addFile"].append(
                    path)  # add the path to computer add files list.
    return 0


def receive_files_server(sock, id, client_num, update_client_users_dict):
    while receive_file_server(sock, id, client_num, update_client_users_dict) != -1:
        pass


def receive_all_server(sock, id, client_num, update_client_users_dict):
    i = 1
    while i != 5:
        if i == 1:  # remove file
            path = receive_path(sock)
            if path == "finish":
                i = i + 1
                continue
            for key in update_client_users_dict[id].keys():
                if key != client_num:
                    update_client_users_dict[id][key][0]["deleteFile"].append(
                        path)  # add the path to computer delete files list.
            remove_path(path)
        if i == 2:  # remove directories
            path = receive_empty_dir(sock)
            if path == "finish":
                i = i + 1
                continue
            for key in update_client_users_dict[id].keys():
                if key != client_num:
                    update_client_users_dict[id][key][0]["deleteDir"].append(
                        path)  # add the path to computer delete directories list.
            remove_path(path)
        if i == 3:  # add directory
            receive_empty_subdirs_server(
                sock, id, client_num, update_client_users_dict)
            i = i + 1
        if i == 4:  # add file
            receive_files_server(sock, id, client_num,
                                 update_client_users_dict)
            i = i + 1


def fix_add_dir_list(add_dir_list):
    for i in range(len(add_dir_list)):
        for j in range(i, len(add_dir_list)):
            if str(add_dir_list[j]) in str(add_dir_list[i]):
                add_dir_list[i], add_dir_list[j] = add_dir_list[j], add_dir_list[i]
    return add_dir_list
