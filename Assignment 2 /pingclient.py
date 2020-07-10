from socket import *
import sys
import time
import datetime

host_ip = str(sys.argv[1])
port_number = int(sys.argv[2])

s = socket(AF_INET, SOCK_DGRAM)

i = 1

while(i<101):

	starttime = time
	data = ''
	while len(data.split())<3:
		starttime = time.time()
		message = 'ping ' + str(i) + ' ' + str(datetime.datetime.now().time())
		s.sendto(message, (host_ip, port_number))
		data, address = s.recvfrom(1024)
		splitData = data.split()
		if len(splitData)<3:
			print("Packet" + splitData[0] + " was dropped with message " + message)

	receivetime = time.time()
	rttime = receivetime - starttime
	print(data + ' ' + str(rttime))

	i = i + 1

s.close()
