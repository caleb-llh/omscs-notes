import os

order = [
    "Readiness",
    "Introduction_to_High_Performance_Computing",
    "Algorithmic_Time____Energy_and_Power",
    "Intro_to_the_Work_Span_Model",
    "Scans_and_List_Ranking",
    "Tree_Computations",
    "Comparison_based_Sorting",
    "Basic_Model_of_Locality",
    "IO_Avoiding_Algorithms",
    "Cache_Oblivious_Algorithms",
    "Intro_to_Dist_Memory_Models",
    "Topology",
    "Intro_to_MPI",
    "Dist_Dense_Matrix_Multiply",
    "Dist_Memory_Sorting",
    "Shared_Memory_Parallel_BFS",
    "Distributed_BFS",
    "Graph_Partitioning",
    "Conclusion"
]

base_dir = "local/CSE6220_Notes"

for i, name in enumerate(order):
    prefix = f"{i:02d}_"
    
    # rename synthesized notes
    old_syn = os.path.join(base_dir, f"{name}.md")
    new_syn = os.path.join(base_dir, f"{prefix}{name}.md")
    if os.path.exists(old_syn):
        os.rename(old_syn, new_syn)
        
    # rename raw transcripts
    old_raw = os.path.join(base_dir, f"{name}_Raw.md")
    new_raw = os.path.join(base_dir, f"{prefix}{name}_Raw.md")
    if os.path.exists(old_raw):
        os.rename(old_raw, new_raw)

print("Successfully renamed files with ordered prefixes.")
