import urllib.request
import urllib.error
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import sys

base_url = "https://lowyx.com/posts/gt-gpu-M{}/"

for i in range(1, 13):
    url = base_url.format(i)
    filename = f"local/M{i}.md"
    print(f"Fetching {url}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        article = soup.find('article')
        
        if article:
            # Remove any unwanted elements if needed, like script tags or tail-wrapper
            for tag in article.find_all('script'):
                tag.decompose()
            tail = article.find(class_='post-tail-wrapper')
            if tail:
                tail.decompose()
                
            markdown_content = md(str(article), heading_style="ATX")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(markdown_content.strip())
            print(f"Saved {filename}")
        else:
            print(f"No <article> tag found in {url}")
    except urllib.error.URLError as e:
        print(f"Failed to fetch {url}: {e}")
    except Exception as e:
        print(f"Error processing {url}: {e}")

print("Done.")
