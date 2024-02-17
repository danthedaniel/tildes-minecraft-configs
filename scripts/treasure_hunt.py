import socket
import select
import struct
import time
import signal
import random
import re
import os


class MCRconException(Exception):
    pass


def timeout_handler(signum, frame):
    raise MCRconException("Connection timeout error")


class MCRcon(object):
    socket = None

    def __init__(self, host, password, port=25575, timeout=5):
        self.host = host
        self.password = password
        self.port = port
        self.timeout = timeout
        signal.signal(signal.SIGALRM, timeout_handler)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type, value, tb):
        self.disconnect()

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self._send(3, self.password)

    def disconnect(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def _read(self, length):
        signal.alarm(self.timeout)
        data = b""
        while len(data) < length:
            data += self.socket.recv(length - len(data))
        signal.alarm(0)
        return data

    def _send(self, out_type, out_data):
        if self.socket is None:
            raise MCRconException("Must connect before sending data")

        # Send a request packet
        out_payload = (
            struct.pack("<ii", 0, out_type) +
            out_data.encode("utf8") + b"\x00\x00"
        )
        out_length = struct.pack("<i", len(out_payload))
        self.socket.send(out_length + out_payload)

        # Read response packets
        in_data = ""
        while True:
            # Read a packet
            (in_length,) = struct.unpack("<i", self._read(4))
            in_payload = self._read(in_length)
            in_id, in_type = struct.unpack("<ii", in_payload[:8])
            in_data_partial, in_padding = in_payload[8:-2], in_payload[-2:]

            # Sanity checks
            if in_padding != b"\x00\x00":
                raise MCRconException("Incorrect padding")
            if in_id == -1:
                raise MCRconException("Login failed")

            # Record the response
            in_data += in_data_partial.decode("utf8")

            # If there's nothing more to receive, return the response
            if len(select.select([self.socket], [], [], 0)[0]) == 0:
                return in_data

    def command(self, command):
        result = self._send(2, command)
        time.sleep(0.003)  # MC-72390 workaround
        return result


def list_players(rcon):
    response = rcon.command("list")
    match = re.search(r"\d+ players online: (.*)", response)
    if not match:
        return []

    return match.group(1).split(", ")


RCON_HOST = os.environ.get("RCON_HOST", "localhost")
RCON_PASSWORD = os.environ.get("RCON_PASSWORD", "password")
RCON_PORT = int(os.environ.get("RCON_PORT", 25575))


def main():
    odds = 8 # X in 1000

    if random.randint(0, 1000) >= odds:
        print("Skipping treasure hunt")
        return

    with MCRcon(RCON_HOST, RCON_PASSWORD, RCON_PORT) as rcon:
        players = list_players(rcon)
        if len(players) == 0:
            return

        rcon.command("treasurehunt start")


if __name__ == "__main__":
    main()
