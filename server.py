import socket
import threading

portNumber = 5001
localIP = "127.0.0.1"
map = {}


class Server:

    # Function for checking the message format sent by client.
    # Checking for this format: SEND [recipient username] Content-length: [length] [message of length given in the header]

    def checkForm(self, msg):                          

        arr = msg.split("\n")                            # splitting the message according to the \n character.
        a = arr[0].split(" ")                            # splitting first header line according to spaces.
        b = arr[1].split(" ")                           

        recipient = a[1]                                 # a[1] is the message recipient.
        length = b[1]                                    # b[1] is the message length.
        content = arr[3]                                 # arr[3] is the actual message content.

        form = True                                      # Initially the form is True but if it doesn'n match the form then we toggle it to False. 
        if(a[0] != "SEND" or b[0] != "Content-length:" or recipient == '' or content == '' or len(content) != int(length)):   # if invalid form appears.
            form = False

        return form, recipient, content



    # Function for message transfer from One Sender to One Receiver.

    def unicast(self, recipient, username, content, clientSoc):
        forwardSoc = map[recipient]                                 # getting the socket from the map enrty where the message to be forwarded (ie. receiving socket registered by client).
        forwardMsg = "FORWARD {}\nContent-length: {}\n\n{}".format(username,len(content),content)  # creating forward message in format: "FORWARD [username] Content-length: [length of message] [message content]".

        # Forwarding to receiver

        try:
            forwardSoc.send(forwardMsg.encode("utf-8"))             # forwarding the message to receiving socket.
        except:
            print("ERROR 102 : Unable to Send")
            print("Message not delivered from {} to {}".format(username,recipient))
            ack = "ERROR 102 Unable to send\n\n"                    # server to sender message if message is undelivered.
            clientSoc.send(ack.encode("utf-8"))                     # sending nack in format; "ERROR 102 Unable to send\n\n"


        # Getting response from receiver

        try:
            recv_msg = forwardSoc.recv(1024)                        # receiving the response from receiver.
        except:
            print("ERROR 102 : Unable to Send")
            print("Message not delivered from {} to {}".format(username,recipient))
            ack = "ERROR 102 Unable to send\n\n"                    # server to sender message if message ack not received. 
            clientSoc.send(ack.encode("utf-8"))                     # sending nack in format: "ERROR 102 Unable to send\n\n"


        recv_msg = recv_msg.decode("utf-8")
        arr = recv_msg.split(" ")


        # if response from receiver in format: "RECEIVED [sender username]"
        if(arr[0] == "RECEIVED" and arr[1] == "{}\n\n".format(username)):       # checking the message format.
            print('Message forwarded from {} to {}'.format(username,recipient)) # username is sender and recipient is receiver.
            ack_msg = "SEND {}\n\n".format(recipient)
            clientSoc.send(ack_msg.encode("utf-8"))                             # sending ack in format: "SEND [recipient name]\n\n"
                        


        # if response from receiver in format: "ERROR 103 Header Incomplete\n\n"
        elif(arr[0] == "ERROR" and arr[1] == "103" and arr[2] == "Header" and arr[3] == "Incomplete\n\n"):
            print("ERROR 103 Incomplete Header")
            print("Message not delivered from {} to {}".format(username, recipient))
            print("Closing connection of {}".format(username))
            nack_msg = "ERROR 103 Header Incomplete\n\n"
            clientSoc.send(nack_msg.encode("utf-8"))
            clientSoc.close()
            del map[username]                                                   # since message not received hence deleting the entry from map
             

        # if error does not fit in any format
        else:
            print('Unknown Error')
        


    # Function for message transfer from one sender to multiple receivers

    def broadcast(self, username, content, clientSoc):
        for recipient in map:

            if(recipient != username):
                forwardSoc = map[recipient]
                forwardMsg = "FORWARD {}\nContent-length: {}\n\n{}".format(username,len(content),content)

                #forward to receiver
                try:
                    forwardSoc.send(forwardMsg.encode("utf-8"))    # forwarding the message to sender.
                except:
                    print("ERROR 102 : Unable to Send")
                    print("Message not delivered from {} to {}".format(username, recipient))
                    ack = "ERROR 102 Unable to send\n\n"
                    clientSoc.send(ack.encode("utf-8"))
                    break


                        #response from receiver
                try:
                    recv_msg = forwardSoc.recv(1024)        # receiving the message from receiver.
                except:
                    print("ERROR 102 : Unable to Send") 
                    print("Message not delivered from {} to {}".format(username, recipient))
                    ack = "ERROR 102 Unable to send\n\n"
                    clientSoc.send(ack.encode("utf-8"))    # Sending nack in format: "Error 102 : Unable to send\n\n"
                    break


                recv_msg = recv_msg.decode("utf-8")
                arr = recv_msg.split(" ")


                # if response from receiver in format: "RECEIVED [sender username]"
                if(arr[0] == "RECEIVED" and  arr[1] == "{}\n\n".format(username)):          # checking the correctness of message format
                    print("Message successfully forwarded from {} to {}".format(username,recipient))
                    ack = "SEND ALL\n\n"                                   # If format is correct then send positive acknowledgment
                                                                                            
                            
                # if response from receiver in format: "ERROR 103 Header Incomplete\n\n"
                elif(arr[0]=="ERROR" and arr[1]=="103" and arr[2]=="Header" and arr[3]=="Incomplete\n\n"):  
                    print("ERROR 103 : Incomplete Header")
                    print("Message not delivered from {} to {}".format(username, recipient))
                    print("Closing connection of {}".format(username))
                    ack = "ERROR 103 Header Incomplete\n\n"
                    clientSoc.send(ack.encode("utf-8"))                                    # Sending nack in format: "ERROR 103 Header Incomplete\n\n"
                    clientSoc.close()   
                    del map[username]                                                       # Deleting user entry from the map
                    break
                        
                else:
                    print('Unknown Error')
                    break

        arr = ack.split(" ")

        if(ack == "SEND {}\n\n".format("ALL")):
            print('Message forwarded from {} to {}'.format(username,'ALL'))
            clientSoc.send(ack.encode("utf-8"))                                             # sending ack in format: "SEND [recipient name]\n\n"



    # Function for registering both sender and receiver
    # registered for both sending and receiving 
    def registerAndForward(self, clientSoc):
        
        try:
            msg = clientSoc.recv(1024)              # receiving registration message from client 
        except Exception as e:
            print('Client Inactive')
            print("Exception occured is : ", e)
            clientSoc.close()
            return 

        msg = msg.decode("utf-8")


        flag = False                                                         # boolean for continuing the process
        arr = msg.split("\n")                                                # splitting the message according to next line.
        a = arr[0].split(" ")

        if(a[0]=='REGISTER' and a[1]=='TOSEND'):                             # checking the message according to format: "REGISTER TOSEND [username]".
            if(a[2].isalnum()):
                username = a[2]                                              # l[2] gives username ie. name of client who want to send message to server.
                flag = True
                print("{} Successfully Registered to Send".format(username))
                ack = 'REGISTERED TOSEND {}\n\n'.format(username)                # creating the response messsage to client in format: "REGISTERED TOSEND [username]".
            else:
                print("The username should be Alphanumeric")

        elif(a[0]=='REGISTER' and a[1]=='TORECV'):                           # checking the message according to format: "REGISTER TORECV [username]".
            if(a[2].isalnum()):
                username = a[2]                                                  # l[2] gives username ie. name of client who want to receiver message from server.
                map[username] = clientSoc
                print("{} Successfully Registered to Receive".format(username))         
                ack = 'REGISTERED TORECV {}\n\n'.format(username)                # creating the response message to client in format: "REGISTERED TORECV [username]".
            else:
                print("The Username should be Alphanumeric")

        elif(len(a)>2 and not a[2].isalnum()):                               # if username is invalid then raise this error.
            print("ERROR 100 : Malformed username : {}".format(a[2]))
            ack = "ERROR 100 : Malformed username : {}\n\n".format(a[2])
            
        else:
            print('ERROR 101 : No user registered. Please register this user first.')                          # server response to client for sny communication before registration.
            ack = 'ERROR 101 No user registered\n\n'
            
        clientSoc.send(ack.encode("utf-8"))                                  # sending the responses created above to client.

        if not flag:
            return

        #server will recieve messages and forward them

        while True:
            try:
                ack = clientSoc.recv(1024)                                  # receiving message from client.
            except:
                print('Client Inactive')
                break

            ack = ack.decode("utf-8")

            form, recipient, content = self.checkForm(ack)

        
            if(form == False):                                               # if message found in invalid form
                print("ERROR 103 : Incomplete Header")
                print("Message not delivered from {} to {}".format(username,recipient))
                nack = "ERROR 103 Header Incomplete\n\n"                    # responding the client with an error.
                clientSoc.send(nack.encode("utf-8"))                        # sending the error message to client.
                clientSoc.close()                                           # closing the client socket
                del map[username]                                           # deleting socket entry form map
                break


            else:

                if recipient in map.keys():                                     # if client is in map means client is already registered.
                    self.unicast(recipient, username, content, clientSoc)       # calling unicast function for single recipient

                elif(len(map) > 1 and recipient == "ALL"):
                    self.broadcast(username, content, clientSoc)                # calling broadcast function for multiple recipients

                else:
                    print("ERROR 102 : Unable to Send") 
                    print("Message not delivered from {} to {}".format(username,recipient))
                    print("{} does not exist".format(recipient))
                    ack = "ERROR 102 Unable to send\n\n"
                    clientSoc.send(ack.encode("utf-8"))                         # sending nack in format: "ERROR 102 Unable to send\n\n"

                
    
            
svr = Server()                                  # Creating server object to call server methods

connections = 10                                              
server = socket.socket()                        # creating server socket
server.bind((localIP,portNumber))                 # binding the server socket to localhost and mentioned PORT number

server.listen(connections)                                # server is listening for connections
print("Server is Waiting for connections...")

while True:
    clientSoc, addr = server.accept()           # when server get any connection request at same port then then accepting that request
    thread = threading.Thread(target=svr.registerAndForward, args=(clientSoc,))     # creating multithreads for multiple connections at same port
    thread.start()                                                                  # starting the threads