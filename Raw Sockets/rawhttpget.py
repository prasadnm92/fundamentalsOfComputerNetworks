#!/usr/bin/python
import sys
import socket
import random
import struct
import string
import os
import datetime

def error (message):
	sys.stderr.write("error: "+message+"\n")
	sys.exit(1)
    
def isFileName(f):
	if '.' in f:
		fname = f.rsplit('.',1)
		if len(fname[-1])>1 and len(fname[-1])<5:
			return True
	return False
    
def getHostName(page):
	if 'http://' in page:
		page = page.split('http://')[1]
	else:
		pass
	p = page.split('/')
	
	if len(p) == 1:					#If the URL ends in a slash ('/') or does not include any path, 
		file_name = 'index.html'		#then we must use the default filename - index.html
		path = '/'
	elif isFileName(p[-1]):
		file_name = p[-1]
		path = '/'+page.split('/',1)[1].rsplit('/',1)[0]+'/'
	else:
		file_name = 'index.html'
		path = '/'+page.split('/',1)[1]
	
	host = p[0]
	'''
	print 'Host Name: ',host
	print 'File Name: ',file_name
	print 'Path: ',path
	'''
	return host, file_name, path

#class for IP header construction
class IP(object):
        def __init__(self, s, d, payload):
                self.version = 4			# IPV4 header
                self.ihl = 5 				# Internet Header Length
                self.tos = 0 				# Type of Service
                self.tl = 20 + len(payload)		# kernel will calculate the total length of the packet
                self.id = random.randint(5000,65530)	# Packet ID
                self.flags = 0				# IP flags
                self.offset = 0				# Fragment offset value
                self.ttl = 255				# Time to live
                self.protocol = socket.IPPROTO_TCP	# Type of Transport layer protocol
                self.checksum = 0 			# kernel will fill the correct checksum
                self.source = socket.inet_aton(s)	# Source IP Address
                self.destination = socket.inet_aton(d)	# Destination IP Address

        def pack(self):
                ver_ihl = (self.version << 4) + self.ihl
                flags_offset = (self.flags << 13) + self.offset
                ip_header = struct.pack("!BBHHHBBH4s4s", ver_ihl, self.tos, self.tl, self.id, flags_offset,
                                        self.ttl, self.protocol, self.checksum, self.source, self.destination)

                return ip_header

#class for IP header retrieval from received packet
class Rec_IP(object):
	def __init__(self):
		pass

        def unpack(self, packet):
		packet = packet[0]
                self.ihl = (ord(packet[0]) & 0xf) * 4			# Internet Header Length
                iph = struct.unpack("!BBHHHBBH4s4s", packet[:self.ihl])
                self.ver = iph[0] >> 4					# Version of the IP protocol
                self.tos = iph[1]					# Type of Service
                self.tl = iph[2]					# Total length of the packet
                self.id = iph[3]					# Packet ID
                self.flags = iph[4] >> 13				# IP flags
                self.offset = iph[4] & 0x1FFF				# Fragment offset value
                self.ttl = iph[5]					# Time to live
                self.protocol = iph[6]					# Type of Transport layer protocol
                self.checksum = hex(iph[7])				# Header checksum
                self.source = socket.inet_ntoa(iph[8])			# Source IP Address
                self.destination = socket.inet_ntoa(iph[9])		# Destination IP Address
		self.options = packet[20:self.ihl]			# Header options
		self.payload = packet[self.ihl:]			# Packet payload
		self.list = [self.ver,self.ihl,self.tos,self.tl,self.id,self.flags,self.offset,self.ttl,self.protocol,self.checksum,
				self.source,self.destination,self.options,self.payload]
                return

