#!/usr/bin/env python3
from pybrickspc.messaging import BluetoothMailboxClient, TextMailbox

# This is the address of the server EV3 we are connecting to.
SERVER = "f0:45:da:13:1c:8a"

client = BluetoothMailboxClient()
mbox = TextMailbox("greeting", client)

print("establishing connection...")
client.connect(SERVER)
print("connected!")

mbox.send("ping")
mbox.wait()
print(mbox.read())
