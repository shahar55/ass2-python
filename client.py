import socket
import  sys;
import time
def main():
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
        print ("time isn't valid")
        return
    for num in ipNums:
        if int(num) > 255 or int(num) < 0:
            print("IP address isn't valid.")
            return
    ipNum = sys.argv[1]
    portNum = int(sys.argv[2])
    id = ""
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ipNum, portNum))
        if len(sys.argv) == 5 and id == "": # the client first connection to the server.
            s.send(b'no-id')
            data = s.recv(200)
            id = data.decode()
            if len(data) != 128:
                return
            s.send(b'here we send the new folder folder')
        else:
            s.send(sys.argv[5].encode())
            data = s.recv(200)
            flag, id = data.decode().split('.') # check if that is a new computer.
            if id != sys.argv[5]:
                return
            if flag == 'no': #if the client is exist but the computer is new.
                s.send(b'give me copy of the folder')
                folder = s.recv(1024) #here we got a copy of the folder.
            else:
                folder = "here we opening the folder if he exist in our computer."
            # here that's the part of of checking changes in the folder.
            s.send(b'here we send the changes that we check in the folder')
            newFolder = s.recv(1024) # here we get the files we need to change.
            # this is the part when we change the files and save them.
        s.close()
        time.sleep(int(sys.argv[4]))
if __name__ == '__main__':
    main()
