# Module 10: Andrew File System and Security

## 1. Introduction
- **Overview**: The Andrew File System (AFS) was a bold experiment in the CS department at Carnegie Mellon University (CMU).
- **Goal**: Enable students across campus to walk up to any workstation, log in, and securely access all their files stored on a central server over a local area network (LAN).
- **Core Assumption**: The network itself is untrusted.
- **Focus**: Using AFS as a case study to understand how private key cryptographic infrastructure can provide security and authentication for a distributed file system available to a user community.

## 2. State of Computing Circa 1988
- **Environment**: CMU campus, user community, client workstations connected via LAN to file servers.
- **Workstations**: Local disks served as efficient caches for files downloaded from the server.
- **Vision of AFS (and Coda File System)**: Afford users the ability to access their personal information spread out throughout the campus securely and centrally.
- **Legacy**: Modest beginnings of today's cloud computing and mobile device concepts.

## 3. Andrew Architecture
- **Virtue (Client Environment)**: Client workstations connected by insecure network links to the LAN. Run a flavor of the UNIX operating system.
  - **Venus**: A special process running on the Virtue workstation responsible for user authentication and client caching of files fetched from the Vice servers. It acts as a surrogate for the user, utilizing RPC (Remote Procedure Call) to fetch files.
- **Vice (Server Environment)**: Secure servers (S1, S2, S3, etc.) located in a secure environment. Communication within Vice is secure (no encryption needed inside the boundary).
- **Communication Boundary**: Clients access Vice servers over insecure links, requiring encryption for data on the wire to prevent packet sniffing. Secure RPC is used for both passing parameters and receiving results.

## 4. Encryption Primer
- **Private Key Cryptosystem (Symmetric)**: 
  - Sender and receiver use the same symmetric key for encryption and decryption.
  - *Process*: Sender encrypts data with the private key to produce *ciphertext*, which travels over insecure links. Receiver decrypts it using the same key.
  - *Saltzer's Principle*: Publish the design but protect the keys. Breaking the key must be computationally hard.
  - *Challenge*: Key distribution problem, especially as organizations scale.
- **Public Key Cryptosystem (Asymmetric)**: 
  - Overcomes the key distribution problem.
  - *Keys*: A pair of keys—a *public key* (published, used for encryption) and a *private key* (kept secret, used for decryption).
  - *Process*: Sender encrypts data using the receiver's public key (a one-way function). Only the entity with the private key can decrypt the ciphertext back into the original data.

## 5. Private Key Encryption System in Action
- Two entities (A and B) exchange keys (e.g., $K_a$ for A, $K_b$ for B).
- A uses $K_a$ to encrypt a message to B. B decrypts it using $K_a$.
- **Requirement**: The receiver needs to know the identity of the sender to select the correct decryption key.
- **Implementation**: The sender's identity must be sent in *clear text* alongside the ciphertext. 

## 6. Challenges for the Andrew System
1. **Authenticating the User**: Unambiguously verifying the user's identity (e.g., proving "I am Kishore").
2. **Authenticating the Server**: Ensuring messages received by the client are from a genuine server, not a Trojan horse.
3. **Preventing Replay Attacks**: Ensuring intercepted packets cannot be resent to fool the sender or receiver.
4. **Isolating Users**: Shielding the user community from unintended or malicious interference by other users.
- **Design Decisions**: AFS uses secure RPC and private key cryptography (suitable for closed communities like a campus, avoiding the key distribution problem).
- **Dilemma**: Overexposing a username/password pair (as the clear text identity and private key) for all communications poses a security hole. 

## 7. The Andrew Solution: Three Classes of Interaction
To avoid overexposing the username and password, AFS uses ephemeral IDs and keys.
1. **Logging In**: Username and password are used exactly once to log in and securely authenticate with the server.
2. **RPC Session Establishment**: Establishing an RPC session to fetch or store files. Uses ephemeral IDs and keys.
3. **File System Access**: Actual secure RPC calls during the session for file operations (open, close, read, write).

## 8. Login Process
1. User logs in with a username and password.
2. The Virtue login process securely communicates this to the Vice login server.
3. The Vice login server returns two tokens:
   - **Clear Token**: A data structure containing a Handshake Key ($HK_c$).
   - **Secret Token**: An encrypted version of the Clear Token, encrypted with a key known only to Vice. This serves as an *ephemeral client ID* for the session (a meaningless bit string to sniffers).
4. Vice sends both tokens securely back to the Virtue login process. Virtue extracts the $HK_c$.
5. **Usage**: The secret token acts as the client ID for future communication. When Vice receives it, it decrypts it using its own key to extract the clear token and $HK_c$, verifying the client. Venus stores these tokens for the duration of the login session and discards them at logoff.

