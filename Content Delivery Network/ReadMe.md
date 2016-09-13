# CONTENT DELIVERY/DISTRIBUTION NETWORK

## DNS Server (./dnsserver -p <port> -n <name>)


> The DNS server runs on port number mentioned in the command line argument.

> It creates a socket that listens for UDP packets that are DNS requests.

> Once it binds to the host and port, it starts receiving data and retrieves the client IP, port information and the DNS packet ID as well.

> It then retrieves the name to be resolved by unpacking the packet.

> This name is verified with the name input as a command line argument.

> If they are the same, the latitude and longitude of the requested client is obtained by using the IP-info-DB API (same was done for the replica servers and stored prior to execution).

> Using the Latitude and Longitude values of the client and the precomputed replica servers, the closest server based on geo-location is determined by using distance formula.

> The returned server IP is packed into the Answer section of the DNS response and sent to the client.



Challeges faced:


> Understanding the DNS packet format, packing and unpacking was a challenge.





## HTTP Server (./httpserver -p <port> -o <origin>)

> The HTTP Server runs on port number mentioned in the command line arugument.
> It gets the request to serve a page as requested by the DNS server.
> The HTTP server looks up if the page already exists in its cache and serves it if present. Else it will contact the nearest replica server(based on geo location, computed by the DNS server) to fetch the page.
> The cache uses LRU algorithm to remove the least recently used page before inserting a new page when the cache size is full

Challenges faced:


>
 Determining the right algorithm to use for caching technique