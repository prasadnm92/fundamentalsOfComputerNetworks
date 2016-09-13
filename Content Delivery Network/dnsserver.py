#!/usr/bin/python
import sys
import socket
import os
import struct
import urllib
import threading
import httplib2

replica_servers = [
['ec2-52-4-98-110.compute-1.amazonaws.com', 'Origin server'],
['ec2-52-0-73-113.compute-1.amazonaws.com', 'N. Virginia'],
['ec2-52-16-219-28.eu-west-1.compute.amazonaws.com', 'Ireland'],
['ec2-52-11-8-29.us-west-2.compute.amazonaws.com', 'Oregon, USA'],
['ec2-52-8-12-101.us-west-1.compute.amazonaws.com', 'N.California, USA'],
['ec2-52-28-48-84.eu-central-1.compute.amazonaws.com', 'Frankfurt, Germany'],
['ec2-52-68-12-77.ap-northeast-1.compute.amazonaws.com', 'Tokyo, Japan'],
['ec2-52-74-143-5.ap-southeast-1.compute.amazonaws.com', 'Singapore'],
['ec2-52-64-63-125.ap-southeast-2.compute.amazonaws.com', 'Sydney, Australia'],
['ec2-54-94-214-108.sa-east-1.compute.amazonaws.com', 'Sao Paulo, Brazil']]

#------------------------------REPLICA IPs-----------------------------
'''
replica_ips = []
for ser in replica_servers:
	replica_ips.append(socket.gethostbyname(ser[0]))
print replica_ips
#sys.exit(0)
'''
replica_ips = ['52.4.98.110', '52.0.73.113', '52.16.219.28', '52.11.8.29', 
               '52.8.12.101', '52.28.48.84', '52.68.12.77', '52.74.143.5', 
	       '52.64.63.125', '54.94.214.108']

#---------------------------REPLICA LONG-LATs--------------------------
key = "a2996ddec460092af54048df251e7f6ede6963c50474f013636ef4c4fbc9ef4f"
'''
replica_lat_long = []
for ser in replica_ips:
	lat_long = []
	url = "http://api.ipinfodb.com/v3/ip-city/?key="+key+"&ip="+ser
	f = urllib.urlopen(url)
	addr_info = f.read()
	addr_info = addr_info.split(';')
	lat_long.append(addr_info[2])
	lat_long.append(addr_info[-3])
	lat_long.append(addr_info[-2])
	replica_lat_long.append(lat_long)
print len(replica_lat_long)
#sys.exit(0)
'''
replica_lat_long=[
['52.4.98.110', '39.0437', '-77.4875'], ['52.0.73.113', '39.0437', '-77.4875'],
['52.16.219.28', '53.344', '-6.26719'], ['52.11.8.29', '45.5234', '-122.676'],
['52.8.12.101', '37.7749', '-122.419'], ['52.28.48.84', '50.1155', '8.68417'],
['52.68.12.77', '35.6895', '139.692'], ['52.74.143.5', '1.28967', '103.85'],
['52.64.63.125', '-33.8679', '151.207'],
['54.94.214.108', '-23.5475', '-46.6361']]

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
port = 0
ip_cache = dict()	# {client_ip:closest_replica_ip}

def error (message):
        sys.stderr.write("error: "+message+"\n")
        sys.exit(1)

def ret_labels(msg, off):
	labels = []
	while 1:
		l, = struct.unpack_from("!B", msg, off)
		if (l & 0xC0) == 0xC0:
			ptr, = struct.unpack_from("!H", msg, off)
			off += 2
			return lables + ret_labels(msg, ptr & 0x3FFF), off

		if (l & 0xC0) != 0x00:
			raise StandardError("Unknown Label Encoding")

		off += 1
		if l == 0:
			return labels, off
		labels.append(*struct.unpack_from("!%ds" % l, msg, off))
		off += l

def ret_req_name(msg):
	id1, flags_, qdc, anc, nsc, arc = struct.unpack_from("!6H", msg)
	off = struct.Struct("!6H").size

	qns = []
	count = qdc
	while(count):
		qname, off = ret_labels(msg, off)
		qt, qc = struct.unpack_from("!2H", msg, off)
		off += struct.Struct("!2H").size
		qn = {"domain_name": qname, "query_type": qt, "query_class": qc}
		qns.append(qn)
		count = count - 1

	req = qns[0]
	req_n = req["domain_name"]
	req_t = req["query_type"]
	req_c = req["query_class"]
	client = ""
	if len(qns) == 1 and req_c == 1 and req_t == 1:
		for name in req_n:
			client = client+name+"."
		client = client[:-1]
	else:
		error("Invalid DNS request")
	return id1, client

