# CSE 6220: Readiness Survey

> **Background Context:** CSE 6220 (High-Performance Computing) is a notoriously rigorous, deeply rewarding course. Before diving into parallel algorithms, distributed systems, and C/MPI/OpenMP programming, it's crucial to ensure your foundational skills are sharp. This document outlines the purpose, strategy, and mental models for interpreting the course's Readiness Survey.

## 1. Purpose of the Survey
- **Self-Assessment**: Designed to help students determine if they have the appropriate background to succeed in the course.
  - *Intuition*: High-performance computing builds heavily on algorithmic complexity. This survey acts as a "temperature check" to see if you are ready to tackle advanced parallelization concepts without drowning in prerequisite material.
- **Unpredictability of Success**: The instructor emphasizes that traditional metrics (e.g., GPAs, GRE scores) are poor predictors of success. Students are treated as individuals ("you are not a number"), and anyone could be the next innovator in the field.
  - *Mental Model*: Think of HPC as a marathon. Your previous track record matters less than your current stamina, resourcefulness, and willingness to train. Your background doesn't define your ceiling, but your foundational grasp determines your starting line.

## 2. Format and Content
- **Topics Covered**: The survey consists of a series of questions focusing on foundational **Math** and **CS 101** concepts.
  - *Examples*: 
    - **Math**: Expect topics like discrete mathematics, probability, summation formulas ($\sum$), and asymptotic notation (Big-$O$, Big-$\Omega$, Big-$\Theta$).
    - **CS 101**: Expect basic data structures (trees, graphs, linked lists), standard algorithm analysis (sorting, searching), and a solid grasp of control flow.
- **Prerequisite Knowledge**: Comfort with these foundational materials is highly recommended to do well in the course.
  - *Why this matters*: When you are trying to debug a race condition in a multi-threaded C program, you cannot simultaneously be struggling to understand how a basic recursive function works. The cognitive load would simply be too high.

## 3. Instructions for Taking the Survey
- **Method**: Work out the problems manually using pencil and paper.
  - *Intuition*: Writing things out forces you to slow down and exposes gaps in your logic that an IDE's autocomplete or a quick Google search might otherwise mask. It builds a stronger mental muscle memory for algorithmic tracing.
- **Resourcefulness**: If you do not immediately know how to approach a question, do not give up. It is fully expected and acceptable to look up information to refresh your memory on problem-solving techniques.
  - *Example*: If you see a summation like $\sum_{i=1}^{n} i$ and forget the closed-form formula, looking up Gauss's formula ($n(n+1)/2$) is a great example of being resourceful. Real-world engineering is about knowing *how* to find answers, not rote memorization.
- **Reviewing Solutions**: Once you have an answer, or if you become completely stuck, review the provided solution that follows each question.

## 4. Evaluating Your Results
*How do you interpret your performance? Use the "Rust vs. Missing Foundation" mental model.*

- **Minor Knowledge Gaps**: If you answered incorrectly but the provided solution makes sense to you, you are likely in a good position. With dedication to the course, you can fill in the remaining gaps as you progress.
  - *Mental Model (The "Rust" Model)*: You are just "rusty." The neural pathways are there, they just haven't been used in a while. Brushing up will be fast and manageable.
- **Major Deficiencies**: If you feel highly uncomfortable with the material even after reviewing the solutions, it is strongly advised to reconsider taking the course, as catching up may consume an excessive amount of your time.
  - *Mental Model (The "Missing Foundation" Model)*: If the solution explains a recursive tree traversal and the concepts of recursion, nodes, and base cases still feel completely alien, you are dealing with a missing foundation. Building that from scratch *while* taking CSE 6220 is a recipe for burnout.
- **Final Note**: The instructor sets these ground rules and wishes students luck, humorously hoping to see them "on the other side of hell."
  - *Context*: The course is affectionately (and accurately) known to be highly challenging ("hell"), but those who make it through often consider it one of the best courses they've ever taken. The survey is your first step into the fire!
