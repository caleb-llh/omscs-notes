import os
import cv2
import numpy as np
import subprocess
import math
import glob

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLAwxTw4SYaPkKfusBLVfklgfdcB3BNpwX"
MAX_VIDEOS = 2

def get_playlist_videos():
    print("Fetching playlist info...")
    cmd = ["uv", "run", "yt-dlp", "--flat-playlist", "--print", "%(id)s|%(title)s", PLAYLIST_URL]
    result = subprocess.run(cmd, capture_output=True, text=True)
    videos = []
    for line in result.stdout.splitlines():
        if "|" in line:
            vid, title = line.split("|", 1)
            videos.append({"id": vid.strip(), "title": title.strip()})
    return videos[:MAX_VIDEOS]

def download_video_and_subs(vid, out_dir):
    print(f"Downloading video and subs for {vid}...")
    base_name = os.path.join(out_dir, vid)
    
    # Download worst video + subs
    cmd = [
        "uv", "run", "yt-dlp",
        "-f", "worstvideo[ext=mp4]/worst",
        "--write-auto-sub", "--sub-format", "vtt",
        "-o", f"{base_name}.%(ext)s",
        f"https://www.youtube.com/watch?v={vid}"
    ]
    subprocess.run(cmd, capture_output=True)
    
    return f"{base_name}.mp4"

def parse_vtt(vtt_file):
    # Very basic VTT parser
    with open(vtt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    transcript = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if '-->' in line:
            # e.g., 00:00:01.000 --> 00:00:03.000
            start_str = line.split('-->')[0].strip()
            # Convert HH:MM:SS.mmm to seconds
            parts = start_str.split(':')
            if len(parts) == 3:
                h, m, s = parts
                sec = int(h) * 3600 + int(m) * 60 + float(s)
            elif len(parts) == 2:
                m, s = parts
                sec = int(m) * 60 + float(s)
            else:
                sec = 0
                
            text = ""
            i += 1
            while i < len(lines) and lines[i].strip() != "" and '-->' not in lines[i]:
                text += lines[i].strip() + " "
                i += 1
            
            # Remove VTT formatting tags like <c>
            import re
            text = re.sub(r'<[^>]+>', '', text)
            transcript.append({"start": sec, "text": text.strip()})
        else:
            i += 1
    return transcript

def extract_keyframes(video_path, out_dir, threshold=15.0):
    print(f"Extracting keyframes from {video_path}...")
    os.makedirs(out_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or math.isnan(fps):
        fps = 30.0
    
    prev_frame = None
    keyframes = []
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Check every 2 seconds
        if frame_count % int(fps * 2) == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if prev_frame is not None:
                diff = cv2.absdiff(prev_frame, gray)
                non_zero_count = np.count_nonzero(diff > 30)
                change_ratio = (non_zero_count * 100) / diff.size
                
                if change_ratio > threshold:
                    timestamp = frame_count / fps
                    img_name = f"frame_{int(timestamp):04d}.jpg"
                    img_path = os.path.join(out_dir, img_name)
                    cv2.imwrite(img_path, frame)
                    keyframes.append({"time": timestamp, "path": img_path})
                    prev_frame = gray
            else:
                timestamp = frame_count / fps
                img_name = f"frame_{int(timestamp):04d}.jpg"
                img_path = os.path.join(out_dir, img_name)
                cv2.imwrite(img_path, frame)
                keyframes.append({"time": timestamp, "path": img_path})
                prev_frame = gray
                
        frame_count += 1
        
    cap.release()
    return keyframes

def generate_markdown(video, transcript, keyframes, out_file):
    print(f"Generating markdown for {video['title']}...")
    
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"# {video['title']}\n\n")
        f.write(f"[Watch Video](https://www.youtube.com/watch?v={video['id']})\n\n")
        
        paragraphs = []
        current_p = {"start": 0, "text": ""}
        for t in transcript:
            if current_p["text"] == "":
                current_p["start"] = t["start"]
            
            # Avoid duplicate text common in auto-subs
            if t["text"] not in current_p["text"]:
                current_p["text"] += t["text"] + " "
            
            if t["start"] - current_p["start"] > 30:
                paragraphs.append(current_p)
                current_p = {"start": 0, "text": ""}
        
        if current_p["text"]:
            paragraphs.append(current_p)
            
        kf_idx = 0
        for p in paragraphs:
            while kf_idx < len(keyframes) and keyframes[kf_idx]["time"] <= p["start"] + 30:
                kf = keyframes[kf_idx]
                time_str = f"{int(kf['time'] // 60):02d}:{int(kf['time'] % 60):02d}"
                rel_path = os.path.relpath(kf['path'], os.path.dirname(out_file))
                f.write(f"\n![Slide at {time_str}]({rel_path})\n*Timestamp: {time_str}*\n\n")
                kf_idx += 1
                
            f.write(f"{p['text'].strip()}\n\n")

def main():
    out_dir = "local/yt_notes"
    os.makedirs(out_dir, exist_ok=True)
    videos = get_playlist_videos()
    
    for vid_info in videos:
        vid = vid_info["id"]
        title = vid_info["title"]
        print(f"\nProcessing: {title} ({vid})")
        
        video_path = download_video_and_subs(vid, out_dir)
        frames_dir = f"{out_dir}/{vid}_frames"
        md_path = f"{out_dir}/{title.replace(' ', '_').replace('/', '_')}.md"
        
        # Find vtt file
        vtt_files = glob.glob(f"{out_dir}/{vid}*.vtt")
        transcript = []
        if vtt_files:
            transcript = parse_vtt(vtt_files[0])
            
        if os.path.exists(video_path):
            keyframes = extract_keyframes(video_path, frames_dir, threshold=15.0)
            if transcript:
                generate_markdown(vid_info, transcript, keyframes, md_path)
            else:
                print(f"Skipping markdown generation for {vid} due to missing transcript.")
        else:
            print(f"Video {video_path} not found.")

if __name__ == "__main__":
    main()
