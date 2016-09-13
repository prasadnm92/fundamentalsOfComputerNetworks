# RAW SOCKETS

## High level approach

- Designed the project using python and raw sockets. Implemented various functions including error handling, computation of checksum, retrieving hostname and filename and so on
- Designed classes for IP and TCP headers and methods to pack and unpack the header fields before sending and after receiving the packet, respectively

- Emulated the real working of a TCP/IP connection:

	- First, send a SYN packet to the server (retrieved from the input link) to setup a connection betwwen the client and the server

	- Then we wait till we receive a SYN/ACK packet from the sever

	- Finally, to complete the connection setup, we acknowledge the server with an ACK packet

	- Now, the actual request for the link input to the program is sent. We build a GET request and add it to the payload of the TCP header
	- We receive all the responses for this request, and if any fragment was not received (due to a packet drop, may be), we request it with a DUP ACK packet.
	- After all the data has been received, the server sends a FIN packet, for a connection teardown

	- We also send a FIN/ACK packet to complete the teardown




## Features implemented

-Computed the TCP header's checksum by building a pseudo header, adding every 16bit word, complementing and masking the final result

- The congestion window of the client is updated on every ACK that it sends. Also, it checks the advertised window size of the server

- Validate the incoming packets' checksum

- When a required packet does not arrive within 60 seconds of ACK-ing the previous response, we request for it again

- When the server does not send any packets for 180 seconds, then we terminate the program (due to a socket being closed, may be)




## Challenges faced


- Calculating and computing the Internet chekcsum for TCP header

- Setting the Sequence and Acknowledgment numbers for packets
- Effecient error handling at the network level
- Retrieving the correct server host name and file name to be downloaded from the input link



## Individual responsibilities


- Jyothi Prasad: Program flow and coding the basic logic

- Srinivasa Tumati: Stress tests and error handling




## References

- binarytides.com (Silvermoon's tutorial) & pythonforpentesting.com
: to understand the basic working of raw sockets and header construction

- packetlife.net: to understand the working of sequence and acknowledgment numbers

- howtogeek.com
: to understand the working of wireshark