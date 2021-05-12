# webProxy

# ---PROGRAM DESCRIPTION---
This program is a "simple" TCP server on localhost:8888 that receives HTTP requests sent
from browser clients.

# ---Progress notes---
code for forwarding HTTP requests and responses based on: 
https://pymotw.com/3/socket/tcp.html

code that lets TCP server handle simultaneous connections based on:
https://steelkiwi.com/blog/working-tcp-sockets/

cacheing is by my own monkey design where i just write whatever i get from recv() to files and read
from them when they exist instead of trying to connect a client socket to a url

I tried messing with injecting pages with new data but there seems to be some bugs
(most likely not doing the decoding of some encountered items properly)

# ---KNOWN ERRORS---
-sometimes get a socket closed error but its super random and i cant seem to replicate it
-restarting server/client connection seems to "fix" it and client will try requesting stuff again

tested on google chrome (ver. 88.0.4324.96 (Official Build)(x86_64)) on a macbook pro (Catalina ver. 10.15.7)