#class for TCP header construction
class TCP(object):
        def __init__(self, sp, dp, payload):
                self.sport = int(sp)			# Source port
                self.dport = int(dp)			# Destination port
                self.seqn = random.randint(0,10000)	# Sequence number
                self.ackn = 0				# Acknowledgment number
                self.data_off = 5		 	# Data offset: 5x4 = 20 bytes
                self.reserved = 0			# Reserved field (0 for now)
                self.urg = 0				# URGENT flag
                self.ack = 0				# ACK flag
                self.psh = 0				# PUSH flag
                self.rst = 0				# RESET flag
                self.syn = 0				# SYN flag
                self.fin = 0				# FINISH flag
                self.window = socket.htons(100)		# cwnd - Congestion Window
                self.checksum = 0			# Header checksum
                self.urgp = 0				# Urgent pointer
                self.payload = payload			# Packet payload

        def pack(self, source, destination):
                data_offset = (self.data_off << 4) + 0
                flags = self.fin + (self.syn << 1) + (self.rst << 2) + (self.psh << 3) + (self.ack << 4) + (self.urg << 5)
                tcp_header = struct.pack('!HHLLBBHHH', self.sport, self.dport, self.seqn, self.ackn, data_offset, flags,
				self.window, self.checksum, self.urgp)

                #Pseudo header fields to compute checksum
                source_ip = socket.inet_aton(source)
                destination_ip = socket.inet_aton(destination)
                reserved = 0
                protocol = socket.IPPROTO_TCP
                total_length = len(tcp_header) + len(self.payload)

                #Pseudo header
                psh = struct.pack("!4s4sBBH", source_ip, destination_ip, reserved, protocol, total_length)
                psh = psh + tcp_header + self.payload
                tcp_checksum = checksum(psh)
                tcp_header = struct.pack("!HHLLBBH", self.sport, self.dport, self.seqn, self.ackn, data_offset, flags, self.window) + 				struct.pack("H",tcp_checksum) + struct.pack("!H", self.urgp)
                return tcp_header

#class for TCP header retrieval from received packet
class Rec_TCP(object):
	def __init__(self):
		pass

        def unpack(self, packet):
                cflags = {32:"U", 16:"A", 8:"P", 4:"R", 2:"S", 1:"F"}	# character representations for TCP header flags
                self.thl = (ord(packet[12])>>4) * 4			# Total header length
                tcph = struct.unpack("!HHLLBBHHH", packet[:20])
                self.sport = tcph[0] 					# Source port
                self.dport = tcph[1] 					# Destination port
                self.seqn = tcph[2] 					# Sequence number
                self.ackn = tcph[3] 					# Acknowledgment number
		self.data_off = tcph[4] >> 4				# Data offset: 5x4 = 20 bytes
		self.flag_byte = tcph[5]
                self.flags = ""						# Flags - the set flags are indicated by the presence
                for f in cflags:					#         of the corrosponding character representation
                        if tcph[5] & f:
                                self.flags+=cflags[f]
                self.window = tcph[6] 					# Advertised congestion Window
                self.checksum = hex(tcph[7]) 				# Header checksum
                self.urgp = tcph[8] 					# Urgent pointer
                self.options = packet[20:self.thl]			# TCP header options
                self.payload = packet[self.thl:]			# Packet payload
		self.list = [self.sport,self.dport,self.seqn,self.ackn,self.data_off,self.flags,self.window,
				self.checksum,self.urgp,self.payload]
                return

#Checksum function needed for calculation of checksum
def checksum(data):
    	size = len(data)

    	# Converting to even number, if odd
    	if (size & 1):  
        	size = size - 1
        	res_data = ord(data[size])  
    	else:
        	res_data = 0
     
    	for i in range(0, size, 2):
        	temp = ord(data[i]) + (ord(data[i+1]) << 8)
        	res_data = res_data + temp     
    	res_data = (res_data >> 16) + (res_data & 0xffff)
    	res_data = res_data + (res_data >> 16)

	#Complement and Mask to 4 byte short
    	res_data = ~res_data & 0xffff
    	return res_data


