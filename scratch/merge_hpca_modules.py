import os
import glob

base_dir = "local/HPCA_Modules"
modules = sorted(os.listdir(base_dir))

for mod in modules:
    mod_path = os.path.join(base_dir, mod)
    if not os.path.isdir(mod_path):
        continue
        
    # Get all markdown files in the module folder, sorted by their global index
    all_files = sorted(glob.glob(os.path.join(mod_path, "*.md")))
    
    raw_files = [f for f in all_files if "_Raw.md" in f]
    processed_files = [f for f in all_files if "_Raw.md" not in f]
    
    # We will name the merged files exactly after the module folder name
    merged_raw_path = os.path.join(mod_path, f"{mod}_Raw.md")
    merged_processed_path = os.path.join(mod_path, f"{mod}.md")
    
    # Merge Raw
    with open(merged_raw_path, "w") as out_raw:
        out_raw.write(f"# {mod} (Raw Transcripts)\n\n")
        for f in raw_files:
            with open(f, "r") as in_file:
                out_raw.write(in_file.read() + "\n\n---\n\n")
                
    # Merge Processed
    with open(merged_processed_path, "w") as out_proc:
        out_proc.write(f"# {mod} (Synthesized Notes)\n\n")
        for f in processed_files:
            with open(f, "r") as in_file:
                out_proc.write(in_file.read() + "\n\n---\n\n")
                
    # Cleanup old chunked files
    for f in all_files:
        if f != merged_raw_path and f != merged_processed_path:
            os.remove(f)

print("Successfully merged chunked files into single module files.")
