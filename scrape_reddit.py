import os
import re
import json
import time
import sys
from datetime import datetime, timezone
import requests

# Reconfigure stdout/stderr to support unicode/emojis in Windows console safely
for stream in (sys.stdout, sys.stderr):
    reconfig = getattr(stream, 'reconfigure', None)
    if reconfig:
        reconfig(encoding='utf-8')

OUTPUT_FILE = 'data/3_reddit_reviews.json'
TARGET_COUNT = 1000

LOCAL_POSTS_FILE = r"C:\Users\Karuna\Downloads\r_spotify_posts.jsonl"
LOCAL_COMMENTS_FILE = r"C:\Users\Karuna\Downloads\r_spotify_comments.jsonl"

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

def format_timestamp(utc_timestamp):
    try:
        if isinstance(utc_timestamp, (int, float)):
            return datetime.fromtimestamp(utc_timestamp, timezone.utc).isoformat() + "Z"
        return str(utc_timestamp)
    except Exception:
        return str(utc_timestamp)

def process_local_files():
    print("Searching for pre-downloaded Reddit JSONL files...")
    if not os.path.exists(LOCAL_POSTS_FILE) or not os.path.exists(LOCAL_COMMENTS_FILE):
        print("Local JSONL files not found in Downloads. Falling back to Arctic Shift API mode...")
        return None
        
    collected = []
    seen_ids = set()
    
    # 1. Process posts
    print(f"Processing posts from: {LOCAL_POSTS_FILE}")
    posts_processed = 0
    with open(LOCAL_POSTS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            try:
                post = json.loads(line)
                post_id = post.get('id')
                if not post_id or post_id in seen_ids:
                    continue
                    
                title = post.get('title', '')
                selftext = post.get('selftext', '')
                
                # Combine title and selftext for relevance checking
                full_text = f"{title}\n{selftext}".strip()
                
                if is_relevant_review(full_text):
                    seen_ids.add(post_id)
                    
                    mapped_review = {
                        "review_id": post_id,
                        "source": "reddit",
                        "raw_text": full_text,
                        "clean_text": full_text,
                        "title": title,
                        "rating": 0,
                        "upvotes_likes": post.get('score', 0),
                        "created_at": format_timestamp(post.get('created_utc')),
                        "url": f"https://reddit.com{post.get('permalink', '')}",
                        "metadata": {
                            "subreddit": post.get('subreddit', 'spotify'),
                            "type": "post"
                        }
                    }
                    collected.append(mapped_review)
                    posts_processed += 1
                    
                    if len(collected) >= TARGET_COUNT:
                        break
            except Exception:
                continue
                
    print(f"Finished processing posts. Relevant collected so far: {len(collected)}/{TARGET_COUNT}")
    
    # 2. Process comments
    if len(collected) < TARGET_COUNT:
        print(f"Processing comments from: {LOCAL_COMMENTS_FILE}")
        comments_processed = 0
        with open(LOCAL_COMMENTS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                try:
                    comment = json.loads(line)
                    comment_id = comment.get('id')
                    if not comment_id or comment_id in seen_ids:
                        continue
                        
                    body = comment.get('body', '')
                    if is_relevant_review(body):
                        seen_ids.add(comment_id)
                        
                        mapped_review = {
                            "review_id": comment_id,
                            "source": "reddit",
                            "raw_text": body,
                            "clean_text": body,
                            "title": "",
                            "rating": 0,
                            "upvotes_likes": comment.get('score', 0),
                            "created_at": format_timestamp(comment.get('created_utc')),
                            "url": f"https://reddit.com{comment.get('permalink', '')}",
                            "metadata": {
                                "subreddit": comment.get('subreddit', 'spotify'),
                                "type": "comment"
                            }
                        }
                        collected.append(mapped_review)
                        comments_processed += 1
                        
                        if len(collected) >= TARGET_COUNT:
                            break
                except Exception:
                    continue
                    
        print(f"Finished processing comments. Relevant collected: {len(collected)}/{TARGET_COUNT}")
        
    return collected[:TARGET_COUNT]

def fetch_from_api():
    print("Starting API-based Reddit scraper via Arctic Shift...")
    collected = []
    seen_ids = set()
    
    # Search keywords to get relevant threads
    keywords = ["recommendation", "shuffle", "algorithm", "same songs", "playlist fatigue"]
    
    # Process posts
    for keyword in keywords:
        if len(collected) >= TARGET_COUNT:
            break
            
        print(f"Searching API for posts with keyword: '{keyword}'...")
        url = f"https://arctic-shift.photon-reddit.com/api/posts/search?subreddit=spotify&q={keyword}&limit=100"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"Non-200 status code: {response.status_code}")
                continue
                
            data = response.json()
            posts = data.get('data', [])
            
            new_relevant = 0
            for post in posts:
                post_id = post.get('id')
                if not post_id or post_id in seen_ids:
                    continue
                    
                title = post.get('title', '')
                selftext = post.get('selftext', '')
                full_text = f"{title}\n{selftext}".strip()
                
                if is_relevant_review(full_text):
                    seen_ids.add(post_id)
                    
                    mapped_review = {
                        "review_id": post_id,
                        "source": "reddit",
                        "raw_text": full_text,
                        "clean_text": full_text,
                        "title": title,
                        "rating": 0,
                        "upvotes_likes": post.get('score', 0),
                        "created_at": format_timestamp(post.get('created_utc')),
                        "url": f"https://reddit.com{post.get('permalink', '')}",
                        "metadata": {
                            "subreddit": post.get('subreddit', 'spotify'),
                            "type": "post"
                        }
                    }
                    collected.append(mapped_review)
                    new_relevant += 1
                    
                    if len(collected) >= TARGET_COUNT:
                        break
            print(f"Found {new_relevant} new relevant posts. Total collected: {len(collected)}/{TARGET_COUNT}")
            time.sleep(1.0)
        except Exception as e:
            print(f"Error fetching API posts: {e}")
            time.sleep(2)
            
    # Process comments if needed
    if len(collected) < TARGET_COUNT:
        for keyword in keywords:
            if len(collected) >= TARGET_COUNT:
                break
                
            print(f"Searching API for comments with keyword: '{keyword}'...")
            url = f"https://arctic-shift.photon-reddit.com/api/comments/search?subreddit=spotify&q={keyword}&limit=100"
            
            try:
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    print(f"Non-200 status code: {response.status_code}")
                    continue
                    
                data = response.json()
                comments = data.get('data', [])
                
                new_relevant = 0
                for comment in comments:
                    comment_id = comment.get('id')
                    if not comment_id or comment_id in seen_ids:
                        continue
                        
                    body = comment.get('body', '')
                    if is_relevant_review(body):
                        seen_ids.add(comment_id)
                        
                        mapped_review = {
                            "review_id": comment_id,
                            "source": "reddit",
                            "raw_text": body,
                            "clean_text": body,
                            "title": "",
                            "rating": 0,
                            "upvotes_likes": comment.get('score', 0),
                            "created_at": format_timestamp(comment.get('created_utc')),
                            "url": f"https://reddit.com{comment.get('permalink', '')}",
                            "metadata": {
                                "subreddit": comment.get('subreddit', 'spotify'),
                                "type": "comment"
                            }
                        }
                        collected.append(mapped_review)
                        new_relevant += 1
                        
                        if len(collected) >= TARGET_COUNT:
                            break
                print(f"Found {new_relevant} new relevant comments. Total collected: {len(collected)}/{TARGET_COUNT}")
                time.sleep(1.0)
            except Exception as e:
                print(f"Error fetching API comments: {e}")
                time.sleep(2)
                
    return collected[:TARGET_COUNT]

def main():
    collected = process_local_files()
    if collected is None:
        collected = fetch_from_api()
        
    if not collected:
        print("No reviews collected.")
        return
        
    # Truncate to exactly TARGET_COUNT if we went over
    collected = collected[:TARGET_COUNT]
    
    # Save to file
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(collected, f, indent=2, ensure_ascii=False)
        
    print(f"\nSuccessfully saved exactly {len(collected)} relevant reviews to '{OUTPUT_FILE}'.")

if __name__ == "__main__":
    if run_tests():
        main()