def main(argc, argv):

	if argc!=2:
		error("Invalid number of arguments")
	page = argv[1]

	#IP Table rule reset to not Drop packets
	os.system("iptables -A OUTPUT -p tcp --tcp-flags RST RST -j DROP")
	#Enabling promiscuous mode
	os.system("ifconfig eth0 promisc")

	host, f_name, path = getHostName(page)
	if (f_name == 'index.html') and (page[-1] != '/'):
		page = page + '/'
	dst_ip = socket.gethostbyname(host)
	dst_port = 80

	if 'http://' not in page:
		page = 'http://' + page

	h = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]]	
	src_ip = h[0][1].strip()
	src_port = random.randint(10000,65535)

	#-----Create a Raw Socket for sending data
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
	except socket.error , msg:
		error(msg)
	if s == -1:
        	error("Failed to create socket");

	#-----Create a Raw Socket for receiving data
	try:
		rs = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
	except socket.error , msg:
		error(msg)
	if rs == -1:
        	error("Failed to create socket");

	#-----Establish TCP connection (handshake)
	#"---------------------------SYN PACKET----------------------------"
	ip1 = IP(src_ip, dst_ip, '')
	ip_header1 = ip1.pack()

	tcp1 = TCP(src_port, dst_port, '')
	tcp1.syn = 1
	cwnd = 1
	tcp_header1 = tcp1.pack(src_ip, dst_ip)

	packet = ip_header1 + tcp_header1 + ''
	n = s.sendto(packet, (dst_ip, 0))
	rec_time = datetime.datetime.now() + datetime.timedelta(seconds=60)
	#print n

	#"-------------------------SYN/ACK PACKET--------------------------"
	response = ""
	rip1 = Rec_IP()
	rtcp1 = Rec_TCP()
	while (1):
		response = rs.recvfrom(200)
		if (response):
			rip1.unpack(response)
			response = rip1.payload
			rtcp1.unpack(response)
			if ('S' in rtcp1.flags) and ('A' in rtcp1.flags) and (rip1.source == dst_ip):
				break
				
		elif datetime.datetime.now() > rec_time:
			n = s.sendto(packet, (dst_ip, 0))
	cwnd = min(1000,cwnd+99)
	awnd = rtcp1.window

	#"--------------------------ACK PACKET----------------------------"
	ip2 = IP(src_ip, dst_ip, '')
	ip_header2 = ip2.pack()

	tcp2 = TCP(src_port, dst_port, '')
	tcp2.ack = 1
	tcp2.seqn = rtcp1.ackn
	tcp2.ackn = rtcp1.seqn + 1
	tcp_header2 = tcp2.pack(src_ip, dst_ip)

	packet = ip_header2 + tcp_header2 + ''
	n = s.sendto(packet, (dst_ip, 0))

	#"------------------------HANDSHAKE DONE--------------------------"

	#-----Build GET request
	request = "GET "+page+" HTTP/1.0\nHost: "+host+"\nConnection: keep-alive\r\n\r\n"

	#"----------------------GET-REQUEST PACKET------------------------"

	ip3 = IP(src_ip, dst_ip, request)
	ip_header3 = ip3.pack()	

	tcp3 = TCP(src_port, dst_port, request)
	tcp3.ack = 1
	tcp3.psh = 1
	tcp3.ackn = tcp2.ackn
	tcp3.seqn = tcp2.seqn
	tcp_header3 = tcp3.pack(src_ip, dst_ip)

	packet = ip_header3 + tcp_header3 + request
	n = s.sendto(packet, (dst_ip, 0))

	#"-------------------------REQUEST SENT----------------------------"

	timeout_time = datetime.datetime.now() + datetime.timedelta(seconds = 180)
	req_data = ''
	first = 1			# To check if no packet is being received from the server

	payload_length = len(request)
	resend_packet = packet		# To request for an unreceived packet in sequence
	rip3 = Rec_IP()
	rtcp3 = Rec_TCP()

	#-----Expected Acknowledgment and Sequence numbers for the next packet
	exp_ackn = tcp3.seqn + payload_length
	exp_seqn = tcp3.ackn

	while (1):
		t = datetime.datetime.now() + datetime.timedelta(seconds = 60)
		response = rs.recvfrom(65535)
		if (response):
			rip3.unpack(response)
			response = rip3.payload
			rtcp3.unpack(response)

			#-----PSH flag indicates the presence of some data in the packet
			if ('P' in rtcp3.flags) and ('A' in rtcp3.flags) and (rip3.source == dst_ip) and (rtcp3.seqn == exp_seqn) and (rtcp3.ackn == exp_ackn) and (rtcp3.sport == 80) and (rtcp3.dport == src_port) and ('F' not in rtcp3.flags):

				#-----For status codes other than 200
				if (first == 1) and ('200 OK' not in rtcp3.payload):
					error("Invalid response (Received something other than '200 OK')")
				first = 0

				#-----Validating the received TCP checksum
				sip = socket.inet_aton(src_ip)
				dip = socket.inet_aton(dst_ip)
				res = 0
		                proto = socket.IPPROTO_TCP
				tot_len = len(rip3.payload)
				psh = struct.pack("!4s4sBBH", sip, dip, res, proto, tot_len)
				psh = psh + rip3.payload[:(len(rip3.payload)-len(rtcp3.payload))]
				chk_sum = checksum(psh)
				#print chk_sum

				req_data += rtcp3.payload
				cwnd = min(1000,cwnd+99)

				ip3_ = IP(src_ip, dst_ip, '')
				ip_header3_ = ip3_.pack()	
			
				tcp3_ = TCP(src_port, dst_port, '')
				tcp3_.ack = 1
				tcp3_.seqn = rtcp3.ackn
				tcp3_.ackn = rtcp3.seqn + len(rtcp3.payload)
				tcp_header3_ = tcp3_.pack(src_ip, dst_ip)

				packet = ip_header3_ + tcp_header3_ + ''
				n = s.sendto(packet, (dst_ip, 0))

				resend_packet = packet
				exp_ackn = tcp3_.seqn
				exp_seqn = tcp3_.ackn
				continue

			#-----If the required packet does not come within 60sec, request for it again	
			elif (datetime.datetime.now() > t):
				n = s.sendto(resend_packet, (dst_ip, 0))
				cwnd = 1
				continue

			#-----FIN flag indicates a connection teardown request
			elif ('F' in rtcp3.flags) and (rip3.source == dst_ip) and (rtcp3.seqn == exp_seqn) and (rtcp3.ackn == exp_ackn) and (rtcp3.sport == 80) and (rtcp3.dport == src_port):
				if ('P' in rtcp3.flags):
					req_data += rtcp3.payload

				cwnd = min(1000,cwnd+99)

				ip3_ = IP(src_ip, dst_ip, '')
				ip_header3_ = ip3_.pack()	
			
				tcp3_ = TCP(src_port, dst_port, '')
				tcp3_.ack = 1
				tcp3_.fin = 1
				tcp3_.seqn = rtcp3.ackn
				tcp3_.ackn = rtcp3.seqn + 1
				tcp_header3_ = tcp3_.pack(src_ip, dst_ip)

				packet = ip_header3_ + tcp_header3_ + ''
				n = s.sendto(packet, (dst_ip, 0))
				break

		#-----If no packet was received for more than 3min, then exit
		elif (datetime.datetime.now() > timeout_time):
			error("Timed Out!\nExiting...")

	#-----Store the downloaded data
	req_data = req_data.split('\r\n\r\n')[1]
	f = open(f_name , 'w')
	f.write(req_data)
	f.close()

	rs.close()
	s.close()

if __name__ == "__main__":
    main(len(sys.argv), sys.argv)

'''
Sample Inputs:
./rawhttpget http://www.ccs.neu.edu
./rawhttpget http://david.choffnes.com/classes/cs4700sp15/project4.php
./rawhttpget http://david.choffnes.com/classes/cs4700sp15/
./rawhttpget david.choffnes.com/classes/cs4700sp15/2MB.log
./rawhttpget david.choffnes.com/classes/cs4700sp15/50MB.log
./rawhttpget david.choffnes.com/classes/cs4700sp15/10MB.log
'''
