
### Scrape Lecture Videos
- Scraped from youtube playlists 

``` bash
### paste the playlist link into hpca.txt, one per line

cd ./scrape_playlist
python scrape.py hpca.txt

### all video links and descriptions will be saved in hpca_csv.txt
```

### NotebookLM Upload Limit
- Upload limit is 50 files per user. Split into topics to stay within the limit.
- You can't upload 50 at once. Upload in batches of decreasing size. Their internal limit follows this binary search pattern: 25, 12, 6, 3, 1.


### NotebookLM Scribe Prompt
Make sure to set responses to "Long".

> Act as a technical scribe. Using the provided material, generate a comprehensive structural synthesis. Do NOT summarize or omit specific details; instead, re-organize the raw information into a hierarchical technical manual. 
> 
> For every lecture, the goal is exhaustiveness/completion and first-principles elaboration instead of brevity. Be as verbose as possible. Make sure all information is captured, and assume a technical reader but no prior context. (Include the quiz examples if present) Thus, craft a detailed set of notes over multiple responses/parts. If the response cuts off due to length, I will prompt you to 'Continue' iteratively until every data point is mapped.


**Paper**:
Explain this paper to me using the Feynman technique, considering yourself as the author. our goal is exhaustiveness/completion. Thus, craft a detailed set of notes over multiple responses/parts. If the response cuts off due to length, I will prompt you to 'Continue' iteratively until every data point is mapped.

**Lecture**:
Act as a technical scribe. Using the provided material, generate a comprehensive structural synthesis. Include everything. Do NOT summarize or omit specific details; instead, turn the raw information into a hierarchical technical manual. Your goal is exhaustiveness/completion. Include the code examples. Thus, craft a detailed set of notes over multiple responses/parts. If the response cuts off due to length, I will prompt you to 'Continue' iteratively until every data point is mapped.


### Trae multi-agent prompt (Gemini 3.1 Pro Preview)
> I want you to use an LLM sub-agent to read the transcript for all the videos in this playlist, reorganise them in a way into highly readable and structured textbook-style Markdown notes, grouped by themes. Create a new copy, do NOT lose semantic information in the process, and feel free to do multiple passes through the generated notes to ensure quality.

> Group them based on the modules/lessons specified in the syllabus

> Supplement the notes where necessary to make it more readable and friendly.
> Examples of block comments to add:
> background contexts, purpose (problem that this system is solving), connective information, intuitions, design philosophy, conceptual mental-models/frameworks, dichotomy/tradeoffs, hypotheticals/first-principles (what if i changed this aspect), common examples, common confusions (what it is not), etc. Do NOT lose information, only add.

> Do a few passes to enrich and refine the notes to achieve the high readability, density and quality of information. Do NOT lose information.

> Do NOT lose information, only add. To ensure quality is not compromised due to context window limitations, feel free to do multiple passes. Parallelize with multiple sub-agents to speed up the process. Edit the file directly, do not write scripts to modify the file.

> Consolidate all the modules in this course into a course summary markdown file, walking through all the modules with a connective thread, including key insights along the way. Focus on the conceptual gist/intution instead of the actual details, like a textbook introduction so i know the shape of this course and why it is relevant to me. To ensure quality is not compromised due to context window limitations, feel free to do multiple passes. Parallelize with multiple sub-agents to speed up the process.