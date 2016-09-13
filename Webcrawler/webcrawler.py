#!/usr/bin/python
import sys
import socket
import re
from bs4 import BeautifulSoup
import datetime

host = "cs5700sp15.ccs.neu.edu"
port = 80
csrftoken = ""
session_id = ""
secrets = []
frontier = []
visited = ["http://www.ccs.neu.edu/home/choffnes/","http://www.northeastern.edu","mailto:choffnes@ccs.neu.edu"]

def get_csrftoken(response):
    l = -1
    while l <= len(response):
            j = response.find('<input', l+1)
            k = response.find('>', j)     #find all input tags
            if k == -1:
                break
            l = k
            input_tag = response[j+7:k-2] #retrieve the contents of an input tag
            #print input_tag
            if "csrf" in input_tag:
                csrftoken = input_tag.split(" ")[2].split("=")[1][1:-1]
                return csrftoken          #retrieve and return the required token value

def get_session_id(response):
    resp = response.split('\r\n\r\n')
    resp = resp[0].split('\r\n')          #retrieve only the header part of the recieved message
    s_id = session_id
    #print resp
    for x in resp:                        #in each line of the header, check for the Cookie header
        #print x+'\n'
        if 'Set-Cookie' in x:
            cookie_header = x.split(':')
            cookie_attr = cookie_header[1].strip()
            for y in cookie_attr.split(';'):    #search for session id in all of the attributes of the cookie header
                if "sessionid" in y:
                    s_id = y.split("=")[1]
    #print s_id
    return s_id                           #return the session id

def get_status_code(response):
    resp = response.split("\r\n")[0].split(" ")        #retrieve only the first line of the received message
    code = resp[1]                        #the code is the second word in the first line of the response
    return code                           #return the status code

def get_page_links(page):
    check_for_secret(page)                #first, check for any secret flags
    soup = BeautifulSoup(page)
    links = []
    for link in soup.find_all("a"):       #make a list of all links in the 'href' field of the anchor tags
        links.append(link.get("href"))    #return all these links, except for the last three because they
    return links[:-3]                     # are not a part of the fakebook website and should not be crawled

def check_for_secret(page):
    global secrets
    global start
    global stop
    soup = BeautifulSoup(page)
    for head in soup.find_all("h2", {"class" : "secret_flag"}):       #retrieve all <h2> tags with class attribute equal to 'secret_flag'
        sec = head.text                   #retrieve the text part of the header
        flag = sec.split(" ")[1].strip()
        secrets.append(flag)
        print flag                        #print the flag
    if len(secrets) == 5:                 #if all the 5 flags are found, exit
        stop = datetime.datetime.now()
        #print "Time take: ", (stop - start).seconds/60               #calculate time taken to run the crawler
        sys.exit(0)
    return

def get_location(response):
    for x in response.split('\r\n'):
        if 'Location' in x:               #look for the location header in the received response
            loc = x.split(' ')[1]
            return loc                    #return this new location
    error("3xx Status received, but no location header found")

def error (message):
    sys.stderr.write("error: "+message+"\n")
    sys.exit(1)

def main(argc, argv):
    global frontier
    global visited
    global session_id
    global secrets
    global start
    global stop

    if argc!=3:
        error("Invalid number of arguments")
    username = argv[1]
    password = argv[2]

    s = socket.socket()
    s.connect((host,port))

    #--------Retrieving login page
    request = "GET /accounts/login/ HTTP/1.1\r\nHost:cs5700sp15.ccs.neu.edu\r\nConnection: keep-alive\r\n\r\n"
    s.sendall(request)
    response = s.recv(1000000)
    #print response
    csrftoken = get_csrftoken (response)
    #print "CSRF Token: "+csrftoken

    #--------Logging in to Fakebook
    request = "POST /accounts/login/ HTTP/1.1\r\nHost:cs5700sp15.ccs.neu.edu\r\nContent-length: 109\r\nContent-Type: application/x-www-form-urlencoded\r\nConnection: keep-alive\r\nCookie: csrftoken="+csrftoken+";\r\n\r\nusername="+username+"&password="+password+"&csrfmiddlewaretoken="+csrftoken+"&next=%2Ffakebook%2F\r\n"
    s.sendall(request)
    response = s.recv(1000000)
    if "Please enter a correct username and password. Note that both fields are case-sensitive." in response:
        error("Please enter a correct username and password and try again")
    #print response
    session_id = get_session_id(response)
    #print "Session ID: "+session_id

    #--------Retrieving home page
    home_page = get_location(response)
    request = "GET "+home_page+" HTTP/1.1\r\nHost:cs5700sp15.ccs.neu.edu\r\nConnection: keep-alive\r\nCookie: csrftoken="+csrftoken+"; sessionid="+session_id+"\r\n\r\n"
    s.sendall(request)
    response = s.recv(1000000)
    #print response
    visited.append(home_page)

    links = get_page_links(response)
    frontier = frontier + links
    #print "start crawling...\n"

    #--------Start crawling
    start = datetime.datetime.now()

    while len(frontier) != 0:
        current_page = frontier.pop(0)
        if current_page in visited:
            continue

        s1 = socket.socket()
        s1.connect((host, port))
        request = "GET "+current_page+" HTTP/1.1\r\nHost:cs5700sp15.ccs.neu.edu\r\nConnection: keep-alive\r\nCookie: csrftoken="+csrftoken+"; sessionid="+session_id+"\r\n\r\n"
        s1.sendall(request)
        response = s1.recv(1000000)
        #print "Current page:\n%s" %current_page
        status = get_status_code(response)

        if status[0] == "2":
            if "Connection: close" in response.split("\r\n\r\n")[0]:
                temp_s = socket.socket()
                temp_s.connect((host,port))
                s1 = temp_s
                temp_s.shutdown(socket.SHUT_RDWR)
                temp_s.close()

        elif status[0] == "3":
            loc = get_location(response)
            temp_s = socket.socket()
            temp_s.connect((host, port))
            request = "GET "+loc+" HTTP/1.1\r\nHost:cs5700sp15.ccs.neu.edu\r\nConnection: keep-alive\r\nCookie: csrftoken="+csrftoken+"; sessionid="+session_id+"\r\n\r\n"
            temp_s.sendall(request)
            response = temp_s.recv(1000000)
            s1 = temp_s
            temp_s.shutdown(socket.SHUT_RDWR)
            temp_s.close()

        elif status[0] == "4":
            continue

        elif status[0] == "5":
            while get_status_code(response)[0] == '5':             #keep trying to request the server with a new socket till a valid response is received
                temp_s = socket.socket()
                temp_s.connect((host, port))
                request = "GET "+current_page+" HTTP/1.1\r\nHost:cs5700sp15.ccs.neu.edu\r\nConnection: keep-alive\r\nCookie: csrftoken="+csrftoken+"; sessionid="+session_id+"\r\n\r\n"
                temp_s.sendall(request)
                response = temp_s.recv(1000000)
                s1 = temp_s
                temp_s.shutdown(socket.SHUT_RDWR)
                temp_s.close()
        #print response
        visited.append(current_page)
        links = get_page_links(response)
        frontier = frontier + links
        s = s1

    s.shutdown(socket.SHUT_RDWR)
    s.close()

#main(3, ['./webcrawler','001783901','Q3LU2L9C'])

if __name__ == "__main__":
    main(len(sys.argv), sys.argv)
