import socket
import sys
import random
import http_utils

# grab ip and port arguments from system
ip = str(sys.argv[1])
port = int(sys.argv[2])

# create a udp socket
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.settimeout(1.0)

debug = False

def isLost():
    return random.randint(1, 100) <= 5

class HTTPServer:
    def send_packet(self, message, address):
        self.last_packet_sent = (message, address)
        self.seq_number += 1
        
        if isLost():
            return 

        udp_socket.sendto(message, address)
        if debug:
            print("sent", message, len(message))


    def receive_packet(self, attempt=0):
        try:
            data, address = udp_socket.recvfrom(1024)
            header, body = http_utils.parseMessage(data)
            if debug:
                print("received", header, body, attempt, self.state)
            
            return header, body, address
        except socket.timeout:
            if attempt == 5:
                print ("5 attempts complete")
                raise

            if self.state == "waiting":
                # if the server is in waiting state, no need to resend last packet or have limited retries
                return self.receive_packet()

            self.resend_last_packet()
            return self.receive_packet(attempt+1)

    def resend_last_packet(self):
        if isLost():
            return
        message, address = self.last_packet_sent
        udp_socket.sendto(message, address)

    def send_data_packet(self, ack_num, address):
        packetBody = self.packets_to_send[self.packet_num]
        if debug:
            print("packet:",packetBody, len(packetBody))
        message = http_utils.encodeMessage("DATA", self.seq_number, ack_num, packetBody)
        self.send_packet(message, address)

    # handler is a function that can process an HTTP request to create an HTTP response
    def __init__(self, handler):
        udp_socket.bind((ip, port)) # start listening in ip and port
        self.state = "waiting"
        self.seq_number = 0
        print("Listening for requests now")

        while True:
            header, body, address = self.receive_packet()
            
            method = header[0]

            if method == "SYN":
                if self.state != "waiting":
                    # if not in "waiting" drop any SYN packets
                    continue
                # respond with an ACK
                self.send_packet(http_utils.encodeMessage("ACK", self.seq_number, header[1]+1, ""), address)
                self.state = "handshake"

            elif method == "ACK":
                if self.state == "handshake":
                    if header[2] != self.seq_number:
                        # drop if the ACK is not for the ACK packet we just sent
                        continue
                    
                    self.state = "connected"
                elif self.state == "finished":
                    if header[2] != self.seq_number:
                        # drop if the ACK is not for the FIN packet we just sent
                        continue
                    
                    self.state = "waiting"
                elif self.state == "sending_data":
                    if header[2] != self.seq_number:
                        # drop if the ACK is not for the packet we just sent
                        continue
                    
                    self.packet_num += 1
                    
                    if self.packet_num == len(self.packets_to_send):
                        # send FIN
                        self.send_packet(http_utils.encodeMessage("FIN", self.seq_number, header[1]+1, ""), address)
                        self.state = "finished"
                    else:
                        self.send_data_packet(header[1]+1, address)
                else:
                    # drop "ACK" if not server not in "handshake" or "sending_data" state
                    continue
            elif method == "GET":
                if self.state != "connected":
                    # drop if the server not in the correct state
                    continue

                response = handler(body).encode()
                
                # TODO: break the response in packets and send it while receiving ACKs
                totalLength = len(response)
                
                maxPacketBodySize = 1024 - 5 # 5 bytes for header and 1024 is the total packet size
                
                # create small packets of the response
                responsePackets = [response[i:i+maxPacketBodySize].decode() for i in range(0, totalLength, maxPacketBodySize)]
                
                self.state = "sending_data"

                self.packets_to_send = responsePackets
                self.packet_num = 0

                self.send_data_packet(header[1] + 1, address)

            else:
                # return 404 for everything else
                response = "method not supported"
                self.send_packet(http_utils.encodeMessage("DATA", self.seq_number, header[1]+1, response), address)
                
        

def handler(requestString):
    requestParts = requestString.split(":")
    if requestParts[0] == "ping":
        return "pong"
    elif requestParts[0] == "readFile":
        if len(requestParts) < 2:
            return "ERROR: filename missing"

        filename = requestParts[1]

        try:
            f = open(filename, "r")
            response = f.read()
            f.close()
        except:
            return "Error: could not read the requested file"
        
        return response

    return "ERROR: Request not supported"

server = HTTPServer(handler)
    
    