def ret_send_packet(qname, s_ip, pid):
	p = struct.pack("!H", pid)	# Same ID as the request
	p += struct.pack("!H", 32768)  	# Flags 0x8000
	p += struct.pack("!H", 1)  	# Question Count
	p += struct.pack("!H", 1)  	# Answer Record Count
	p += struct.pack("!H", 0)  	# Authority Record Count
	p += struct.pack("!H", 0)  	# Additional Record Count

	#Build the question in terms of octets
	split_name = qname.split(".")
   	for n in split_name:
        	p += struct.pack("!B", len(n))
        	for byte in bytes(n):
            		p += struct.pack("!c", byte)
    	p += struct.pack("!B", 0)  	# End of String
    	p += struct.pack("!H", 1)  	# Query Type - 'A'
    	p += struct.pack("!H", 1)  	# Query Class - 'IN'
    	p += struct.pack("!H",49164) 	# Pointer to above packed qname(0xC0C0)
    	p += struct.pack("!H", 1)  	# Query Type - 'A'
    	p += struct.pack("!H", 1)  	# Query Class - 'IN'
    	p += struct.pack("!I", 0)  	# TTL for response to be cached
   	p += struct.pack("!H", 4)  	# Length of RDATA

    	#Building the answer in terms of octets
    	split_name = s_ip.split(".")
    	for dot_dec in split_name:
        	p += struct.pack("!B", int(dot_dec))

    	return p


def dist(x1, y1, x2, y2):
	x = x1 - x2
	y = y1 - y2
	dist = ((x**2) + (y**2)) ** 0.5
	return dist

def process_dns_req(r, c_host, c_port, name_to_resolve):
	global port
	dns_port = port + 64
        pid, req_name = ret_req_name(r)

        if req_name != name_to_resolve:
                error("Invalid name to be resolved")

	s_ip = ''

	if ip_cache.has_key(c_host):
		s_ip = ip_cache[c_host]
	else:
		#'''
                #Best IP based on RTT
                rtt_s = []
                for each_ec2 in replica_ips[1:]:
                        rtt_req = httplib2.Http()
			req = "http://"+each_ec2+":"+str(dns_port)+"/"+c_host
                        h = rtt_req.request(req, "HEAD")
                        rtt_s.append(float(h[0]['cookie']))
                min_rtt = min(float(rtt) for rtt in rtt_s)
                i = rtt_s.index(min_rtt)
                s_ip = replica_ips[i+1]
		'''
		#GeoIP
        	url="http://api.ipinfodb.com/v3/ip-city/?key="+key+"&ip="+c_host
        	c_info = urllib.urlopen(url).read().split(';')
	        lat = float(c_info[-3])
	        lng = float(c_info[-2])
	        d = []
	        for rep_ser in replica_lat_long[1:]:
	                rep_lat = float(rep_ser[1])
	                rep_lng = float(rep_ser[2])
	                rep_server = rep_ser[0]
	                d1 = dist(lat, lng, rep_lat, rep_lng)
			d.append(d1)
		min_d = min(float(dist) for dist in d)
	        j = d.index(min_d)
	        s_ip = replica_ips[j+1]
		'''
		ip_cache.update({c_host:s_ip})

	#s_ip(1) -----> best replica server based on RTT
	#s_ip(2) -----> best replica server based on GeoIP
	#print s_ip
        packet = ret_send_packet(req_name, s_ip, pid)
        n = s.sendto(bytes(packet), (c_host,c_port))
        #print n


def main(argc, argv):
	global port
	host = ''
	port = int(argv[2])
	name_to_resolve = argv[4]
	c_host = ''
	c_port = 0
	#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	#print "-----Socket created"
	try:
		s.bind((host,port))
	except socket.error as msg:
		error("Failed to bind: "+str(msg[1]))
	#print "-----Bind complete"

	threads = []
	while 1:
		try:
			r, addr = s.recvfrom(2048)
			if r:
				c_host =  addr[0]
				c_port = addr[1]
				#print c_host, c_port
				t1 = threading.Thread(target = process_dns_req, args = (r, c_host, c_port, name_to_resolve))
				t1.start()
				#break
				threads.append(t1)
		except KeyboardInterrupt:
			#print ""
			s.close()
			for t in threads:
				t.join()
			break


#main(5, ["./dnsserver", "-p", "45000", "-n", "cs5700cdn.example.com"])
#run as ./dnsserver -p 45000 -n cs5700cdn.example.com

if __name__ == "__main__":
	argc = len(sys.argv)
	argv = sys.argv
	if argc != 5:
		error("Invalid number of arguments. Run as\n./dnsserver -p <port> -n <name>")
	if int(argv[2])<40000 or int(argv[2])>65535:
		error("Invalid port number. Use (40000-65535)")
	main(argc, argv) 
