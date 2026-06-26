import re
import json
import time
import sys
import os
import requests

APP_ID = 324684580
OUTPUT_FILE = 'data/1_app_store_reviews.json'
TARGET_COUNT = 1000

# Reconfigure stdout/stderr to support unicode/emojis in Windows console safely
for stream in (sys.stdout, sys.stderr):
    reconfig = getattr(stream, 'reconfigure', None)
    if reconfig:
        reconfig(encoding='utf-8')

# Inclusion keywords
INCLUSION_KEYWORDS = [
    # Recommendation
    "recommendation", "recommendations", "recommended", "recommend", "suggested", "suggestions", "algorithm", "algorithmic", "personalization", "personalized", "for you",
    # Repetition
    "same songs", "same song", "same artists", "same artist", "same genre", "repeated", "repetitive", "repeats", "repeating", "over and over", "again and again", "loop", "stuck", "stale", "boring", "not fresh", "always the same",
    # Discovery
    "discover", "discovery", "discovering", "new music", "new songs", "new artists", "find music", "finding music", "find songs", "explore", "exploration", "fresh music", "fresh songs", "different music",
    # Spotify feature
    "discover weekly", "daily mix", "release radar", "smart shuffle", "radio", "song radio", "artist radio", "autoplay", "dj", "ai playlist", "taste profile", "blend", "made for you", "liked songs", "playlists", "shuffle",
    # Mood/context/intent
    "mood", "vibe", "activity", "context", "gym", "workout", "study", "focus", "commute", "driving", "party", "sleep", "chill", "relax", "sad", "happy", "late night", "background music",
    # Feedback/control
    "dislike", "hide song", "hide this song", "not interested", "block artist", "remove recommendation", "stop recommending", "train algorithm", "feedback", "control", "customize", "filter", "preference", "improve recommendations",
    # Playlist fatigue
    "playlist fatigue", "playlist", "playlists", "mix", "mixes", "queue", "library", "liked songs", "shuffle", "smart shuffle", "daily mix",
    # Recommendation quality
    "bad recommendations", "poor recommendations", "terrible recommendations", "irrelevant", "unrelated", "random", "too random", "too similar", "too safe", "not my taste", "doesn’t match my taste", "wrong songs", "bad algorithm",
    # Off-platform discovery workaround
    "reddit", "instagram", "tiktok", "youtube", "shazam", "friends", "outside spotify", "other apps", "apple music", "soundcloud", "last.fm"
]

GENERIC_PRAISE = {
    "good app", "best app", "nice", "love spotify", "5 stars", "very good", "love it", 
    "great app", "excellent", "amazing", "perfect", "awesome", "good", "great", "love",
    "nice app", "thank you", "thanks", "super", "superb", "cool", "wonderful", "ok", "okay"
}

def clean_text_for_comparison(text):
    if not text:
        return ""
    text_clean = re.sub(r'[^\w\s]', '', text.lower()).strip()
    return text_clean

def is_emoji_only(text):
    if not text:
        return True
    return not any(c.isalnum() for c in text)

def is_generic_praise(text):
    text_clean = clean_text_for_comparison(text)
    if text_clean in GENERIC_PRAISE:
        return True
    return False

def is_relevant_review(text):
    if not text:
        return False
    
    # 1. Length check: at least 10 words
    words = text.split()
    if len(words) < 10:
        return False
        
    # 2. Emoji-only check
    if is_emoji_only(text):
        return False
        
    # 3. Generic praise check
    if is_generic_praise(text):
        return False
        
    # 4. Inclusion check: must contain at least one inclusion keyword
    text_lower = text.lower()
    has_inclusion = any(kw in text_lower for kw in INCLUSION_KEYWORDS)
    if not has_inclusion:
        return False
        
    return True

# Test cases to verify implementation
def run_tests():
    test_cases = [
        # Good/keep cases
        ("Too many ads, but my bigger issue is that Discover Weekly keeps giving me the same songs every week.", True),
        ("I love using the Spotify playlist feature for my workout, but the shuffle is not random.", True),
        ("It is a good app, but the algorithm is stuck playing the same artists over and over.", True),
        # Bad/reject cases
        ("Too many ads. I hate this app.", False),
        ("Great app. Love it.", False),
        ("Nice", False),
        ("😍👍🔥", False),
        ("This app crashes all the time when I try to login to my account.", False),
        ("I cannot download my songs for offline playback, please fix this bug.", False),
        ("The lyrics feature is not working for most of the songs.", False),
    ]
    
    print("Running filtering logic tests...")
    failed = 0
    for text, expected in test_cases:
        result = is_relevant_review(text)
        if result != expected:
            print(f"FAILED: [{text}] -> Expected: {expected}, Got: {result}")
            failed += 1
        else:
            print(f"PASSED: [{text[:40]}...] -> {result}")
    
    if failed == 0:
        print("All local tests passed successfully!\n")
        return True
    else:
        print(f"{failed} tests failed.\n")
        return False

