import os
import shutil

mapping = {
    "01_Introduction_and_Performance": [("pl0", [1,2,3,4])],
    "02_Pipelining": [("pl0", [5,6])],
    "03_Branch_Prediction": [("pl0", [7,8,9])],
    "04_Predication": [("pl0", [10,11])],
    "05_ILP_and_Tomasulo": [("pl1", [1,2,3,4,5])],
    "06_Reorder_Buffer_ROB": [("pl2", [1,2,3])],
    "07_Memory_Ordering": [("pl2", [4])],
    "08_Compiler_ILP_and_VLIW": [("pl2", [5,6,7])],
    "09_Cache_Fundamentals": [("pl2", [8,9,10,11,12])],
    "10_Virtual_Memory": [("pl3", [1,2,3])],
    "11_Advanced_Caches": [("pl3", [4,5,6])],
    "12_Storage_Technologies": [("pl3", [7,8])],
    "13_Fault_Tolerance": [("pl4", [1,2,3])],
    "14_Multi_Processing": [("pl4", [4,5])],
    "15_Cache_Coherence": [("pl4", [6,7,8])],
    "16_Synchronization": [("pl4", [9,10])],
    "17_Memory_Consistency": [("pl5", [1,2])],
    "18_Many_Core_Challenges": [("pl5", [3])]
}

base_dir = "local/HPCA_Notes"
out_dir = "local/HPCA_Modules"

os.makedirs(out_dir, exist_ok=True)

global_index = 1

for topic_name, sources in mapping.items():
    topic_dir = os.path.join(out_dir, topic_name)
    os.makedirs(topic_dir, exist_ok=True)
    
    for pl_name, modules in sources:
        for mod_num in modules:
            for suffix in [".md", "_Raw.md"]:
                filename = f"{pl_name}_Module_{mod_num}{suffix}"
                src_path = os.path.join(base_dir, filename)
                if os.path.exists(src_path):
                    # Prefix with global index so they sort cleanly
                    dest_filename = f"{global_index:02d}_{filename}"
                    dest_path = os.path.join(topic_dir, dest_filename)
                    shutil.copy2(src_path, dest_path)
            global_index += 1

print(f"Successfully reorganized HPCA notes into {out_dir}")
