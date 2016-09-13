#!/usr/bin/python
import sys
import subprocess

replica_servers = [
'ec2-52-0-73-113.compute-1.amazonaws.com',
'ec2-52-16-219-28.eu-west-1.compute.amazonaws.com',
'ec2-52-11-8-29.us-west-2.compute.amazonaws.com',
'ec2-52-8-12-101.us-west-1.compute.amazonaws.com',
'ec2-52-28-48-84.eu-central-1.compute.amazonaws.com',
'ec2-52-68-12-77.ap-northeast-1.compute.amazonaws.com',
'ec2-52-74-143-5.ap-southeast-1.compute.amazonaws.com',
'ec2-52-64-63-125.ap-southeast-2.compute.amazonaws.com',
'ec2-54-94-214-108.sa-east-1.compute.amazonaws.com']

def error(message):
        sys.stderr.write("error: "+message+"\n")
        sys.exit(1)

def main(argv, argc):
	port = argv[2]
	origin_server = argv[4]
	name = argv[6]
	username = argv[8]
	keyfile = argv[10]

	#Disable pop confirmation for hostkey checking
	hostcheck = "StrictHostKeyChecking=no"

	dns_server = "cs5700cdnproject.ccs.neu.edu"
	usr_at_dns = username+"@"+dns_server

	# Stopping dnsserver on DNS server
	try:
		cmd1 = "ssh -o "+hostcheck+" -i "+keyfile+" "+usr_at_dns+" pkill -f dnsserver"
   		subprocess.Popen(cmd1.split(' '),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		#print "Killed dnsserver"
	except:
   		error("Failed to stop dnsserver")

	# Stopping httpserver on all replica servers
	for each in replica_servers:
    		usr_at_rep = username+"@"+each
    		try:
			cmd2 = "ssh -o "+hostcheck+" -i "+keyfile+" "+usr_at_rep+" pkill -f httpserver"
        		subprocess.Popen(cmd2.split(' '),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			#print "Killed httpserver"
    		except:
        		error("Failed to stop httpserver at all Replicas")

	#print "CDN Terminated Successfully"

if __name__ == "__main__":
	argc = len(sys.argv)
	argv = sys.argv

	if argc!=11 or argv[1]!="-p" or argv[3]!="-o" or argv[5]!="-n" or argv[7]!="-u" or argv[9]!="-i":
		usage = "./[deploy|run|stop]CDN -p <port> -o <origin> -n <name> -u <username> -i <keyfile>"
		error("Invalid arguments.\nUsage: "+usage)

	main(argv,argc)

