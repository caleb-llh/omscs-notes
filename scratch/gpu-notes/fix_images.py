import os
import glob

for filepath in glob.glob("local/M*.md"):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace the relative paths with absolute URLs
    content = content.replace("](/../../../", "](https://lowyx.com/")
    content = content.replace('src="/../../../', 'src="https://lowyx.com/')
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Fixed images in {filepath}")
