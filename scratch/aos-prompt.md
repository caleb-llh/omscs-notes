**Role & Objective:**
Act as an advanced educational content synthesizer and Python automation expert. My goal is to convert a series of YouTube lecture playlists and a course syllabus into a highly organized, comprehensive, and lossless set of Markdown notes, structured exactly according to the official course schedule.

**Inputs:**
- **Course Name:** [Insert Course Name]
- **Syllabus PDF URL/Path:** [Insert Syllabus Link or Local Path]
- **YouTube Playlist URLs:** 
  1. [Insert Playlist 1 URL]
  2. [Insert Playlist 2 URL]
  ...

**Execution Steps:**
Please execute the following tasks sequentially. Do not proceed to the next step until the current one is fully completed and verified.

**Step 1: Fetch and Group Transcripts**
- Write and run a Python script using `yt-dlp` (with `--skip-download --write-auto-sub` and `--sub-lang en`) to download the VTT transcripts for all videos in the provided playlists.
- Parse the VTT files to extract clean text.
- Group the transcripts into logical "Modules" per playlist. Start a new module when you detect a natural shift in topic (e.g., a video titled "Introduction to...") or when a module exceeds ~15-20 short videos.

**Step 2: Synthesize Lossless Markdown Notes**
- For each grouped module, use an LLM sub-agent to synthesize the raw transcripts into structured Markdown notes.
- **Rules for Notes:** 
  - The notes must be practically **lossless**—capture all technical details, examples, and nuances.
  - Group the content **thematically** rather than strictly chronologically.
  - Do not include placeholders for screenshots or images; rely entirely on text formatting (tables, bullet points, bolding).
  - For each module, save two files in a local directory: `Module_X_Raw.md` (the raw transcript text) and `Module_X.md` (the synthesized notes).

**Step 3: Parse the Syllabus**
- Download the syllabus PDF (use `--native-tls` if using `uv pip` to avoid certificate issues).
- Write a Python script using `PyMuPDF` (`fitz`) to extract the text from the syllabus.
- Identify and extract the official Course Schedule, specifically noting the Lesson/Week numbers, Lesson topics, and associated reading materials.

**Step 4: Map and Reorganize Files**
- Based on the topics and readings extracted from the syllabus, map each of the generated Markdown modules to its corresponding official Lesson.
- Write a Python script to create a new directory structure (e.g., `Lesson_1_Topic_Name/`, `Lesson_2_Topic_Name/`).
- Copy the synthesized notes and raw transcripts into their respective lesson folders. 
- Prefix the filenames with their original playlist identifier (e.g., `pl1_Module_3.md`) to prevent naming collisions and preserve the viewing order.

**Step 5: Enrich**
Supplement the notes to make it more readable and friendly. e.g. via background contexts, purpose, connective information, intuitions, philosophy/gist, conceptual mental-models/frameworks, common examples, etc (come up with your own ways too and feel free to go include/exclude these supplementary methods). Do NOT lose information, only add.

**Step 6: Verify**
Do a few passes to verify the readability, density and quality of information.

Please begin with Step 1 and let me know when you are ready to synthesize the notes!