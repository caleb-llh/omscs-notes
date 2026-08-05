# Module 8: Virtualization

## Introduction
- **Evolution of OS Design**: The drive for extensibility in operating system services led to innovations in the internal structure of operating systems and the dynamic loading of modules.
- **Virtualization**: Takes the vision of extensibility to a new level by allowing the simultaneous coexistence of entire operating systems on top of the same hardware platform.

## Contexts of Virtualization
The term "virtualization" appears across various computing and cultural contexts:
- **Virtual Memory Systems**
- **Data Centers & Cloud Computing** (e.g., AWS, Microsoft)
- **Virtual Machines**: Java Virtual Machine (JVM), Dalvik (Android)
- **Desktop/Workstation Virtualization**: VirtualBox, VMware Workstation
- **Historical/Pioneering Systems**: IBM VM 370 (the "mother of all virtualization" from the 1960s/70s)
- **Pop Culture & Tech Hype**: Google Glass, the movie *Inception*

## Platform Virtualization
- **Virtual Platforms**: An operating system running on top of some hardware that provides the illusion of an exclusive platform.
- **Motivation (Alice Inc. vs. Bala Inc.)**: 
  - *Alice Inc.* can afford dedicated physical servers.
  - *Bala Inc.* wants the exact same capabilities and abstractions but at a fraction of the cost. Virtual platforms provide this experience.
- **User Perspective**: Users treat the virtual platform as a black box; they only care that their applications run correctly.
- **Designer Perspective**: Operating system designers focus on providing the illusion of a dedicated platform without incurring the associated hardware acquisition and maintenance costs.

## Utility Computing
- **Resource Sharing**: Multiple user communities (e.g., Bala, Piero, Kim) share the same underlying hardware resources.
- **Bursty Usage**: Individual resource usage (like memory) is typically very bursty. By combining multiple users, the cumulative usage pattern smooths out.
- **Cost Efficiency**:
  - Buying dedicated hardware requires purchasing for peak usage (plus a safety margin).
  - A shared virtual machine pools resources, providing a total capacity larger than any individual's needs.
  - The costs of acquiring, maintaining, and upgrading hardware are collectively shared among users.
- **Utility Model**: Similar to electricity and water utilities, data centers provide computing resources on a shared, rental basis. Users gain access to massive resources at a fraction of the individual cost.
- **Connection to Extensibility**: Virtualization is extensibility applied at the granularity of an entire operating system (rather than individual OS services like in SPIN or Exokernel).

## Hypervisors (Virtual Machine Monitors)
- **Definition**: An "operating system of operating systems" that manages hardware sharing and protection. Often referred to as a **Virtual Machine Manager (VMM)** or **Hypervisor**.
- **Guest OS / Virtual Machine (VM)**: The operating systems running on top of the shared hardware. *(Note: In this context, VM stands for Virtual Machine, not Virtual Memory).*
- **Types of Hypervisors**:
  - **Type 1: Native (Bare-Metal) Hypervisor**:
    - Runs directly on top of the bare hardware.
    - Guest operating systems are clients of this hypervisor.
    - Interferes minimally with guest OS operations, offering the best performance (conceptually similar to Exokernel).
  - **Type 2: Hosted Hypervisor**:
    - Runs as an application process on top of a host operating system.
    - Guest OSes emulate functionality through this host.
    - Examples: VMware Workstation, VirtualBox.

## Historical Timeline: Connecting the Dots
- **1960s–1970s**: IBM VM 370 pioneered virtualization to give users the illusion of owning a computer and to support legacy binary applications.
- **1980s–Early 1990s**: The rise of microkernels.
- **1990s**: Extensibility of operating systems became a focus.
- **Late 1990s**: Stanford's SimOS project laid the groundwork for modern OS-level virtualization (and became the basis for VMware).
- **Early 2000s**: Papers on Xen and VMware proposed virtualization for application mobility, server consolidation, and distributed web services.
- **Today**: A massive resurgence in data centers. Companies (IBM, Microsoft, Amazon, HP) shifted focus to providing isolated services on a utility basis, creating a win-win for users and providers.

## Virtualization Approaches

### 1. Full Virtualization
- **Concept**: The guest operating system remains completely unmodified. Its unchanged binary runs directly on the hypervisor.
- **Mechanism (Trap and Emulate)**:
  - Guest OSes run as user-level processes.
  - When the guest OS attempts to execute privileged instructions (thinking it is in kernel mode on bare metal), it generates a trap.
  - The hypervisor catches the trap and emulates the intended hardware functionality.
- **Challenges (Silent Failures)**:
  - On some older architectures (early Intel/AMD), privileged instructions might fail silently without generating a trap.
- **Solution (Binary Translation)**:
  - The hypervisor scans the unmodified guest OS binary for problematic instructions and edits them to ensure they are caught and handled appropriately. *(Note: Modern hardware now includes built-in virtualization support to solve this).*
- **Example**: Utilized by VMware.

### 2. Para Virtualization
- **Concept**: The source code of the guest operating system is modified to make it "hypervisor-aware."
- **Advantages**:
  - Avoids the problematic instructions that plague full virtualization.
  - Allows for optimizations (e.g., exposing real hardware resources to the guest OS, enabling page coloring tricks).
- **Application Transparency**: The API presented to applications remains completely identical. Applications require zero changes.
- **Modification Scope**: Surprisingly small.
  - **Less than 2%** of the original OS codebase needs to be modified.
  - *Proof of concept (Xen)*: Modifying Linux required changing only ~1.36% of the code, and Windows XP required a minuscule change ("in the noise").
- **Example**: Utilized by the Xen hypervisor family.

## The Big Picture
Regardless of the approach (Full or Para Virtualization), the core responsibilities of a hypervisor are:
1. **Virtualizing Hardware Resources**: Safely and transparently realizing the memory hierarchy, CPU, and physical devices for the guest operating systems.
2. **Transfer Mechanisms**: Managing the data and control transfers between the guest operating systems and the underlying hypervisor.
