# Module 3: Introduction to Operating Systems

## 1. What is an Operating System?

*   **Core Definition**: Most concisely, an operating system (OS) is a program that contains code to access physical hardware resources and arbitrates among competing requests for those resources from multiple, simultaneously running applications.
*   **Nature of the OS**: 
    *   It is fundamentally a program, much like any other software (though more complex than a "Hello World" application).
    *   Learning to build one is just a matter of "climbing the programming ladder" (from simple programs to complex systems).
*   **Application Programming Interfaces (APIs)**:
    *   The OS provides well-defined APIs for accessing the hardware resources it manages.
    *   Applications request hardware resources by making API calls to the OS.
    *   The OS provides these resources as services and sends responses back to the applications.

## 2. Core Functionalities of an Operating System

The operating system serves several critical roles in managing a computer system:

*   **Resource Manager**: The OS acts as the "boss" in control of all physical hardware resources.
*   **Consistent Hardware Interface**: 
    *   It provides a consistent interface to physical hardware (CPU, memory, I/O devices).
    *   The OS acts as a level in the abstraction hierarchy, sitting directly between user applications and the physical processor/resources.
*   **Application Scheduler (Arbiter)**: 
    *   Because multiple applications may require hardware resources simultaneously, the OS acts as an arbiter.
    *   It schedules applications on the CPU and coordinates requests for hardware devices.

> **Note on Privacy**: The OS does *not* exist to store personal information (such as credit card numbers, social security numbers, or email addresses). 

## 3. Hardware-Software Interaction: The Mouse Click Example

The interaction between hardware and software is best illustrated by examining what happens during a standard user action, such as clicking a mouse in an application like Google Earth.

### Anatomy of the System Bus
*   **The Bus**: The conduit connecting hardware devices to the system.
*   **Bus Components**: Contains data lines, address lines, and one or more **interrupt lines**.

### Step-by-Step: What Happens When You Click the Mouse?

1.  **Hardware Controller Action**: The hardware controller interfacing the mouse asserts a signal on the **interrupt line** of the system bus to indicate it needs attention.
    *   *Analogy*: Raising a hand in a classroom to ask a question.
2.  **CPU Interrupt**: Asserting the interrupt line results in a **CPU Interrupt**.
    *   **Definition - Interrupt**: A hardware mechanism used to alert the processor that an external event (like a mouse click) requires immediate attention.
    *   *Analogy*: Someone ringing the doorbell of a house.
3.  **Context Switch to OS**: 
    *   The CPU is a "dumb animal" that only executes instructions. At the moment of the click, it might be busy executing an application (e.g., Google Earth).
    *   When the interrupt arrives, the current program pauses, and the Operating System schedules *itself* to run on the CPU to "answer the doorbell."
4.  **Handling the Interrupt**: The OS fields the interrupt, determines which application it is intended for, and passes the event to that specific program for appropriate action.
5.  **Domino Effect**: This sequence of events ultimately results in the target application running specific code to read the spatial coordinates of the mouse and executing the desired software action.
