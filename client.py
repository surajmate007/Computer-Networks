import sys
import threading
import socket


username = sys.argv[1]
SERVER_IP = sys.argv[2]
PORT = 5001


if username == 'ALL':                          # if username is "ALL" then warning the user to change it. Since ALL is used for broadcast
    print('''"ALL" is reserved keyword, please use different username.''')
    sys.exit()


class Client:

    # Function to check the format of the sent message from the client end
    # Checking for the exact format: "@[recipient name]: [message]"
    def checkSendFormat(self, msg):
        recipient = ""
        content = ""
        form = True                     # form variable represents whether the format is correct or not

        if(msg[0] == "@"):                  
            i = msg.find(':')
            if(i == -1):                # if : does not exist means the form is incorrect
                form = False
            else:
                arr = msg.split(":")
                rec = arr[0].split("@")
                recipient = rec[1]
                content = arr[1]
                content = content.strip()
            
            if(recipient=="" or content==""):
                form = False
        else:
            form = False

        return recipient, content, form         # extracting the recipient name and content from the message input from user.
    


    # Functions to check the format of the forwarded message from the server end 
    # The format is: "FORWARD [sender name] Content-length: [length of content] [content of message]"
    def checkRecvFormat(self, msg):
        sender = ""
        content = ""
        form = True                      # form variable represents whether the format is correct or not

        arr = msg.split("\n")
        a = arr[0].split(" ")
        b = arr[1].split(" ")

        if(a[0] != "FORWARD" or b[0] != "Content-length:"):         # checking the message parameters are as expected or not. if not then form = False
            form = False

        sender = a[1]
        content = arr[3]
        length = b[1]

        if(sender == "" or content == "" or len(content) != int(length)):       # if both sender and content is empty then also form = False
            form = False
        
        return sender, content, form     # extracting the sender name and content from the message forwarded from server.


    # Function to send the messages if the client is behaving like sender
    def sendMsg(self):

        while True:
            msg = input()
            recipient, content, form = self.checkSendFormat(msg)        # checking the correctness of message format

            if(form == False):                                          # if format is not correct then telling user the correct format
                print("Messsage format incorrect.")
                print("Use following form :")
                print('@[RECIPIENT NAME]: Message\n')
                continue

            if(recipient == username):                                  # if the sender username and receiver username are same then telling it to sender
                print("Sender and Receiver both are same.")
                print("Register with different username...")
                continue
            
            message = "SEND {}\nContent-length: {}\n\n{}".format(recipient, len(content), content)      # creating the message in format: "SEND [recipient username] Content-length: [length of message] [content of the message]" 

            try:
                clientSend.send(message.encode("utf-8"))                # sending the above created message to sender
            except Exception as e:
                print("Server Unavailable : ", e)
                break

            try:
                ack = clientSend.recv(1024)                             #receiving the ack form sender
            except Exception as e:
                print("Server Unavailable : ", e)
                break

            ack = ack.decode("utf-8")
            arr = ack.split(" ")

            if(arr[0] == "SEND" and arr[1] == "{}\n\n".format(recipient)):      # checking the send format like : "SEND [Rrecipient name]\n\n"
                print("Message delivered successfully to {}".format(recipient))

            elif(arr[0] == "ERROR" and arr[1] == "102" and arr[2] == "Unable" and arr[3] == "to" and arr[4] == "send\n\n"):     # checking the error format as expetedd or not like : "ERROR 102 Unable to send\n\n"
                print(ack)
                print("Message undelivered to {}".format(recipient))
                print("try again")
            
            elif(arr[0] == "ERROR" and arr[1] == "103" and arr[2] == "Header" and arr[3] == "Incomplete\n\n"):                  # checking the error format as expected or not like: "ERROR 103 Header Incomplete\n\n"
                print(ack)
                print("Message undelivered to {}".format(recipient))
                print("try again")

            else:
                print("Unknown error")                                          # if error format is not matching then printing unknown error
                break

        clientSend.close()


    # Function to receive the message if the client is behaving like receiver
    def recvMsg(self):

        while True:

            try:
                msg = clientRecv.recv(1024)                                     # receiving the forwarded message from the sender
            except Exception as e:
                print("Server unavailavle : ", e)
            
            msg = msg.decode("utf-8")

            sender, content, form = self.checkRecvFormat(msg)                   # calling the function to check the received message format

            if(form == False):                                          
                ack = "ERROR 103 Header Incomplete\n\n"                         # if form is not correct then creating the negative acknowledgment message
                print("Message not in well form")
            else:
                ack = "RECEIVED {}\n\n".format(sender)                          # if form is correct then creating the positive acknowledgment message
                print("{} :- {}".format(sender, content))                       # printing the message on receivers window

            try:
                clientRecv.send(ack.encode("utf-8"))                            # seding the acknowledgment from receiver to server 
            except Exception as e:
                print("Exception appeared is: ", e)
                break
        clientRecv.close()                                                      # closing the client socket
            

    # Function to register the client for sending the messages.
    def doSendRegesitration(self):
        regReq1 = "REGISTER TOSEND {}\n\n".format(username)                     # creating the registration request

        try:
            clientSend.send(regReq1.encode("utf-8"))                            # sending the registration request

        except Exception as e:
            print("Server gives this exception ", e)
            sys.exit()

        try:
            ack1 = clientSend.recv(1024)                                        # receiving the acknowledgment from server
            
        except Exception as e:
            print("Server unavailable ", e)
            sys.exit()

        ack1 = ack1.decode("utf-8")
        arr1 = ack1.split(" ")


        if(arr1[0] == "REGISTERED" and arr1[1] == "TOSEND" and arr1[2] == "{}\n\n".format(username)):       # checking the ack is well formed or not.
            print("{} Successfully Registered to Send".format(username))
            send_thread = threading.Thread(target=self.sendMsg)                                             # creating the thread for client to send the messages any time


            #----------------------- Put threading line here --------------------------

        elif(arr1[0] == "ERROR" and arr1[1] == "100" and arr1[2]=="Malformed" and arr1[3] == "username\n\n"):   # checking the ack is error like: "ERRPR 100 Malformed username\n\n"
            print(ack1)
            print("Exititng... Try Again...")
            sys.exit()                                                                                          # exiting so that user can register again

        else:
            print("ERROR 101 : No user registered")                                                             # if user starts sending without registration
            print("Exititng... Try Again...")
            sys.exit()                                                                                          # exiting so that user can register

        return send_thread

    # Function to register the client for receiving the messages.
    def doRecvRegistration(self):                                              
        
        regReq2 = "REGISTER TORECV {}\n\n".format(username)                     # creating the registration request

        try:
            clientRecv.send(regReq2.encode("utf-8"))                            # sending the registration request to server

        except Exception as e:
            print("Server gives this exception ", e)
            sys.exit()

        try:
            ack2 = clientRecv.recv(1024)                                        # receiving the acknowledgment from server
            
        except Exception as e:
            print("Server unavailable ", e)

        
        ack2 = ack2.decode("utf-8")
        arr2 = ack2.split(" ")

        if(arr2[0] == "REGISTERED" and arr2[1] == "TORECV" and arr2[2] == "{}\n\n".format(username)):       # checking the format of acknowledgment
            print("{} Successfully Registered to Receive".format(username))
            recev_thread = threading.Thread(target=self.recvMsg)                                            # creating the thread for client to receive messages any time

            #----------------------- Put threading line here --------------------------

        elif(arr2[0] == "ERROR" and arr2[1] == "100" and arr2[2]=="Malformed" and arr2[3] == "username\n\n"):   # checking the error like: "ERROR 100 Malformed username"
            print(ack2)
            print("Exititng... Try Again...")
            sys.exit()                                                                                          # exiting so that user can register again for receiving

        else:
            print("ERROR 101 : No user registered")                                                         # if user starts sending without registration
            print("Exititng... Try Again...")
            sys.exit()                                                                                      # exiting so that user can register

        return recev_thread




cl = Client()                                                                               # creating object of client class

clientSend = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)                  # creating the client socket for sending
clientSend.connect((SERVER_IP,PORT))                                                        # connecting the client socket to server's IP and PORT number

send_thread = cl.doSendRegesitration()                                                      # calling the function for registering the client for sending

clientRecv = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)                  # creating the client socket for receiving
clientRecv.connect((SERVER_IP, PORT))                                                       # connecting the client socket to server's IP and PORT number

recev_thread = cl.doRecvRegistration()                                                      # calling the function for registering the client for receiving

# Starting the sending and receiving threads
send_thread.start()                                                                     
recev_thread.start()