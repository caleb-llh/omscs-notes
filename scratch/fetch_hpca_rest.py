import os
import glob
import subprocess
import re

playlists = [
    "PLAwxTw4SYaPkr-vo9gKBTid_BWpWEfuXe", # pl4
    "PLAwxTw4SYaPndXEsI4kAa6BDSTRbkCKJN"  # pl5
]

base_dir = "local/HPCA_raw_subs"
out_dir = "local/HPCA_Notes"
os.makedirs(base_dir, exist_ok=True)
os.makedirs(out_dir, exist_ok=True)

def clean_vtt(filepath):
    lines = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('WEBVTT') or '-->' in line or line.isdigit():
                    continue
                line = re.sub(r'<[^>]+>', '', line)
                lines.append(line)
    except Exception as e:
        pass
    return " ".join(lines)

for i, pl_id in enumerate(playlists, start=4):
    pl_dir = os.path.join(base_dir, f"pl{i}")
    os.makedirs(pl_dir, exist_ok=True)
    
    url = f"https://www.youtube.com/playlist?list={pl_id}"
    print(f"Downloading pl{i}...")
    subprocess.run([
        "yt-dlp", "--skip-download", "--write-auto-sub", "--sub-lang", "en",
        "-o", f"{pl_dir}/%(playlist_index)03d_%(title)s.%(ext)s", url
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    vtt_files = sorted(glob.glob(os.path.join(pl_dir, "*.vtt")))
    
    modules = []
    current_module = []
    for vtt in vtt_files:
        filename = os.path.basename(vtt)
        title = re.sub(r'^\d+_', '', filename).replace('.en.vtt', '').replace('.vtt', '').strip()
        title = title.replace(" - Georgia Tech - HPCA", "").replace(" - Georgia Tech", "").strip()
        
        if ("Introduction" in title or len(current_module) >= 15) and current_module:
            modules.append(current_module)
            current_module = []
        
        current_module.append((title, vtt))
        
    if current_module:
        modules.append(current_module)
        
    for mod_idx, mod_vids in enumerate(modules, 1):
        raw_path = os.path.join(out_dir, f"pl{i}_Module_{mod_idx}_Raw.md")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(f"# Playlist {i} Module {mod_idx} Raw Transcript\n\n")
            for title, vtt in mod_vids:
                f.write(f"## {title}\n")
                text = clean_vtt(vtt)
                f.write(text + "\n\n")
        print(f"Generated {raw_path}")

print("Remaining HPCA transcripts fetched and grouped!")
