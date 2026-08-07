# CSE 6220: Readiness Survey

> **Fact Check:** CSE 6220 at Georgia Tech's OMSCS program is officially titled "Intro to High-Performance Computing". It extensively uses C, MPI (Message Passing Interface), and OpenMP, and heavily emphasizes algorithmic analysis.

> **Mental Model (The "Hardware Sympathy" Model):** HPC isn't just writing fast code; it's aligning software structures with hardware realities (caches, interconnects). The readiness survey ensures you have the algorithmic baseline so you can focus your mental energy on hardware interactions.

> **Background Context:** CSE 6220 (High-Performance Computing) is a notoriously rigorous, deeply rewarding course. Before diving into parallel algorithms, distributed systems, and C/MPI/OpenMP programming, it's crucial to ensure your foundational skills are sharp. This document outlines the purpose, strategy, and mental models for interpreting the course's Readiness Survey.

## 1. Purpose of the Survey

> **Fact Check:** Research on student success in CS courses often shows that prerequisite knowledge and self-efficacy are stronger predictors of success than generalized test scores (like GREs). The instructor's philosophy aligns with this pedagogical research.

> **Tradeoff:** While taking a readiness survey might feel like an extra hurdle before the course even begins, the time invested here saves exponential time later. Discovering a prerequisite gap in week 1 costs hours; discovering it in week 6 during a complex MPI project costs letter grades.

> **Tradeoff (Confidence vs. Reality):** Overestimating your readiness preserves your ego in the short term but risks a severe reality check during the first exam or project. Underestimating your readiness might cause unnecessary stress, but often leads to over-preparation, which is a net positive in HPC.

- **Self-Assessment**: Designed to help students determine if they have the appropriate background to succeed in the course.
  - *Intuition*: High-performance computing builds heavily on algorithmic complexity. This survey acts as a "temperature check" to see if you are ready to tackle advanced parallelization concepts without drowning in prerequisite material.
- **Unpredictability of Success**: The instructor emphasizes that traditional metrics (e.g., GPAs, GRE scores) are poor predictors of success. Students are treated as individuals ("you are not a number"), and anyone could be the next innovator in the field.
  - *Mental Model*: Think of HPC as a marathon. Your previous track record matters less than your current stamina, resourcefulness, and willingness to train. Your background doesn't define your ceiling, but your foundational grasp determines your starting line.

> **Hypothetical:** Imagine a student who barely scraped by in undergraduate algorithms years ago but has since spent years building complex systems in industry. They might struggle with a formal math exam but excel in this course's practical optimization tasks because of their hardened debugging skills.

## 2. Format and Content

> **Fact Check:** Master's Theorem and recurrence relation evaluation (e.g., $T(n) = aT(n/b) + f(n)$) are fundamental to analyzing divide-and-conquer parallel algorithms. Knowing Big-O notation is essential, but understanding Big-$\Omega$ (lower bounds) and Big-$\Theta$ (tight bounds) is equally critical for rigorous proofs in this course.

> **Mental Model (The "Cognitive Budget"):** You have a finite amount of working memory. If 80% of your cognitive budget is spent trying to remember how pointers work in C, only 20% remains for conceptualizing distributed memory algorithms. The survey ensures pointer manipulation and basic data structures only consume 10% of your budget.

> **Common Confusion:** Students often mistake "knowing C" for being ready for HPC. While C is the medium, the true currency of the course is algorithm analysis (Big-O, work-span models) and hardware sympathy (cache lines, memory bandwidth).

- **Topics Covered**: The survey consists of a series of questions focusing on foundational **Math** and **CS 101** concepts.
  - *Examples*: 
    - **Math**: Expect topics like discrete mathematics, probability, summation formulas ($\sum$), and asymptotic notation (Big-$O$, Big-$\Omega$, Big-$\Theta$).
    - **CS 101**: Expect basic data structures (trees, graphs, linked lists), standard algorithm analysis (sorting, searching), and a solid grasp of control flow.
- **Prerequisite Knowledge**: Comfort with these foundational materials is highly recommended to do well in the course.
  - *Why this matters*: When you are trying to debug a race condition in a multi-threaded C program, you cannot simultaneously be struggling to understand how a basic recursive function works. The cognitive load would simply be too high.

