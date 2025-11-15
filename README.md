# WebSocket Relay

This program is a relay node network, to transmit messages via websocket, similar to MQTT, or other PubSub networks.
Each program is a node, that can connect to other nodes, so that clients can have low-latency messaging, with the ability
to send messages globally.

The idea is to have several small cloud servers (Low memory, low CPU, but decent networking), and run a node on each.
The nodes are aware of a few others (But the intention is that they're not aware of the entire network, easier configuration)
When a node turns on, it will try to connect to the ones it knows about, and will use them to learn more about the network.
Eventually, a node will either know the entire network, or run out of "intra-node connections", and it can use those
to send intra-node messages.
Theoretically, running the nodes as colocations in a datacenter (VPS, Dedicated Server, etc) means that they will have
low-latency "dark fibre" or direct connections to other datacenters, so that the node network can have lower latency globally.

These messages are primarily for global dispersion of normal messages, but can also include command and control messages to
administrate the network, or gather information about it.

The nodes will disperse the active channels, so that all of the nodes keep track of the channels, and easily send messages to each other.
There will be a race condition on two nodes each trying to open the same channel, however this will try to be avoided by having the
nodes ask each other (explicitly confirm) before opening the new channel. Nodes will advertise channels they have open regardless,
but there is always the chance of the two channels being open at the same time, which could lead to a data leak (if the channel is password-protected),
or if the channel is open, then theoretically there shouldn't be a real problem.

The clients will connect to the closest server (Either hard-coded, or using the Master Node to get the closest node), and connect.
That way, the clients connected can have low-latency communication with geographically close clients, and the node network will handle
multiple clients from different geographic regions, without every client needing to connect to the same node.

Clients will connect, subscribe to topics, and then they can send and receive messages as if they had direct websockets to each other.