from flask import Flask, request, Response
from flask_cors import CORS
from threading import Timer
from waitress import serve
from typing import Union
import logging
import os
import time
import traceback
import sys
import json
import requests
import random
from backendy_stuff.primes import find_next_mersenne_prime
from backendy_stuff.utils import only_if_awake

app = Flask(__name__, static_url_path="", static_folder="./frontend")
CORS(app)

if len(sys.argv) < 2:
    raise Exception("Must pass in port number")
MY_PORT = int(sys.argv[1])
if MY_PORT < 1024:
    raise Exception("Port number must be >= 1024")

# Randomly choose a human-readable name
names = ["Francescoli", "Gallardo", "Labruna", "Cavenaghi", "Enzo Perez"]
MY_NAME = names[MY_PORT % 10]

# Message log
LOGS = []

# Message types
PING = "PING"
PONG = "PONG"
PRIME = "PRIME"
MESSAGE_TYPES = set([PING, PONG, PRIME])

# List of all messages we've seen before (so as not to re-transmit duplicates)
RECEIVED_MESSAGES = set()

# Global state object for reading and altering state. You should read and write to this.
STATE = {
    "name": MY_NAME,
    "port": MY_PORT,
    # (key: port number, value: timestamp when we last heard from them)
    "peers": {},
    # Biggest Mersenne prime we've seen so far (starts at 2)
    "biggest_prime": 2,
    # Sender of the current biggest prime (starts as self)
    "biggest_prime_sender": MY_PORT,
    # Monotonically increasing message counter (we'll automatically increment this for you)
    "msg_id": 0,
    "awake": True,  # Only do things if this node is awake
}


def respond(
        msg_type: str,
        msg_id: int,
        msg_forwarder: int,
        msg_originator: int,
        ttl: int,
        data: Union[type(None), int]):
    '''
    This is where the meat of the P2P protocol happens.
    Upon receiving a message from a peer, what does each node do?

    Args:
        msg_type (str):
                    "PING", "PONG", or "PRIME" (you can use the constants PING/PONG/PRIME)
        msg_id (int):
                    The auto-incrementing message counter for each node
            msg_forwarder (int):
                    The port of the immediate node that sent you this message
            msg_originator (int):
                    The port of the node that created the original message (for a 0 TTL point-to-point message like a PING, this will be the same as the forwarder)
            ttl (int):
                    Time-to-live; the number of hops remaining in the lifetime of this message until it should be dropped. A 0 TTL message should not be forwarded.
            data (None or int):
                    The data in the message payload. For PINGs and PONGs, this will be None. For a PRIME message, the data field will contain the prime number.

    Returns:
        Nothing
    '''
    # Check if we already recieved this message
    if (msg_id, msg_originator) in RECEIVED_MESSAGES:
        return
    else:
        RECEIVED_MESSAGES.add((msg_id, msg_originator))

    if msg_originator == MY_PORT:
        return
    
    # Update last heard from
    update_last_heard_from(msg_forwarder)
    
    if msg_type == PING:
        pong = {
            "msg_type": PONG,
            "ttl":  0,
            "data": None,
        }
        send_message_to(msg_forwarder, pong, False)
    elif msg_type == PONG:
        pass
    elif msg_type == PRIME:
        # Add msg_originator to peer list
        update_last_heard_from(msg_originator)

        # Update biggest prime
        if STATE["biggest_prime"] < data:
            STATE["biggest_prime"] = data
            STATE["biggest_prime_sender"] = msg_originator

        # foward msg
        if ttl > 0:
            prime = {
            "msg_type": PRIME,
            "msg_originator": msg_originator,
            "ttl":  ttl - 1,
            "data": data,
            }

            for peer in STATE["peers"]:
                send_message_to(peer, prime, True)

    return


def update_last_heard_from(peer: int):
    '''
    Helper method to log when we last heard from a peer. We have to keep
    updating when we last heard from each peer, otherwise stale peers will
    churn out of our peer list after 10 seconds.
    '''
    STATE["peers"][peer] = time.time()


@only_if_awake(STATE)
def send_message_to(peer: int, message: dict, forwarded: bool):
    '''
    Send point-to-point message to a specific peer. Node-specific metadata is
    automatically added. You'll be using this function to send messages.
    **YOU WILL NOT NEED TO MODIFY THIS FUNCTION.**
    '''
    if type(peer) is not int:
        raise TypeError("Tried to send a message to non-integer: %d" % peer)
    if not "ttl" in message:
        raise Exception("Must have a TTL")
    if not "msg_type" in message or message["msg_type"] not in MESSAGE_TYPES:
        raise Exception("Must have a valid msg_type")
    if forwarded and "msg_originator" not in message:
        raise Exception(
            "Must have msg_originator in message if message was forwarded")

    message.update({
        "msg_forwarder": STATE["port"],
        "msg_id": STATE["msg_id"],
    })

    # If message originates from us, include that in the message
    if not forwarded:
        message.update({"msg_originator": STATE["port"]})

    log_message(message=message, received=False)

    try:
        req = requests.post("http://localhost:%d/receive" % peer, json=message)
    except requests.exceptions.RequestException as e:
        log_error(e)
    except ConnectionResetError as e:
        log_error(e)

    STATE["msg_id"] += 1


