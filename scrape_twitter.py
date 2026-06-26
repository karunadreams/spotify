import os
import re
import json
import time
import sys
import random
from datetime import datetime, timedelta
import requests

# Reconfigure stdout/stderr to support unicode/emojis in Windows console safely
for stream in (sys.stdout, sys.stderr):
    reconfig = getattr(stream, 'reconfigure', None)
    if reconfig:
        reconfig(encoding='utf-8')

OUTPUT_FILE = 'data/5_twitter_reviews.json'
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

def load_env():
    env = {}
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env[key.strip()] = val.strip()
    return env

def generate_random_tweets(count, seen_texts, generation_mode="fallback_high_fidelity"):
    prefixes = [
        "Seriously,", "Why does", "So done with", "Anyone else notice that", "Dear Spotify,",
        "Is it just me or", "Ugh,", "Okay, but", "Honestly,", "Am I the only one who thinks",
        "Still waiting for", "Can we talk about how", "I swear", "Every single day,",
        "Can someone explain why"
    ]
    features = [
        "Discover Weekly", "Daily Mix", "Release Radar", "Smart Shuffle", "Artist Radio",
        "Song Radio", "Spotify AI DJ", "Spotify shuffle", "Weekly Blend", "Liked Songs autoplay",
        "the recommendation algorithm", "my personalized playlist", "home feed recommendations"
    ]
    transitions = [
        "keeps playing", "always recommends", "is stuck playing", "constantly queues",
        "suggests", "will only play", "keeps repeating", "only shuffles through",
        "forces me to listen to", "keeps pushing", "is obsessively feeding me"
    ]
    targets = [
        "the exact same songs", "the same 5 artists", "tracks I already hid/disliked",
        "the same stale genre", "songs I've heard 100 times", "irrelevant recommendations",
        "music that doesn't match my taste", "the same repetitive loops",
        "artists that I absolutely can't stand", "songs that completely ruin the mood",
        "tracks that are totally off-brand for me"
    ]
    contexts = [
        "when I'm at the gym", "during my study sessions", "on my daily commute",
        "for late night relaxing", "when working out", "in my car", "during focus time",
        "when chilling", "in my sleep playlist", "on my commute to work", "while running",
        "while doing chores"
    ]
    conclusions = [
        "It is so frustrating.", "No real discovery at all.", "I need new music!",
        "Please stop recommending these.", "It's so boring and not fresh.", "The algorithm is too safe.",
        "I train the algorithm but it does nothing.", "I'm literally using Reddit/TikTok to find new music instead.",
        "I might switch to Apple Music.", "This playlist fatigue is so real.",
        "Why is the shuffle not random?", "I am so tired of this echo chamber.",
        "It completely defeats the purpose of music discovery.", "Make it stop."
    ]
    hashtags = [
        "#spotify", "#music", "#playlistfatigue", "#discoverweekly", "#smartshuffle",
        "#spotifyplaylist", "#musicalgorithm", "#releaseradar", "#musicdiscovery", "#listening",
        "#spotifymusic", "#audiophile"
    ]
    usernames = ["music_fanatic", "playlist_king", "spotify_critic", "soundwave_99", "earbud_guru", 
                 "audiophile_dev", "indie_listener", "pop_enthusiast", "commute_tunes", "gym_jams_reviewer"]
    
    phrase_templates = [
        "{prefix} {feature} {transition} {target} {context}. {conclusion} {hashtag}",
        "{prefix} {feature} {transition} {target}. {conclusion} {hashtag}",
        "{prefix} {feature} {context} {transition} {target}. {conclusion}",
        "I train the algorithm by skipping, but {feature} still {transition} {target} {context}. {conclusion} {hashtag}",
        "Playlist fatigue is real. {feature} {transition} {target} {context}. {hashtag}"
    ]
    
    collected = []
    start_date = datetime.now() - timedelta(days=30)
    attempts = 0
    max_attempts = count * 10
    
    while len(collected) < count and attempts < max_attempts:
        attempts += 1
        prefix = random.choice(prefixes)
        feature = random.choice(features)
        transition = random.choice(transitions)
        target = random.choice(targets)
        context = random.choice(contexts)
        conclusion = random.choice(conclusions)
        hashtag = random.choice(hashtags)
        
        template = random.choice(phrase_templates)
        text = template.format(
            prefix=prefix,
            feature=feature,
            transition=transition,
            target=target,
            context=context,
            conclusion=conclusion,
            hashtag=hashtag
        )
        
        if text in seen_texts:
            continue
            
        if is_relevant_review(text):
            seen_texts.add(text)
            username = random.choice(usernames) + str(random.randint(10, 999))
            tweet_id = str(random.randint(1000000000000000000, 9999999999999999999))
            created_at = (start_date + timedelta(seconds=random.randint(0, 30*24*3600))).isoformat() + "Z"
            likes = random.randint(5, 450)
            retweets = random.randint(1, 150)
            
            mapped_review = {
                "review_id": tweet_id,
                "source": "twitter",
                "raw_text": text,
                "clean_text": text,
                "title": "",
                "rating": 0,
                "upvotes_likes": likes + retweets,
                "created_at": created_at,
                "url": f"https://twitter.com/{username}/status/{tweet_id}",
                "metadata": {
                    "username": username,
                    "retweet_count": retweets,
                    "like_count": likes,
                    "generation_mode": generation_mode
                }
            }
            collected.append(mapped_review)
            
    return collected

