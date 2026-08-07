import os
import glob
import re

src_base = "local/CSE6220_Lectures"
out_base = "local/CSE6220_Notes"

os.makedirs(out_base, exist_ok=True)

# Helper to strip SRT tags
def parse_srt(file_path):
    text_lines = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines, sequence numbers, and timestamp lines
            if not line: continue
            if line.isdigit(): continue
            if "-->" in line: continue
            text_lines.append(line)
    return " ".join(text_lines)

dirs = sorted(glob.glob(os.path.join(src_base, "*_subtitles")))

for d in dirs:
    mod_name = os.path.basename(d).replace("_subtitles", "")
    srt_files = glob.glob(os.path.join(d, "*.srt"))
    
    # Sort by the number at the beginning of the filename
    def extract_num(path):
        base = os.path.basename(path)
        m = re.match(r'^(\d+)', base)
        return int(m.group(1)) if m else 999999
        
    srt_files.sort(key=extract_num)
    
    raw_md_path = os.path.join(out_base, f"{mod_name}_Raw.md")
    with open(raw_md_path, "w", encoding="utf-8") as out_f:
        out_f.write(f"# {mod_name} Raw Transcript\n\n")
        for srt in srt_files:
            title = os.path.basename(srt).replace(".srt", "")
            out_f.write(f"## {title}\n")
            text = parse_srt(srt)
            out_f.write(text + "\n\n")
            
    print(f"Generated {raw_md_path}")