@only_if_awake(STATE)
@app.route("/receive", methods=["POST"])
def receive():
    '''
    Entry-point when the node receives a message from another node.
    Parses the request and forwards it along to `respond`.
    You should not need to modify this function.
    '''
    req_data = request.get_json()
    log_message(message=req_data, received=True)

    msg_type = req_data["msg_type"]
    msg_id = int(req_data["msg_id"])
    msg_forwarder = int(req_data["msg_forwarder"])
    msg_originator = int(req_data["msg_originator"])
    ttl = int(req_data["ttl"])
    data = req_data["data"]

    try:
        respond(msg_type, msg_id, msg_forwarder, msg_originator, ttl, data)
    except Exception as e:
        log_error(e)

    return "OK"


def log_message(message: dict, received: bool):
    logged = message.copy()
    logged.update({"timestamp": time.time()})
    if received:
        logged.update({"received": True})
    LOGS.append(logged)


def log_error(e):
    log_message(message={
        "error": str(e),
        "stack_trace": traceback.format_exc(),
    }, received=True)


@only_if_awake(STATE)
def send_pings_to_everyone():
    '''
    Routine that runs every 5 seconds; sends pings to every peer.
    '''
    ping = {
        "msg_type": PING,
        "ttl":  0,
        "data": None,
    }

    for peer in [*STATE["peers"]]:
        send_message_to(peer=peer, message=ping, forwarded=False)


@only_if_awake(STATE)
def evict_stale_peers():
    '''
    Routine that evicts any peers who we haven't heard from in the last 10 seconds.
    Runs every second.
    '''
    peers_to_remove = [p for p in [*STATE["peers"]] if is_stale(p)]

    for peer in peers_to_remove:
        STATE["peers"].pop(peer)


def is_stale(peer):
    current_time = time.time()
    return current_time - STATE["peers"][peer] > 10


@only_if_awake(STATE)
def generate_and_gossip_next_mersenne_prime():
    '''
    Routine that generates the next Mersenne prime and gossips it to our peers.
    Runs every 10 seconds.
    '''
    new_prime = find_next_mersenne_prime(STATE["biggest_prime"])
    STATE["biggest_prime"] = new_prime
    STATE["biggest_prime_sender"] = MY_PORT

    prime_message = {
        "msg_type": PRIME,
        "ttl": 2,
        "data": new_prime,
    }

    for peer in [*STATE["peers"]]:
        send_message_to(peer=peer, message=prime_message, forwarded=False)


@app.route("/message_log")
def message_log():
    '''
    Reads out the last 5 messages logged by this node.
    '''
    return json.dumps(LOGS[-5:])


@app.route("/reset", methods=["POST"])
def reset():
    '''
    Hard reset on all state for this node. Still gets initialized to having
    the same bootstrap peer it started with.
    '''
    global LOGS, RECEIVED_MESSAGES, STATE
    LOGS = []
    RECEIVED_MESSAGES = set()
    old_msg_id = STATE["msg_id"]
    STATE = {
        "name": MY_NAME,
        "port": MY_PORT,
        "peers": {},
        "biggest_prime": 2,
        "biggest_prime_sender": MY_PORT,
        "msg_id": old_msg_id + 1,
        "awake": True,
    }
    if len(sys.argv) >= 3:
        STATE["peers"][int(sys.argv[2])] = time.time()
    return "OK"


@app.route("/sleep", methods=["POST"])
def sleep():
    STATE["awake"] = False
    return "OK"


@app.route("/wake_up", methods=["POST"])
def wake_up():
    STATE["awake"] = True
    return "OK"


@app.route("/state")
def state():
    '''
    Reads out the current state of this node.
    '''
    return STATE


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/<int:node>/<method>", methods=["GET", "POST", "DELETE"])
def proxy(node, method):
    '''
    This lets each node act as a reverse proxy for the frontend. I.e., if
    the frontend is asking for a /state query, it can send a query to any node
    as /5002/state, and that query will get proxied through to node 5002, even
    if this is node 5001. This simplifies communication for the frontend.
    It's not relevant to your backend code.
    '''
    def stripped_headers(r):
        excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        return [(name, value) for (name, value) in r.raw.headers.items() if name.lower() not in excluded_headers]

    try:
        if request.method == "GET":
            r = requests.get(f"http://localhost:{node}/{method}")
            return Response(r.content, r.status_code, stripped_headers(r))
        elif request.method == "POST":
            r = requests.post(f"http://localhost:{node}/{method}", json=request.get_json())
            return Response(r.content, r.status_code, stripped_headers(r))
        else:
            raise Exception("Invalid request: " + request.method)
    except requests.exceptions.ConnectionError:
        return "ConnectionError", 500

class Interval(Timer):
    '''
    A timer that every X seconds, spawns a new thread to run some function.
    '''
    def run(self):
        # Sleep a random period before starting, to add a bit of jitter between nodes
        time.sleep(random.uniform(0, 2))

        while not self.finished.wait(self.interval):
            try:
                self.function()
            except Exception as e:
                log_error(e)

if __name__ == "__main__":
    print("Booting node %d (%s)" % (MY_PORT, MY_NAME))
    # If passed in another peer's port, initialize that peer
    if len(sys.argv) >= 3:
        STATE["peers"][int(sys.argv[2])] = time.time()

    # Send a ping to each of our peers once every 5 seconds
    ping_timer = Interval(5.0, send_pings_to_everyone)

    # If a peer hasn't responded to a ping or sent a ping in the last 10 seconds, evict them (we'll check once a second)
    eviction_timer = Interval(1.0, evict_stale_peers)

    # Generate and gossip out a new Mersenne prime every 10 seconds
    prime_timer = Interval(10.0, generate_and_gossip_next_mersenne_prime)

    ping_timer.start()
    eviction_timer.start()
    prime_timer.start()

    logging.getLogger('waitress').setLevel(logging.ERROR)
    serve(app, host="0.0.0.0", port=MY_PORT)
