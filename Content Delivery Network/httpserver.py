#!/usr/bin/python

import sys
import os
import urlparse
import BaseHTTPServer
import httplib2
import subprocess
import threading
import SocketServer #import ThreadingMaxIn
import sqlite3
import datetime
import zlib

origin_host = ''
origin_port = '8080'
dns_ip = '129.10.117.186' #IP address of the cs5700cdnproject.ccs.neu.edu - where the dnsserver is running
dns_port = 0

def error(message):
        sys.stderr.write("error: "+message+"\n")
        sys.exit(1)

class ThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
	pass

class serv_handler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_HEAD(url):
		global dns_ip
		global dns_port
		#dns_port = url.client_address[1]
		if (url.client_address[0] == dns_ip):
			c_ip = url.path[1:] #Removing '/' from path
			cmd = "scamper -c 'ping -c 1' -p 1 -i "+c_ip
			sc = subprocess.check_output(cmd, shell = True)
        		#print sc
        		rtt = sc.split(' ')[-2].split('/')[1]
			url.send_response(200)
			url.send_header("Cookie",rtt)
			url.end_headers()
	
	def do_GET(url):
		global origin_host
		req_time = datetime.datetime.now()
		cache = sqlite3.connect('patriots_table')
		req = cache.cursor()
		req.execute('SELECT contents FROM content_table WHERE url = ?', (url.path,))
		cntnt = req.fetchone()
		#If the content was found in the cache
		if (cntnt != None):
			print "Content fetching from the cache..."

                	url.send_response(200)
                	url.send_header("Content-type", "text/html")
                	url.end_headers()
			url.wfile.write(zlib.decompress(cntnt[0]))

			req.execute('UPDATE content_table SET hits = hits+1 AND tm_stmp = ? WHERE url = ?', (req_time, url.path))
		else:
			print "content fetching from the origin server..."
			head,content = httplib2.Http().request("http://"+origin_host+":"+origin_port+url.path)
			url.wfile.write(head)
			url.wfile.write(content)
			#calculating sizes of content and existing cache (in KB)
			cntnt_size = int(head['content-length'])/1024
			cache_size = os.stat('patriots_table').st_size/1024
			#caching the content
			new_size = cache_size + cntnt_size
			if (cntnt_size < 200):
				if (new_size <= 10000):
					req.execute('INSERT INTO content_table VALUES (?,?,?,?)', (url.path, (buffer(zlib.compress(content))), req_time, 1))
				else:
					req.execute('SELECT COUNT(*) FROM content_table')
					rows = req.fetchone()[0] 
					req.execute('DELETE FROM content_table WHERE url = (SELECT url FROM (SELECT * FROM (SELECT * FROM content_table ORDER BY tm_stmp ASC LIMIT ?) ORDER BY hits ASC LIMIT 1))', (rows,))
					req.execute('INSERT INTO content_table VALUES (?,?,?,?)', (url.path, (buffer(zlib.compress(content))), req_time, 1))
		cache.commit()
		cache.close()
					

def run_at(p):
        l_host = ThreadedHTTPServer(('', p), serv_handler)
        try:
                l_host.serve_forever()
        except KeyboardInterrupt:
                pass
        l_host.server_close()
        print "\nServer stopped by Keyboard Interrupt\n"

        
def main(port, origin):
	global dns_port
	dns_port = port + 64 #Listening for Head requests from dnsserver
	global origin_host
	origin_host = origin

	if not os.path.isfile('patriots_table'):
        	c_table = sqlite3.connect('patriots_table')
 		cache = c_table.cursor()
        	cache.execute('''CREATE TABLE content_table (url text, contents text,tm_stmp text, hits integer)''')
        	c_table.commit()
        	c_table.close()

	th = threading.Thread(target = run_at, args = (dns_port,))
	th.daemon = True
	th.start()

	run_at(port)


#main(45001,"ec2-52-4-98-110.compute-1.amazonaws.com")
#run as ./httpserver -p 45001 -o ec2-52-4-98-110.compute-1.amazonaws.com
if __name__ == '__main__':
	if(len(sys.argv) == 5):
                if(sys.argv[1] == '-p'):
                        port = sys.argv[2]
                        if not port.isdigit():
                                error ('Invalid port number')
                else:
                        error('Invalid input syntax')

                if(sys.argv[3] == '-o'):
                        origin = sys.argv[4]
                else:
                        error ('Invalid input syntax')
        else:
                error ('Invalid input')
	main(int(port),origin)
