
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

> Act as a technical scribe. Using the provided transcripts, generate a comprehensive structural synthesis. Do NOT summarize or omit specific details; instead, re-organize the raw information into a hierarchical technical manual. 
For every lecture, the goal is exhaustiveness and first-principles elaboration instead of brevity. Be as verbose as possible. Make sure all information is captured, and assume a technical reader but no prior context. (Include the quiz examples.) Thus, craft a detailed set of notes over multiple responses/parts. Start off each section with a question. If the response cuts off due to length, I will prompt you to 'Continue' iteratively until every data point is mapped.
