#!/usr/bin/env python3
"""
Scrapes YouTube playlists and outputs all video links to a CSV file.

Usage:
    python scrape.py <input_file>

Where input_file contains one playlist URL per line.

Example input file (playlists.txt):
    https://www.youtube.com/playlist?list=PLAwxTw4SYaPkr-vo9gKBTid_BWpWEfuXe
    https://www.youtube.com/playlist?list=ANOTHER_PLAYLIST_ID
    https://www.youtube.com/playlist?list=YET_ANOTHER_ID

Run:
    python scrape.py playlists.txt

Output:
    Creates a CSV file (playlists.csv) with 'url' and 'title' columns.
"""

import sys
import subprocess
import json
import os
import csv


def scrape_playlist(playlist_url):
    """
    Scrapes a YouTube playlist and extracts video URLs with titles.
    
    Args:
        playlist_url (str): The YouTube playlist URL
        
    Returns:
        list: A list of dicts with 'url' and 'title' keys from the playlist
    """
    try:
        # Ask yt-dlp for the full playlist metadata in one JSON object.
        # This avoids depending on line-by-line output and makes it clear
        # that we are parsing the complete playlist entries returned by yt-dlp.
        result = subprocess.run(
            [
                "yt-dlp",
                "--flat-playlist",
                "--dump-single-json",
                "--no-warnings",
                playlist_url
            ],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"Error: {result.stderr}", file=sys.stderr)
            return []
        
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            print("Error: yt-dlp returned invalid JSON.", file=sys.stderr)
            return []

        video_data = []
        for entry in payload.get('entries') or []:
            url = entry.get('url')
            if not url and entry.get('id'):
                url = f"https://www.youtube.com/watch?v={entry['id']}"

            if not url:
                continue

            title = entry.get('title') or 'Unknown Title'
            video_data.append({'url': url, 'title': title})
        
        return video_data
        
    except FileNotFoundError:
        print("Error: yt-dlp not found. Please install it with: pip install yt-dlp", file=sys.stderr)
        return []


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input_file>", file=sys.stderr)
        print(f"\nInput file should contain one playlist URL per line.", file=sys.stderr)
        print(f"\nExample: {sys.argv[0]} playlists.txt", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Read playlist URLs from input file
    try:
        with open(input_file, 'r') as f:
            playlist_urls = [
                url.strip()
                for url in f
                if url.strip() and not url.lstrip().startswith('#')
            ]
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    
    if not playlist_urls:
        print(f"Error: No URLs found in '{input_file}'.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Processing {len(playlist_urls)} playlist(s)...")
    
    all_videos = []
    for i, playlist_url in enumerate(playlist_urls, 1):
        print(f"  [{i}/{len(playlist_urls)}] Scraping: {playlist_url}")
        video_data = scrape_playlist(playlist_url)
        print(f"      Found {len(video_data)} videos")
        all_videos.extend(video_data)
    
    if not all_videos:
        print("No videos found in any of the playlists.", file=sys.stderr)
        sys.exit(1)
    
    # Generate combined output filename
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f"{base_name}.csv"
    
    # Write combined URLs and titles to CSV file
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'title'])
        writer.writeheader()
        for item in all_videos:
            writer.writerow({'url': item['url'], 'title': item['title']})
    
    print(f"\n✓ Found {len(all_videos)} total videos")
    print(f"✓ Saved to {output_file}")


if __name__ == "__main__":
    main()
