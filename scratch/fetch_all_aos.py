import os
import subprocess
import glob
import re

def parse_vtt(vtt_file):
    if not os.path.exists(vtt_file):
        return ""
    with open(vtt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    text = ""
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if '-->' in line:
            i += 1
            while i < len(lines) and lines[i].strip() != "" and '-->' not in lines[i]:
                clean = re.sub(r'<[^>]+>', '', lines[i].strip())
                if clean not in text:
                    text += clean + " "
                i += 1
        else:
            i += 1
    return text.strip()

def process_playlist(pl_file, out_dir_base, pl_name):
    out_dir = f"local/{out_dir_base}"
    os.makedirs(out_dir, exist_ok=True)
    
    with open(pl_file, "r") as f:
        lines = [l.strip() for l in f if l.strip()]
        
    modules = []
    current_module = []
    
    for line in lines:
        parts = line.split("|")
        if len(parts) != 3: continue
        idx, vid, title = parts
        
        clean_title = title.replace(" - Georgia Tech - Advanced Operating Systems", "").strip()
        
        # Start a new module if it's an Introduction, OR if the current module gets too big (>20 videos)
        if ("Introduction" == clean_title or len(current_module) >= 20) and current_module:
            modules.append(current_module)
            current_module = []
            
        current_module.append({"id": vid, "title": clean_title})
        
    if current_module:
        modules.append(current_module)
        
    for mod_idx, mod_videos in enumerate(modules, 1):
        raw_file = os.path.join(out_dir, f"Module_{mod_idx}_Raw.md")
        if os.path.exists(raw_file):
            print(f"Skipping {raw_file}, already exists.")
            continue
            
        print(f"--- Processing {pl_name} Module {mod_idx} ({len(mod_videos)} videos) ---")
        
        with open(raw_file, "w", encoding="utf-8") as f:
            f.write(f"# {pl_name} Module {mod_idx} Raw Transcript\n\n")
            
            for vid_info in mod_videos:
                vid = vid_info["id"]
                title = vid_info["title"]
                
                print(f"Downloading subs for: {title}")
                cmd = [
                    "uv", "run", "yt-dlp",
                    "--skip-download",
                    "--write-auto-sub", "--sub-format", "vtt",
                    "-o", f"{out_dir}/{vid}.%(ext)s",
                    f"https://www.youtube.com/watch?v={vid}"
                ]
                subprocess.run(cmd, capture_output=True)
                
                vtt_files = glob.glob(f"{out_dir}/{vid}*.vtt")
                transcript = ""
                if vtt_files:
                    transcript = parse_vtt(vtt_files[0])
                    os.remove(vtt_files[0])
                
                f.write(f"## {title}\n")
                if transcript:
                    f.write(f"{transcript}\n\n")
                else:
                    f.write(f"*(No transcript available)*\n\n")
                    
        print(f"Saved {raw_file}")
    
    return len(modules)

def main():
    print("Processing Playlist 1...")
    p1 = process_playlist("local/pl1.txt", "aos_pl1_notes", "Playlist_1")
    print("Processing Playlist 2...")
    p2 = process_playlist("local/pl2.txt", "aos_pl2_notes", "Playlist_2")
    print("Processing Playlist 3...")
    p3 = process_playlist("local/pl3.txt", "aos_pl3_notes", "Playlist_3")
    print(f"Done. Generated {p1} + {p2} + {p3} raw modules.")

if __name__ == "__main__":
    main()
