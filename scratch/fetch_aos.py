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
                # remove vtt tags
                clean = re.sub(r'<[^>]+>', '', lines[i].strip())
                if clean not in text: # avoid basic auto-sub duplication
                    text += clean + " "
                i += 1
        else:
            i += 1
    return text.strip()

def main():
    out_dir = "local/aos_notes"
    os.makedirs(out_dir, exist_ok=True)
    
    with open("local/aos_playlist.txt", "r") as f:
        lines = [l.strip() for l in f if l.strip()]
        
    modules = []
    current_module = []
    
    for line in lines:
        parts = line.split("|")
        if len(parts) != 3: continue
        idx, vid, title = parts
        
        # Strip common suffix to make it cleaner
        clean_title = title.replace(" - Georgia Tech - Advanced Operating Systems", "")
        
        if "Introduction" in clean_title and current_module:
            modules.append(current_module)
            current_module = []
            
        current_module.append({"id": vid, "title": clean_title})
        
    if current_module:
        modules.append(current_module)
        
    for mod_idx, mod_videos in enumerate(modules, 1):
        raw_file = os.path.join(out_dir, f"Module_{mod_idx}_Raw.md")
        print(f"--- Processing Module {mod_idx} ({len(mod_videos)} videos) ---")
        
        with open(raw_file, "w", encoding="utf-8") as f:
            f.write(f"# Module {mod_idx} Raw Transcript\n\n")
            
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
                
                # find the downloaded vtt
                vtt_files = glob.glob(f"{out_dir}/{vid}*.vtt")
                transcript = ""
                if vtt_files:
                    transcript = parse_vtt(vtt_files[0])
                    # Clean up the vtt file so we don't clutter
                    os.remove(vtt_files[0])
                
                f.write(f"## {title}\n")
                if transcript:
                    f.write(f"{transcript}\n\n")
                else:
                    f.write(f"*(No transcript available)*\n\n")
                    
        print(f"Saved {raw_file}")

if __name__ == "__main__":
    main()
