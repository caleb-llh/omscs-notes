import os
import glob
import re

base_dir = "local/aos_notes"
lessons = sorted(os.listdir(base_dir))

def sort_key(filepath):
    # Extract plX and Module_Y numbers to sort correctly (e.g. pl0_Module_10 vs pl0_Module_2)
    basename = os.path.basename(filepath)
    match = re.search(r'pl(\d+)_Module_(\d+)', basename)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return (999, 999)

for lesson in lessons:
    lesson_path = os.path.join(base_dir, lesson)
    if not os.path.isdir(lesson_path):
        continue
        
    all_files = glob.glob(os.path.join(lesson_path, "*.md"))
    
    # Filter out already merged files if they exist to prevent double merging
    all_files = [f for f in all_files if not os.path.basename(f).startswith("Lesson_")]
    
    raw_files = sorted([f for f in all_files if "_Raw.md" in f], key=sort_key)
    processed_files = sorted([f for f in all_files if "_Raw.md" not in f], key=sort_key)
    
    merged_raw_path = os.path.join(lesson_path, f"{lesson}_Raw.md")
    merged_processed_path = os.path.join(lesson_path, f"{lesson}.md")
    
    if raw_files:
        with open(merged_raw_path, "w") as out_raw:
            out_raw.write(f"# {lesson} (Raw Transcripts)\n\n")
            for f in raw_files:
                with open(f, "r") as in_file:
                    out_raw.write(in_file.read() + "\n\n---\n\n")
                    
    if processed_files:
        with open(merged_processed_path, "w") as out_proc:
            out_proc.write(f"# {lesson} (Synthesized Notes)\n\n")
            for f in processed_files:
                with open(f, "r") as in_file:
                    out_proc.write(in_file.read() + "\n\n---\n\n")
                    
    # Cleanup old chunked files
    for f in raw_files + processed_files:
        if os.path.exists(f):
            os.remove(f)

print("Successfully merged chunked files into single lesson files for AOS.")