> **Example:** When analyzing a parallel algorithm, you will need to determine both its total Work (total operations) and Span (critical path length). If you are not comfortable summing series or evaluating recurrence relations (like $T(n) = 2T(n/2) + O(n)$), the parallel analysis will feel impenetrable.

## 3. Instructions for Taking the Survey

> **Fact Check:** Writing algorithms out by hand (often called "tracing" or "dry-running") is a proven pedagogical method for improving code comprehension and identifying logical flaws. It forces the brain to process state changes linearly, avoiding the cognitive shortcuts taken when reading on a screen.

> **Tradeoff (Speed vs. Depth):** Googling an answer provides immediate gratification and speed, but deriving the answer manually builds deep neural pathways. For the survey, you trade the speed of lookup for the depth of self-assessment.

> **Mental Model:** Treat the survey as a closed-book diagnostic first, and an open-book learning opportunity second. The goal isn't to get a perfect score on the first try; it's to map the boundaries of your current knowledge.

- **Method**: Work out the problems manually using pencil and paper.
  - *Intuition*: Writing things out forces you to slow down and exposes gaps in your logic that an IDE's autocomplete or a quick Google search might otherwise mask. It builds a stronger mental muscle memory for algorithmic tracing.
- **Resourcefulness**: If you do not immediately know how to approach a question, do not give up. It is fully expected and acceptable to look up information to refresh your memory on problem-solving techniques.
  - *Example*: If you see a summation like $\sum_{i=1}^{n} i$ and forget the closed-form formula, looking up Gauss's formula ($n(n+1)/2$) is a great example of being resourceful. Real-world engineering is about knowing *how* to find answers, not rote memorization.
- **Reviewing Solutions**: Once you have an answer, or if you become completely stuck, review the provided solution that follows each question.

> **Intuition:** The difference between "I knew that but forgot" and "I have never seen this before" becomes blaringly obvious when you read the solution. The former triggers an 'aha!' moment; the latter induces panic. Pay attention to your emotional response to the solutions.

## 4. Evaluating Your Results

> **Fact Check:** The "other side of hell" reference is a common cultural touchstone within the OMSCS program regarding CSE 6220. The course consistently ranks as one of the most difficult and time-consuming in the curriculum, alongside courses like Compilers and Distributed Systems.

> **Mental Model (The "Technical Debt" Analogy):** Entering the course with minor knowledge gaps is like taking on manageable technical debt—you can pay it off with a bit of weekend study. Entering with major deficiencies is like bankruptcy; the interest payments (time spent catching up) will exceed your weekly time budget, leading to inevitable failure.

> **Tradeoff:** Deciding whether to drop the course based on the survey involves a classic time-vs-reward tradeoff. Pushing through missing foundations means sacrificing personal time, sleep, and potentially performance in other concurrent courses, but successfully surviving it yields immense confidence and skill.

*How do you interpret your performance? Use the "Rust vs. Missing Foundation" mental model.*

- **Minor Knowledge Gaps**: If you answered incorrectly but the provided solution makes sense to you, you are likely in a good position. With dedication to the course, you can fill in the remaining gaps as you progress.
  - *Mental Model (The "Rust" Model)*: You are just "rusty." The neural pathways are there, they just haven't been used in a while. Brushing up will be fast and manageable.
- **Major Deficiencies**: If you feel highly uncomfortable with the material even after reviewing the solutions, it is strongly advised to reconsider taking the course, as catching up may consume an excessive amount of your time.
  - *Mental Model (The "Missing Foundation" Model)*: If the solution explains a recursive tree traversal and the concepts of recursion, nodes, and base cases still feel completely alien, you are dealing with a missing foundation. Building that from scratch *while* taking CSE 6220 is a recipe for burnout.
- **Final Note**: The instructor sets these ground rules and wishes students luck, humorously hoping to see them "on the other side of hell."
  - *Context*: The course is affectionately (and accurately) known to be highly challenging ("hell"), but those who make it through often consider it one of the best courses they've ever taken. The survey is your first step into the fire!

> **Hypothetical:** If you score perfectly on the readiness survey without breaking a sweat, you are exceptionally well-prepared, but don't get complacent. The survey tests the *prerequisites*, not the actual HPC concepts (like race conditions, false sharing, or message passing deadlocks) that make the "hell" so challenging.
