import os
import shutil

# Mapping of Lessons to their source modules
# Format: Lesson Name: [(Playlist folder, [Module numbers])]
mapping = {
    "Lesson_1_Intro_to_AOS": [
        ("aos_pl0_notes", [1, 2, 3, 4])
    ],
    "Lesson_2_OS_Structures": [
        ("aos_pl0_notes", [5, 6, 7])
    ],
    "Lesson_3_Virtualization": [
        ("aos_pl0_notes", [8, 9, 10])
    ],
    "Lesson_4_Parallel_Systems": [
        ("aos_pl1_notes", [1, 2, 3, 4, 5, 6, 7])
    ],
    "Lesson_5_Distributed_Systems": [
        ("aos_pl1_notes", [8, 9, 10]),
        ("aos_pl2_notes", [1, 2])
    ],
    "Lesson_6_Distributed_Objects_and_Middleware": [
        ("aos_pl2_notes", [3, 4, 5])
    ],
    "Lesson_7_Distributed_Subsystems": [
        ("aos_pl2_notes", [6, 7, 8, 9])
    ],
    "Lesson_8_Failures_and_Recovery": [
        ("aos_pl3_notes", [1, 2, 3])
    ],
    "Lesson_9_Internet_Computing": [
        ("aos_pl3_notes", [4, 5, 6])
    ],
    "Lesson_10_RT_and_Multimedia": [
        ("aos_pl3_notes", [7, 8])
    ],
    "Lesson_11_Security": [
        ("aos_pl3_notes", [9, 10])
    ]
}

base_dir = "local"
out_dir = os.path.join(base_dir, "aos_lessons_notes")

if not os.path.exists(out_dir):
    os.makedirs(out_dir)

for lesson_name, sources in mapping.items():
    lesson_dir = os.path.join(out_dir, lesson_name)
    os.makedirs(lesson_dir, exist_ok=True)
    
    for pl_folder, modules in sources:
        pl_name = pl_folder.split('_')[1] # e.g., "pl0"
        for mod_num in modules:
            # We have both Module_X.md and Module_X_Raw.md
            for suffix in [".md", "_Raw.md"]:
                filename = f"Module_{mod_num}{suffix}"
                src_path = os.path.join(base_dir, pl_folder, filename)
                if os.path.exists(src_path):
                    # Rename the file to include the playlist prefix to avoid collision
                    # and to keep order
                    dest_filename = f"{pl_name}_{filename}"
                    dest_path = os.path.join(lesson_dir, dest_filename)
                    shutil.copy2(src_path, dest_path)
                else:
                    print(f"Warning: File not found {src_path}")

print(f"Successfully grouped notes into {out_dir}")
