# Module 9: Computer System Security

## Introduction
- **Overview**: Computer system security is of enormous importance in today's connected world.
- **Goals of the Module**:
  - Introduce terminologies in computer system security for operating system designers.
  - Learn cryptographic techniques used for authentication in distributed systems (via case study).
  - Discuss early terminologies articulated by **Jerome Saltzer**, demonstrating how computer visionaries foresaw information security issues before widespread computer connectivity.

## Firsts from Computing Pioneers
Reviewing early thought pieces provides historical context on information security.
- **Intergalactic Computer Networks (1963)**: An early memorandum conceptualizing global computer networks.
- **First Computer-to-Computer Communication (October 29, 1969)**: A host-to-host call made from UCLA to the Stanford Research Institute, recorded in the logbook of networking pioneer **Professor Leonard Kleinrock**.
- **First Email (1971)**: Written by **Ray Tomlinson** from BBN Technologies.
- **The Entire Internet in One Chart (March 1977)**: A single chart that mapped all the computers in the world.
- **Computer System Model (1975)**: Consisted of a mainframe computer (CPU, memory, I/O devices like disks) accessed via cathode-ray terminals in a time-shared manner, with no network connections.
- **Relevance**: Despite the isolated nature of early systems, Jerome Saltzer's seminal paper identified security issues and terminologies relevant today (e.g., denial of service, firewalls, sandboxing).

## Terminologies and Concepts (Jerome Saltzer, 1975)
Jerome Saltzer's seminal paper outlines critical issues in computer security.

### Privacy vs. Security
- **Privacy**: An individual's right and responsibility concerning when their information is released or protected. It deals with the user and the data they own.
- **Security**: A system function responsible for guaranteeing properties about the information it preserves on behalf of users. It ensures that data is protected and only released with the owner's authorization.
  - **Authentication**: The system must verify a user's identity before granting access.
  - **Protection**: The system must ensure accessed information does not violate the privacy of others. Protection and authentication are foundational to a secure system.

### Core Security Concerns
Saltzer identified a comprehensive set of security concerns:
1. **Unauthorized Information Release**: The system must prevent data from being released without the owner's authorization.
2. **Unauthorized Modification of Information**: The system must ensure that authorized access to view data does not improperly grant authority to modify it.
3. **Unauthorized Denial of Use**: The system must ensure that authorized users are not prevented from accessing their data. This is the first literature mention of what is now commonly known as a **Denial of Service (DoS)** attack.

### Goals of a Secure System
- **Negative Statements (Flawed Approach)**: Defining security as "preventing all violations" or being "bulletproof" is a negative statement. It is impossible to achieve or prove (similar to proving a program has no bugs) and gives a false sense of security.
- **Positive Statements (Preferred Approach)**: The goal should be stated positively, focusing on verifiable actions rather than impossible guarantees.

## Levels of Protection
*(No transcript available)*

## Design Principles
Saltzer laid out eight positive design principles that remain highly applicable to today's connected systems:

1. **Economy of Mechanisms**: Security mechanisms should be simple and easy enough to verify whether they work correctly.
2. **Fail-Safe Defaults**: Access to the system or information should be explicitly allowed. The default state should be a "fail-safe" mode rather than implicitly assuming access or using negative statements.
3. **Complete Mediation**: Security mechanisms must not take shortcuts. Every access must be fully checked against the authentication system.
   - *Example*: Caching a password file in memory for performance can cause security violations if the persistent storage copy changes but the cached copy does not.
4. **Open Design**: The system's design should be completely open and published, but the keys used for authentication must be protected.
   - **Underlying Tenet**: Cracking the design is useless without the keys. Breaking the keys should be computationally infeasible. It also fosters the idea that **detection is easier than prevention**.
5. **Separation of Privilege**: Requiring multiple conditions or parties to grant access.
   - *Example*: Two different individuals holding two separate keys required to open a bank vault.
6. **Least Privilege**: Users and processes should operate using the absolute minimum capabilities necessary to carry out a task based on a "need to know."
   - *Example*: Standard user privileges for daily tasks versus administrative/super-user privileges for installing software. This principle is the origin of modern organizational **firewalls**.
7. **Least Common Mechanism**: The design should limit shared security mechanisms to contain potential damage.
   - *Example*: Implementing a mechanism as a library outside the kernel rather than inside it limits the damage a malfunctioning mechanism can cause to the entire system.
8. **Psychological Acceptability**: Security mechanisms must be easy for the end-user to use and understand. A good user interface is crucial for ensuring users comprehend their actions.

### Key Takeaways from Design Principles
- **Positive Formulation**: All principles are stated positively, focusing on what the system *can* do, avoiding the impossible claim of being "bulletproof."
- **Timeless Applicability**: Despite being crafted in the early 1970s for disconnected systems, they perfectly apply to modern networks.
- **Core Strategy 1**: Build systems where cracking the protection boundary is computationally infeasible.
- **Core Strategy 2**: Build systems to **detect** violations when they occur rather than trying to entirely **prevent** them, as prevention is much harder to guarantee than detection.

## Conclusion
*(No transcript available)*
