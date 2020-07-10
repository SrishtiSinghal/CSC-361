import socket
import sys
import random
import http_utils

# grab ip and port arguments from system
server_ip = str(sys.argv[1])
server_port = int(sys.argv[2])

# get the filename we want to request
filename = sys.argv[3]

# create a udp socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.settimeout(1.0)

debug = False

def isLost():
    return random.randint(1, 100) <= 5

# HTTPClient is the client made using UDP
class HTTPClient:
    def __init__(self):
        # start with a "closed" state
        self.state = "closed"
        self.seq_number = 0
        # establish a connection with the server
        self.handshake()

    def send_packet(self, message):
        self.last_packet_sent = (message, (server_ip, server_port))
        self.seq_number += 1
        
        if isLost():
            return

        udp_socket.sendto(message, (server_ip, server_port))
      # if debug:
         #   print("sent", message)

    
    def receive_packet(self, attempt=0):
        try:
            m, _ = udp_socket.recvfrom(1024)
            header, body = http_utils.parseMessage(m)
            if debug:
                print("received", header, body, m, attempt)
            return header, body
        except socket.timeout:
            if attempt == 5:
                print("5 attempts complete")
                raise
            self.resend_last_packet()
            return self.receive_packet(attempt+1)
            
    def resend_last_packet(self):
        if isLost():
            return 

        message, address = self.last_packet_sent
        udp_socket.sendto(message, address)

    def handshake(self):
        # send syn
        self.send_packet(http_utils.encodeMessage("SYN", self.seq_number, 0, ""))
        
        header, _ = self.receive_packet()
        if header[0] != "ACK":
            raise "Could not connect to the server. Did not receive an ACK"

        # send ACK back
        self.send_packet(http_utils.encodeMessage("ACK", self.seq_number, header[1]+1, ""))
        self.handshake_ack_num = header[1] + 1

    def sendRequest(self, requestString):
        self.send_packet(http_utils.encodeMessage("GET", self.seq_number, self.handshake_ack_num, requestString))
        
        response = ""

        while True:
            header, body = self.receive_packet()
            method = header[0]
            if method == "DATA":
                if header[2] != self.seq_number:
                    # drop the data packet if the ack number is incorrect
                    continue
                # send and ACK
                self.send_packet(http_utils.encodeMessage("ACK", self.seq_number, header[1]+1, ""))
                # append the packet data into the response string
                response = response + body
            elif method == "FIN":
                if header[2] != self.seq_number:
                    # drop the data packet if the ack number is incorrect
                    continue
                self.send_packet(http_utils.encodeMessage("ACK", self.seq_number, header[1]+1, ""))
                break
            else:
                # drop any other packets apart from DATA and FIN
                continue

        return response



def testHTTPClient(requestString):
    client = HTTPClient()
    return client.sendRequest(requestString)
    

# Now let us test our HTTP client by asking for a file from the sever
fileContentsFromServer = testHTTPClient("readFile:"+filename)

f = open(filename, "r")
fileContentsFromClient = f.read()
f.close()

if fileContentsFromServer == fileContentsFromClient:
    print(fileContentsFromServer)
    print("IDENTICAL!")
else:
    print(fileContentsFromServer)
    print("-----")
    print(fileContentsFromClient)
    print("Got a different respnose from server")




