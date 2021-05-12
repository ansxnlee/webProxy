'''
---PROGRAM DESCRIPTION---
This program is a "simple" TCP server on localhost:8888 that receives HTTP requests sent
from browser clients.
-------------------------

---Progress notes---
code for forwarding HTTP requests and responses based on: 
https://pymotw.com/3/socket/tcp.html

code that lets TCP server handle simultaneous connections based on:
https://steelkiwi.com/blog/working-tcp-sockets/

cacheing is by my own monkey design where i just write whatever i get from recv() to files and read
from them when they exist instead of trying to connect a client socket to a url

tried messing with injecting pages with new data but there seems to be some bugs
(most likely not doing the decoding of some encountered items properly)
----------------------

---KNOWN ERRORS---
-sometimes get a socket closed error but its super random and i cant seem to replicate it
-restarting server/client connection seems to "fix" it and client will try requesting stuff again
------------------

-tested on google chrome (ver. 88.0.4324.96 (Official Build)(x86_64)) on a macbook pro (Catalina ver. 10.15.7)
'''

import socket, sys, select, os, time

class Queue:
    '''used in conjunction with select to handle simultaneous connections'''
    def __init__(self):
        self.items = []

    def isEmpty(self):
        return self.items == []
    
    def enqueue(self, item):
        self.items.insert(0, item)

    def dequeue(self):
        return self.items.pop()

    def size(self):
        return len(self.items)

def getIP(msg):
    '''
    hacky way of getting necessary HTTP info to send to client sockets
    msg (str) - the full get request response from urls we visit

    Returns:

    domain_ip - ip address of url domain
    req - the get request to get to specific path in domain
    cache_name - cache filename for each request
    first - if the get request is the first html file (used for step 5)
    
    '''
    msg_split = msg.split('\r\n')
    url = msg_split[0].split(' ')[1]
    domain = url.split('/')[1]

    # ignore favicon get requests
    if(domain == 'favicon.ico'):
        return 'fav', 'fav', 'fav', 'fav'

    # use this ip to connect to client sockets
    domain_ip = socket.gethostbyname(domain)

    # get path from url and turn it into a GET request
    path = url.split('/')[2:]
    new_req = msg_split[0].split(' ')
    req = ''
    req += (new_req[0] + ' ')
    for i in range(len(path)):
        req += ('/')
        req += path[i]
    req += (' ' + new_req[2] + '\r\nHost: ' + domain + '\r\n\r\n')

    # determine appropriate cache filename
    cache_name_full = url.split('/')
    cache_name = ''
    for i in range(len(cache_name_full)):
        cache_name += cache_name_full[i]
    
    # determine if request is the first html request
    first = False
    test = msg_split[-5].split(' ')[0]

    # usually the last 5th header starts with 'Referer:' but the html's last 5th header
    # starts with 'Sec-Fetch-Dest:' idk man but it works so.. :)
    if((test == "Sec-Fetch-Dest:") and (test != "Referer:")):
        first = True
        
    return domain_ip, req, cache_name, first

def inject(page, itype, first):
    '''
    take a html page in byte form, "inject" html code into it, and return the modified version
    page - html page in byte form
    itype - either "fresh" or "cache" (determines the message)
    first - if its the first html request
    '''
    if(not first):
        return page

    try:
        html = page.decode()
    except UnicodeDecodeError:
        pass
    else:
        split = html.split('<head>', maxsplit=1)
        new = ''
        new += split[0]
        new += "  <p style=\"z-index:9999; position:fixed; top:20px; left:20px; width:200px;height:100px; background-color:yellow; padding:10px; font-weight:bold;\">"
        curr_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        if(itype=="fresh"):
            new += "FRESH VERSION AT: "
            new += curr_time
        else:
            new += "CACHED VERSION AS OF:"
            new += curr_time
        new += "</p>\n"
        new += "  <head>"
        new += split[1]
        return new.encode()

    return page



if(len(sys.argv) != 2 or not (sys.argv[1].isnumeric())):
    print("Usage: proxy.py [positive integer]")
    sys.exit()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setblocking(0)
server_address = ('localhost', 8888)
# print('starting on {} port {}'.format(*server_address))
sock.bind(server_address)
sock.listen(10)

expiration = int(sys.argv[1]) # time in seconds before a cache expires
inputs = [sock] # list of connections connecting to server
outputs = [] # tasks to be written to server
message_queues = {} # messages from each existing connection

# main loop to wait for requests, creates connections and cleans up sockets simultaneously
while True:
    readable, writable, exceptional = select.select(
        inputs, outputs, inputs)

    # handle incoming connections to server
    for s in readable:
        if s is sock:
            # create init connections
            connection, client_address = s.accept()
            connection.setblocking(0)
            inputs.append(connection)
            message_queues[connection] = Queue()
        else:
            # handle existing connection sending data to server
            full_message = ''

            # get full message in chunks
            while True:
                try:
                    data = s.recv(512)
                except ConnectionResetError:
                    pass
                else:
                    full_message += data.decode()
                    if len(data) < 512:
                        break;

            if full_message:
                message_queues[s].enqueue(full_message)
                # take received msg and add to writable tasks to be done
                if s not in outputs:
                    outputs.append(s)
            else:
                # no more data incoming, clean up connection
                if s in outputs:
                    outputs.remove(s)
                inputs.remove(s)
                s.close()
                del message_queues[s]



    # handle writables tasks to be done
    for s in writable:
        try:
            get_msg = message_queues[s].dequeue()
            domain_ip, req, cache_name, first = getIP(get_msg)
            if(domain_ip == "fav"):
                raise socket.gaierror
            
        except IndexError:
            outputs.remove(s)

        except KeyError:
            pass

        except UnicodeDecodeError:
            pass

        # temp solution to deal with favicon requests
        except socket.gaierror:
            pass
        
        else:
            # check for cache files if we can before we try connecting to actual server
            cache_checked = False
            expired = False

            cache_filename = cache_name.replace(".", "_")
            cache_filename += ".txt"

            try:
                r = open(cache_filename, 'rb')
            except FileNotFoundError:
                pass
            else:
                # check if file has expired
                modified_time = int(os.path.getmtime('./' + cache_filename))
                current_time = time.time()
                # equation might break in the future if time() changes in behaviour
                if((modified_time + expiration) > time.time()):
                    byte_data = r.read()
                    s.sendall(byte_data)
                    r.close()
                    cache_checked = True
                else:
                    # we should clear the expired file so fresh stuff can be appended
                    e = open(cache_filename, 'r+')
                    e.truncate(0)
                    e.close()

            # create client socket and forward response from url to browser 
            if(not cache_checked):
                web_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                web_address = (domain_ip, 80)
                web_sock.connect(web_address)

                try:
                    web_sock.sendall(req.encode())
                    full_msg = b''
                    while True:
                        web_data = web_sock.recv(512)
                        if(len(web_data) > 0):
                            #s.send(inject(web_data, "fresh", first))
                            full_msg += web_data
                            # cache data received
                            #f = open(cache_filename, 'ab')
                            #f.write(web_data)
                            #f.write(inject(web_data, "cache", first))
                            #f.close()
                        else:
                            break;
                    s.sendall(inject(full_msg, "fresh", first))
                    f = open(cache_filename, 'ab')
                    f.write(inject(full_msg, "cache", first))
                    #f.write(inject(web_data, "cache", first))
                    f.close()
                        

                except BrokenPipeError:
                    pass
                    
                finally:
                    web_sock.close()



    # handle select connection errors
    for s in exceptional:
        inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()
        del message_queues[s]

