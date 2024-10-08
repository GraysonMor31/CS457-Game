# Import the necessary libraries
import sys
import socket
import selectors
import traceback
import logging
import struct

# Import custom libraries
from gameclient import Message

# Set up logging for debug, info, error, and critical messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# crate an objet to manage socket connections
sel = selectors.DefaultSelector()


# create a request dictionary based on the action 
def create_request(action, value):
    if action == "add_player":
        log.info(f"Adding player with name {value}")
        return dict(
            type="text/json", # specify the request type
            encoding="utf-8", # specify the encoding 
            content=dict(action=action, value=value),
    )
    elif action == "get_state":
        log.info("Getting game state")
        return dict(
            type="text/json",
            encoding="utf-8",
            content=dict(action=action, value=value), # content with action and value
        )
    else:
        # error if the action is unknown 
       raise ValueError(f"Unknown action: {action}")
   

# establish a non-blocking connection to the server 
def start_connection(host, port, request):
    addr = (host, port)
    log.info(f"Starting connection to {addr}")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create a TCP socket
    sock.setblocking(False)
    sock.connect_ex(addr)
    
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    message = Message(sel, sock, addr, request)
    sel.register(sock, events, data=message)


# wait for events for up to seoncd 
# iterate throught triggered evetns
def main():
# check if the correct number of command-line arguments is provided 
    if len(sys.argv) != 5:
        log.error("Usage: python client.py <host> <port> <action> <value>")
        sys.exit(1) # exit if the usage is incorrect 

# extract command-line arguments 
    host, port = sys.argv[1], int(sys.argv[2])
    action, value = sys.argv[3], sys.argv[4]
    request = create_request(action, value)
    start_connection(host, port, request)
 
    try:
        while True:
            events = sel.select(timeout=1)
            for key, mask in events:
                message = key.data
                try:
                    message.process_events(mask)
                except Exception:
                # log any exceptions that occur during event processing
                    log.error(
                    "main: error: exception for",
                    f"{message.addr}:\n{traceback.format_exc()}",
                    )
                message.close()
            # Check for a socket being monitored to continue.
            if not sel.get_map():
                break
    except KeyboardInterrupt:
        log.info("Caught keyboard interrupt, exiting")
    finally:
        sel.close() # close the selector to release resources 

if __name__ == "__main__":
    main()