## 9. RPC Session Establishment (The "Bind" Operation)
- Venus establishes an RPC session using the Secret Token (as client ID) and the Handshake Key ($HK_c$) to encrypt messages.
- **Message 1 (Client to Server)**: Venus generates a new random number ($X_r$), encrypts it with $HK_c$, and sends it with the Secret Token.
  - Server decrypts the Secret Token, retrieves $HK_c$, and decrypts the message to get $X_r$.
- **Message 2 (Server to Client)**: Server increments $X_r$ by 1 ($X_r+1$), generates a new random number ($Y_r$), encrypts both with $HK_s$ ($HK_s = HK_c$), and sends them to the client.
  - *Authenticates Server*: Client decrypts the message. Seeing $X_r+1$ proves the server is genuine (it successfully decrypted $X_r$).
- **Message 3 (Client to Server)**: Client increments $Y_r$ by 1 ($Y_r+1$), encrypts it, and sends it back.
  - *Authenticates Client*: Server verifies $Y_r+1$, proving the client is genuine.
- **Replay Protection**: The use of new random numbers back and forth prevents replay attacks.

## 10. RPC Session Establishment (Continued)
- To prevent overexposing the Handshake Key ($HK_c$) during numerous file system operations, the server generates a **Session Key ($SK$)**.
- Server sends the $SK$ and a starting sequence number to the client, encrypted with $HK_c$.
- **File System Access**: For the remainder of the RPC session, Venus uses $SK$ for all secure RPC calls (opening, closing, writing files). The sequence number prevents replay attacks within the session.
- Once the RPC session ends, $SK$ is discarded. New RPC sessions require establishing a new $SK$ via the Bind operation using $HK_c$.

## 11. Login is a Special Case of Bind
- The initial login process is a special case of the Bind operation.
- **Client ID**: Username.
- **Handshake Key**: Password.
- After mutual authentication (validating client and server via random numbers), the server sends the Secret Token and Clear Token back to the client, encrypted using the password as the handshake key.

## 12. Putting It All Together
- **Login Session**: Exposes the username and password exactly once. Provides the Handshake Key ($HK_c$) and Secret Token, valid for the duration of the login session.
- **RPC Session**: Uses $HK_c$ to establish a session and obtain a Session Key ($SK$), valid only for that specific RPC session.
- **File Operations**: Uses the ephemeral Session Key ($SK$) for secure RPC calls.
- **Outcome**: Minimizes exposure of long-term credentials on insecure networks.

## 13. AFS Security Report Card
- **Mutual Suspicion**: **Yes** (Addresses suspicion from fellow users and the server).
- **User Protection from System**: **No** (Users must trust the system; no protection against a compromised system).
- **Confinement of Resource Usage**: **No** (Users can consume excessive network bandwidth; vulnerable to denial-of-service attacks).
- **Authentication**: **Yes** (Mutual authentication between client and server).
- **Server Integrity**: **No** (Servers are assumed to be in a secure physical environment; links inside the server network are unencrypted. Physical and social constraints are the only defenses, presenting a significant vulnerability).

## 14. Conclusion
- **AFS Extensions**: AFS extended UNIX file system privileges with groups, subgroups, positive/negative access rights (useful for quick revocation), and audit trails for administrators.
- **Takeaway**: Operating system designers can implement secure distributed systems by applying information security principles (like Saltzer's) and benchmarking against known vulnerabilities to safeguard against attackers.

## 15. Interview With Yousef Khalidi
- **Background**: Dr. Yousef Khalidi (Georgia Tech PhD, 1989; worked at Sun Microsystems on Solaris MC; currently a Distinguished Engineer at Microsoft leading the Azure Cloud platform).
- **Evolution of Systems**: 
  - Fundamentals (security, isolation, separation of policy/mechanism, replication, consistency) remain the same since the 1980s.
  - Scale has increased by orders of magnitude (from 3-5 machines to millions of VMs).
  - Increased scale requires adjustments (e.g., loose consistency, optimizing for mean time to recovery over perfect prevention).
- **Cloud Architecture Trends**:
  - Shift from "scale-up" (adding to one big mainframe) to "scale-out" (horizontal scaling with many commodity servers).
  - Flat networks for efficient east-west traffic (computation/replication) and north-south traffic.
  - Applications composed of existing services (storage, databases, caching) rather than built from scratch.
  - Applications must be designed to withstand failures and assume network latency/unreliability.
- **Edge Computing & Latency**: 
  - Content Distribution Networks (CDNs) handle streaming by placing data closer to users.
  - For chatty, latency-sensitive applications, computation must move closer to the edge or the device due to physics constraints.
- **Advice for Students**:
  - Build a strong foundation in Operating Systems, Distributed Systems, Programming Languages, and Algorithms.
  - Be curious and keep track of industry trends outside of school.
  - Develop soft skills and study the humanities: leadership, critical thinking, and concise communication are crucial for working in teams and driving projects in the industry.
  - Push the envelope and try "impossible" things in academia, where you aren't bound by industry shipping constraints.
