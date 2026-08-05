import os
import shutil

mapping = {
    "Week_01_Intro_Pipelining_Branch_Prediction": [
        ("pl0", [1,2,3,4,5,6,7,8,9,10])
    ],
    "Week_02_Predication_ILP_Scheduling": [
        ("pl0", [11]),
        ("pl1", [1,2,3,4,5])
    ],
    "Week_03_ROB_Memory_Ordering_VLIW": [
        ("pl2", [1,2,3,4,5,6,7])
    ],
    "Week_04_Cache_Review_Virtual_Memory": [
        ("pl2", [8,9,10,11,12]),
        ("pl3", [1,2,3])
    ],
    "Week_05_Advanced_Caches_Memory": [
        ("pl3", [4,5,6])
    ],
    "Week_06_Storage_Fault_Tolerance": [
        ("pl3", [7,8]),
        ("pl4", [1,2,3])
    ],
    "Week_07_Multi_Processing_Begin_Coherence": [
        ("pl4", [4,5,6])
    ],
    "Week_08_Finish_Cache_Coherence": [
        ("pl4", [7,8])
    ],
    "Week_09_Synchronization_Begin_Consistency": [
        ("pl4", [9,10]),
        ("pl5", [1])
    ],
    "Week_10_Finish_Consistency_Many_Core": [
        ("pl5", [2,3])
    ]
}

base_dir = "local/HPCA_Notes"
out_dir = "local/HPCA_Lessons_Notes"

os.makedirs(out_dir, exist_ok=True)

# Keep a running index to order files sequentially within the course
global_index = 1

for week_name, sources in mapping.items():
    week_dir = os.path.join(out_dir, week_name)
    os.makedirs(week_dir, exist_ok=True)
    
    for pl_name, modules in sources:
        for mod_num in modules:
            for suffix in [".md", "_Raw.md"]:
                filename = f"{pl_name}_Module_{mod_num}{suffix}"
                src_path = os.path.join(base_dir, filename)
                if os.path.exists(src_path):
                    # Add a sequential index so they sort nicely inside the folder
                    dest_filename = f"{global_index:02d}_{filename}"
                    dest_path = os.path.join(week_dir, dest_filename)
                    shutil.copy2(src_path, dest_path)
            global_index += 1

print(f"Successfully grouped HPCA notes into {out_dir}")
