### L1 - intro, history, internet architecture
- world-wide web vs internet?
- presentation layer: big-endian vs little-endian - why does this distinction matter, which one is used where? ASCII vs unicode? what does formatting a video stream entail in the presentation layer?
- session layer: what are checkpoints and token management in the session layer?
- transport layer: what actually is a "connection" if it is made of discrete packets instead of a continuous time-slice? 
- network layer: what is fragmentation/reassembly, packet scheduling and buffer management?
- link layer: what is PPP, 802.11, DOCSIS? what is data framing? what is CSMA/CD vs CSMA/CA in media access control (MAC)? 
- physical layer: what are twisted-pair copper wire, coaxial cable, single-mode fiber optics, CDMA and TDMA? how is timing synchronised? FDM vs TDM?
- how does STUN and UDP hole punching work to expose hosts behind a NAT box?
- tell me more about the **data**, **discovery**, **dissemination**, and **decision** planes of the 4D network architecture. how does it compare to SDN?
- repeater vs hub? why arrange them in a hierarchy? 
- is bandwidth a hardware or software limitation? is bandwidth simply the rate of processing the buffers?
- spanning tree algorithm is distributed - then how do they even make sure that the node ID is initialized to be globally unique? what makes a node become an orphan node instead of a leaf node in the spanning tree algorithm? as the network topology evolves, should a orphan node eventually become connected again, and if so, how does that happen? does the root node become a single point of failure in the network? 

### L2 - transport and application layer
- why exactly does TCP need a 4-tuple socket identifier, that is excessive for a UDP socket?
- Is there such thing as HTTP over UDP? A layer 7 protocol shouldn't dictate the underlying protocol right? Why does NFS use UDP when file integrity is important? what is UDP packet fragmentation?
- What does a "persistent" connection mean a network that uses discrete network packets? What is connection state and why are buffers involved?
- What is 1s complement and 2s complement? Why does the UDP receiver add the checksum as well, when the checksum doesn't take into account itself at the sender's side?
- Why does the server need its own sequence number, why not just rely on client_isn? What if the final client-to-server ACK isn't received in TCP handshake and teardown sequence? 
- How does "piggybacking" work in TCP full-duplex?
- UDP vs TCP socket API? how does the socket API handle full duplex? blocking vs non-blocking socket implementation? 
- Does sender and receiver interaction in ARQ referring to both the client request and server and response? Is handling missing segments (e.g. Go-back-n or selective ACKing) part of ARQ with window size? Do they also apply for stop-and-wait ARQ? are selective ACKing and fast retransmit the same thing? why timeout is necessary even for selective ACK - who implements the timeout and what happens after the timeout?
- Is the receive buffer and receive window per-socket or per-host? receive window is calculated by the receiving host, while congestion window is calculated by?
- What is ICMP source quench? What is ECN and QCN? what about AIMD vs CUBIC vs BBR? TCP Reno vs TCP Tahoe?
- why `Increment = MSS × (MSS / CongestionWindow)` in AIMD? why are there multiple ACK per RTT? doesn't MSS correspond to 1 packet transmission?