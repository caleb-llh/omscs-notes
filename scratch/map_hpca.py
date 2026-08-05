import glob
import re

files = sorted(glob.glob("local/HPCA_Notes/*_Raw.md"))

for f in files:
    with open(f, "r") as file:
        content = file.read()
        headers = re.findall(r'^## (.*)', content, flags=re.MULTILINE)
        if headers:
            print(f"{f}: {headers[0]} ... {headers[-1]}")