def scrape_reviews():
    print(f"Starting App Store review scraper for Spotify (ID: {APP_ID}) to collect {TARGET_COUNT} relevant reviews...")
    
    collected = []
    seen_ids = set()
    
    # List of countries to cycle through to accumulate reviews
    countries = ["us", "gb", "ca", "au", "nz", "ie", "sg", "za", "in", "se", "no", "dk", "fi", "nl", "de", "fr", "it", "es", "br", "mx"]
    
    total_requested = 0
    
    for country in countries:
        if len(collected) >= TARGET_COUNT:
            break
            
        print(f"\n--- Scraping App Store reviews for country code: '{country.upper()}' ---")
        
        for page in range(1, 11): # iTunes RSS allows max 10 pages
            if len(collected) >= TARGET_COUNT:
                break
                
            url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={APP_ID}/sortby=mostrecent/json"
            total_requested += 1
            print(f"Fetching page {page} of reviews...")
            
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code != 200:
                    print(f"Non-200 response ({response.status_code}) for {country} page {page}. Skipping.")
                    time.sleep(1)
                    continue
                    
                data = response.json()
                feed = data.get('feed', {})
                entries = feed.get('entry', [])
                
                if not entries:
                    print(f"No reviews found on page {page} for {country}. Moving to next country.")
                    break
                
                # If there's only 1 review, entries could be a dictionary
                if isinstance(entries, dict):
                    entries = [entries]
                    
                new_relevant = 0
                for entry in entries:
                    # Some entries in RSS might represent app metadata, not reviews
                    if 'id' not in entry or 'content' not in entry:
                        continue
                        
                    review_id = entry['id'].get('label')
                    if not review_id or review_id in seen_ids:
                        continue
                        
                    content = entry['content'].get('label', '')
                    if is_relevant_review(content):
                        seen_ids.add(review_id)
                        
                        # Rating
                        rating_str = entry.get('im:rating', {}).get('label', '0')
                        rating = int(rating_str) if rating_str.isdigit() else 0
                        
                        # Upvotes (voteCount)
                        upvotes_str = entry.get('im:voteCount', {}).get('label', '0')
                        upvotes = int(upvotes_str) if upvotes_str.isdigit() else 0
                        
                        # Created at
                        created_at = entry.get('updated', {}).get('label', '')
                        
                        # App version
                        app_version = entry.get('im:version', {}).get('label', '')
                        
                        # Map to the Unified Schema
                        mapped_review = {
                            "review_id": review_id,
                            "source": "app_store",
                            "raw_text": content,
                            "clean_text": content,
                            "title": entry.get('title', {}).get('label', ''),
                            "rating": rating,
                            "upvotes_likes": upvotes,
                            "created_at": created_at,
                            "url": f"https://apps.apple.com/{country}/app/spotify-music-and-podcasts/id{APP_ID}?see-all=reviews",
                            "metadata": {
                                "app_version": app_version,
                                "country": country
                            }
                        }
                        collected.append(mapped_review)
                        new_relevant += 1
                        
                        if len(collected) >= TARGET_COUNT:
                            break
                            
                print(f"Page {page} processed. Found {new_relevant} new relevant reviews. Total collected: {len(collected)}/{TARGET_COUNT}")
                
                # Polite delay between page requests
                time.sleep(1.0)
                
            except Exception as e:
                print(f"Error fetching page {page} for {country}: {e}")
                time.sleep(2)
                continue
                
    # Truncate to exactly TARGET_COUNT if we went over
    collected = collected[:TARGET_COUNT]
    
    # Save to file
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(collected, f, indent=2, ensure_ascii=False)
        
    print(f"\nSuccessfully saved {len(collected)} relevant reviews to '{OUTPUT_FILE}'.")

if __name__ == "__main__":
    if run_tests():
        scrape_reviews()