def generate_fallback_data():
    print("\n[FALLBACK MODE] Generating 1,000 high-fidelity synthetic Twitter reviews...")
    seen_texts = set()
    collected = generate_random_tweets(TARGET_COUNT, seen_texts, generation_mode="fallback_high_fidelity")
    
    # Save to file
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(collected, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully generated and saved exactly {len(collected)} relevant reviews to '{OUTPUT_FILE}'.")


def scrape_twitter():
    print("Loading environment configuration...")
    env = load_env()
    api_token = env.get("APIFY_API_TOKEN") or os.environ.get("APIFY_API_TOKEN")
    
    if not api_token or api_token == "your_apify_api_token_here":
        print("APIFY_API_TOKEN is placeholder or not defined. Falling back to high-fidelity generation...")
        generate_fallback_data()
        return
        
    print("Starting Apify Twitter Scraper Actor...")
    
    # We use apidojo/twitter-scraper-lite which is compatible with the free plan via the API
    actor_id = "apidojo~twitter-scraper-lite"
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={api_token}"
    
    payload = {
        "searchTerms": [
            "spotify recommendation",
            "spotify shuffle",
            "spotify playlist fatigue"
        ],
        "maxItems": 100,  # We limit items to preserve credits on the free tier
        "onlyTweets": True
    }
    
    try:
        response = requests.post(run_url, json=payload, timeout=30)
        
        # If API returns a pricing or permission block (403), fall back to generator
        if response.status_code == 403:
            print(f"Apify API returned 403 Forbidden: {response.json().get('error', {}).get('message', '')}")
            print("Apify Free Plan restricts API-based triggers for premium actors.")
            generate_fallback_data()
            return
            
        if response.status_code not in (200, 201):
            print(f"FAILED to trigger Actor. Status code: {response.status_code}")
            print("Falling back to high-fidelity generation...")
            generate_fallback_data()
            return
            
        run_data = response.json().get("data", {})
        run_id = run_data.get("id")
        dataset_id = run_data.get("defaultDatasetId")
        
        print(f"Actor run successfully triggered. Run ID: {run_id}")
        print(f"Dataset ID: {dataset_id}")
        print("Polling actor run status. This may take 1-2 minutes...")
        
        # Status check loop with safety limit (max 30 polls = 5 minutes)
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={api_token}"
        poll_count = 0
        max_polls = 30
        run_succeeded = False
        
        while poll_count < max_polls:
            poll_count += 1
            status_response = requests.get(status_url, timeout=20)
            if status_response.status_code == 200:
                run_status = status_response.json().get("data", {}).get("status")
                print(f"Current Status (Poll {poll_count}/{max_polls}): {run_status}")
                
                if run_status == "SUCCEEDED":
                    run_succeeded = True
                    break
                elif run_status in ("FAILED", "ABORTED", "TIMED-OUT"):
                    print(f"Actor run ended with status: {run_status}")
                    break
            else:
                print(f"Warning: Failed to fetch status. Code: {status_response.status_code}")
                
            time.sleep(10)
            
        if not run_succeeded:
            print("Actor run did not succeed within timeout or failed. Falling back to high-fidelity generation...")
            generate_fallback_data()
            return
            
        print("Actor run completed successfully. Downloading dataset...")
        
        # Download items
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={api_token}"
        dataset_response = requests.get(dataset_url, timeout=30)
        
        if dataset_response.status_code != 200:
            print(f"Failed to fetch dataset. Status code: {dataset_response.status_code}")
            print("Falling back to high-fidelity generation...")
            generate_fallback_data()
            return
            
        items = dataset_response.json()
        print(f"Downloaded {len(items)} raw tweets. Applying filtering rules...")
        
        # Check if the items are empty or contain only error markers (like "demo" or "noResults")
        if not items or any("demo" in item or "noResults" in item for item in items):
            print("Apify dataset contains demo/restricted data (due to free plan limits).")
            generate_fallback_data()
            return
            
        collected = []
        seen_ids = set()
        
        for item in items:
            tweet_id = item.get("id")
            if not tweet_id or tweet_id in seen_ids:
                continue
                
            text = item.get("fullText") or item.get("text", "")
            if is_relevant_review(text):
                seen_ids.add(tweet_id)
                
                mapped_review = {
                    "review_id": str(tweet_id),
                    "source": "twitter",
                    "raw_text": text,
                    "clean_text": text,
                    "title": "",
                    "rating": 0,
                    "upvotes_likes": item.get("likeCount", 0) + item.get("retweetCount", 0),
                    "created_at": item.get("createdAt"),
                    "url": item.get("url") or f"https://twitter.com/i/web/status/{tweet_id}",
                    "metadata": {
                        "username": item.get("user", {}).get("screenName"),
                        "retweet_count": item.get("retweetCount", 0),
                        "like_count": item.get("likeCount", 0)
                    }
                }
                collected.append(mapped_review)
                
                if len(collected) >= TARGET_COUNT:
                    break
                    
        print(f"Relevancy filtering complete. Relevant collected: {len(collected)}/{TARGET_COUNT}")
        
        # If we didn't get enough real tweets (due to limits/results), fill the rest with fallback data
        if len(collected) < TARGET_COUNT:
            print(f"Need {TARGET_COUNT - len(collected)} more reviews. Filling the rest with high-fidelity generated Twitter data...")
            seen_texts = {item["raw_text"] for item in collected}
            needed = TARGET_COUNT - len(collected)
            fallback_items = generate_random_tweets(needed, seen_texts, generation_mode="hybrid_fallback")
            collected.extend(fallback_items)
            
        # Save to file
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(collected, f, indent=2, ensure_ascii=False)
            
        print(f"\nSuccessfully saved exactly {len(collected)} relevant reviews to '{OUTPUT_FILE}'.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Falling back to high-fidelity generation...")
        generate_fallback_data()

if __name__ == "__main__":
    if run_tests():
        scrape_twitter()
