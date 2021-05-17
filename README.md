# webProxy

# Program desc
This program is a "simple" TCP server on localhost:8888 that receives HTTP requests sent
from browser clients.

# usage

### `python3 webProxy.py [positive integer]`

The integer arguement determines when cached items expire in seconds.

When the servers up, open your favourite web browser (your fav is google chrome) and go onto some HTTP site through localhost 8888

Server can be (safely?) killed by sending a SIGINT or just ending the process.

# example page

one of my professor's homepages [http://localhost:8888/www.cs.toronto.edu/~ylzhang/](http://localhost:8888/www.cs.toronto.edu/~ylzhang/)

NOTE: cached files will be stored in the same directory as webproxy.py so I suggest putting it into a folder for easier cleanup.

Fun tip: Open chrome's dev tools (F12) and go on the 'Network' tab to see the server work its magic.

Now the second time you visit the same page, the proxy will try to grab cached non-expired files instead of directly trying to connect to the actual page.

# Misc Notes
code for forwarding HTTP requests and responses based on: 
https://pymotw.com/3/socket/tcp.html

code that lets TCP server handle simultaneous connections based on:
https://steelkiwi.com/blog/working-tcp-sockets/

cacheing is by my own monkey design where i just write whatever i get from recv() to files and read
from them when they exist instead of trying to connect a client socket to a url

I tried messing with injecting pages with new data but there seems to be some bugs
(most likely not doing the decoding of some encountered items properly)

tested on google chrome (ver. 88.0.4324.96 (Official Build)(x86_64)) on a macbook pro (Catalina ver. 10.15.7)

# Known Errors
-sometimes get a socket closed error but its super random and i cant seem to replicate it

-restarting server/client connection seems to "fix" it and client will try requesting stuff again
