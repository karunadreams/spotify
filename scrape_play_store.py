import re
import json
import time
import sys
import os
from datetime import datetime
from google_play_scraper import reviews, Sort

# Reconfigure stdout/stderr to support unicode/emojis in Windows console safely
for stream in (sys.stdout, sys.stderr):
    reconfig = getattr(stream, 'reconfigure', None)
    if reconfig:
        reconfig(encoding='utf-8')


APP_ID = 'com.spotify.music'
OUTPUT_FILE = 'data/2_play_store_reviews.json'
TARGET_COUNT = 1000

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
    print(f"Starting review scraper for Spotify ({APP_ID}) to collect {TARGET_COUNT} relevant reviews...")
    
    collected = []
    seen_ids = set()
    continuation_token = None
    batch_size = 500
    total_fetched = 0
    
    # Run the scraper loop
    while len(collected) < TARGET_COUNT:
        try:
            print(f"Fetching batch of up to {batch_size} reviews...")
            if continuation_token:
                batch_raw, continuation_token = reviews(
                    APP_ID,
                    lang='en',
                    country='us',
                    sort=Sort.NEWEST,
                    count=batch_size,
                    continuation_token=continuation_token
                )
            else:
                batch_raw, continuation_token = reviews(
                    APP_ID,
                    lang='en',
                    country='us',
                    sort=Sort.NEWEST,
                    count=batch_size
                )
            
            if not batch_raw:
                print("No more reviews returned from Play Store API.")
                break
                
            total_fetched += len(batch_raw)
            print(f"Fetched {len(batch_raw)} reviews (Total raw fetched so far: {total_fetched})")
            
            new_relevant = 0
            for r in batch_raw:
                review_id = r.get('reviewId')
                if review_id in seen_ids:
                    continue
                
                content = r.get('content', '')
                if is_relevant_review(content):
                    seen_ids.add(review_id)
                    
                    # Map to the Unified Schema
                    mapped_review = {
                        "review_id": review_id,
                        "source": "play_store",
                        "raw_text": content,
                        "clean_text": content,
                        "title": None,
                        "rating": r.get('score'),
                        "upvotes_likes": r.get('thumbsUpCount', 0),
                        # Convert datetime object to ISO string
                        "created_at": r.get('at').isoformat() if isinstance(r.get('at'), datetime) else str(r.get('at')),
                        "url": f"https://play.google.com/store/apps/details?id={APP_ID}&reviewId={review_id}",
                        "metadata": {
                            "app_version": r.get('reviewCreatedVersion')
                        }
                    }
                    collected.append(mapped_review)
                    new_relevant += 1
                    
                    if len(collected) >= TARGET_COUNT:
                        break
                        
            print(f"Found {new_relevant} new relevant reviews in this batch. Total relevant collected: {len(collected)}/{TARGET_COUNT}")
            
            # Rate limiting mitigation
            time.sleep(1.5)
            
        except Exception as e:
            print(f"Error during scraping batch: {e}")
            print("Waiting 5 seconds before retrying...")
            time.sleep(5)
            
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
