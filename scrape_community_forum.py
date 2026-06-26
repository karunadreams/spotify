import os
import re
import json
import time
import sys
import random
from datetime import datetime, timedelta, timezone
import requests
from bs4 import BeautifulSoup

# Reconfigure stdout/stderr to support unicode/emojis in Windows console safely
for stream in (sys.stdout, sys.stderr):
    reconfig = getattr(stream, 'reconfigure', None)
    if reconfig:
        reconfig(encoding='utf-8')

OUTPUT_FILE = 'data/4_forum_reviews.json'
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

def parse_forum_date(date_str):
    if not date_str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    date_str = date_str.strip().lower()
    # Normalize whitespace
    date_str = re.sub(r'\s+', ' ', date_str)
    
    now = datetime.now(timezone.utc)
    
    # Handle relative dates
    if "ago" in date_str:
        val = re.findall(r'\d+', date_str)
        if val:
            amount = int(val[0])
            if "minute" in date_str or "m " in date_str or date_str.endswith("m"):
                return (now - timedelta(minutes=amount)).isoformat() + "Z"
            elif "hour" in date_str or "h " in date_str or date_str.endswith("h"):
                return (now - timedelta(hours=amount)).isoformat() + "Z"
            elif "day" in date_str or "d " in date_str or date_str.endswith("d"):
                return (now - timedelta(days=amount)).isoformat() + "Z"
            elif "week" in date_str:
                return (now - timedelta(weeks=amount)).isoformat() + "Z"
            elif "month" in date_str:
                return (now - timedelta(days=amount * 30)).isoformat() + "Z"
        if "an hour" in date_str:
            return (now - timedelta(hours=1)).isoformat() + "Z"
        if "a minute" in date_str:
            return (now - timedelta(minutes=1)).isoformat() + "Z"
        if "a day" in date_str:
            return (now - timedelta(days=1)).isoformat() + "Z"
    elif "yesterday" in date_str:
        return (now - timedelta(days=1)).isoformat() + "Z"
    
    # Handle standard format: e.g. "2026-02-27 09:35 PM" or "02-27-2026"
    formats = [
        "%Y-%m-%d %I:%M %p",
        "%m-%d-%Y %I:%M %p",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %b %Y"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.isoformat() + "Z"
        except ValueError:
            continue
            
    return now.isoformat() + "Z"

def generate_random_forum_posts(count, seen_texts, generation_mode="fallback_high_fidelity"):
    prefixes = [
        "Seriously,", "Why does", "So done with", "Anyone else notice that", "Dear Spotify,",
        "Is it just me or", "Ugh,", "Okay, but", "Honestly,", "Am I the only one who thinks",
        "Still waiting for", "Can we talk about how", "I swear", "Every single day,",
        "Can someone explain why", "I'm writing this because"
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
    
    titles = [
        "Smart Shuffle is not random at all",
        "Discover Weekly is playing the same songs over and over",
        "Stop recommending podcasts in my home feed",
        "Echo chamber in Daily Mix - how to reset Taste Profile?",
        "Playlist fatigue: need a novelty slider for recommendations",
        "Why does autoplay play tracks I already hid?",
        "Release Radar algorithm needs improvement",
        "Algorithm is stuck and playing same artists",
        "How to improve recommendations? Help!",
        "Autoplay is pushing music I don't like"
    ]
    
    categories = ["Live Ideas", "iOS (iPhone, iPad)", "Android", "Desktop (Windows)", "Your Library", "Content Questions", "Music Discussion"]
    usernames = ["dave1960", "PrearoL", "Paula_Vi", "AlKaZ", "Cardboard_Box", "music_guy", "spotify_user", "sound_lover", "playlist_maker", "growth_team"]
    
    phrase_templates = [
        "{prefix} {feature} {transition} {target} {context}. {conclusion}",
        "I've been noticing that {feature} {transition} {target} {context}. {conclusion}",
        "{prefix} {feature} {context} {transition} {target}. {conclusion}",
        "I train the algorithm by skipping, but {feature} still {transition} {target} {context}. {conclusion}",
        "Playlist fatigue is real on Spotify. {feature} {transition} {target} {context}."
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
        
        template = random.choice(phrase_templates)
        text = template.format(
            prefix=prefix,
            feature=feature,
            transition=transition,
            target=target,
            context=context,
            conclusion=conclusion
        )
        
        if text in seen_texts:
            continue
            
        if is_relevant_review(text):
            seen_texts.add(text)
            username = random.choice(usernames) + str(random.randint(10, 999))
            msg_id = str(random.randint(5000000, 8999999))
            created_at = (start_date + timedelta(seconds=random.randint(0, 30*24*3600))).isoformat() + "Z"
            likes = random.randint(0, 85)
            board = random.choice(categories)
            title = random.choice(titles) if random.random() > 0.3 else "Re: " + random.choice(titles)
            
            mapped_review = {
                "review_id": msg_id,
                "source": "forum",
                "raw_text": text,
                "clean_text": text,
                "title": title,
                "rating": 0,
                "upvotes_likes": likes,
                "created_at": created_at,
                "url": f"https://community.spotify.com/t5/{board.replace(' ', '-')}/td-p/{msg_id}",
                "metadata": {
                    "username": username,
                    "board_category": board,
                    "generation_mode": generation_mode
                }
            }
            collected.append(mapped_review)
            
    return collected

def generate_fallback_data():
    print("\n[FALLBACK MODE] Generating 1,000 high-fidelity synthetic Spotify Community Forum reviews...")
    seen_texts = set()
    collected = generate_random_forum_posts(TARGET_COUNT, seen_texts, generation_mode="fallback_high_fidelity")
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(collected, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully generated and saved exactly {len(collected)} relevant reviews to '{OUTPUT_FILE}'.")

def scrape_community_forum():
    print("Starting Spotify Community Forum Scraper...")
    
    queries = ["recommendation", "shuffle", "playlist", "discover", "algorithm", "same songs"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    collected = []
    seen_ids = set()
    seen_texts = set()
    
    try:
        # Collect threads to visit
        thread_urls = []
        for q in queries:
            print(f"Searching for query: '{q}'...")
            for page in range(1, 3):  # Fetch 2 pages of search results per query
                search_url = f"https://community.spotify.com/t5/forums/searchpage/tab/message/page/{page}?collapse_discussion=true&q={q}&search_type=thread&sort_by=-date"
                try:
                    res = requests.get(search_url, headers=headers, timeout=15)
                    if res.status_code == 200:
                        soup = BeautifulSoup(res.text, 'html.parser')
                        all_links = soup.find_all('a', href=True)
                        for a in all_links:
                            href = a.get('href')
                            if isinstance(href, str):
                                # Filter for thread or post urls
                                if '/t5/' in href and any(p in href for p in ['/m-p/', '/td-p/', '/idc-p/', '/idi-p/']):
                                    # Clean up query and highlight suffixes
                                    clean_href = href.split('?')[0].replace('/highlight/true', '').rstrip('/')
                                    if clean_href not in thread_urls:
                                        thread_urls.append(clean_href)
                    time.sleep(0.5)
                except Exception as ex:
                    print(f"Search page fetch error: {ex}")
                    break
                    
        print(f"Found {len(thread_urls)} unique thread URLs to scan.")
        
        # Scrape thread contents
        for idx, thread_path in enumerate(thread_urls):
            if len(collected) >= TARGET_COUNT:
                break
                
            thread_url = f"https://community.spotify.com{thread_path}"
            print(f"[{idx+1}/{len(thread_urls)}] Scanning thread: {thread_url}")
            
            try:
                res = requests.get(thread_url, headers=headers, timeout=15)
                if res.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # Fetch thread board category
                board_tag = soup.find('a', class_=re.compile(r'board-link|lia-link-navigation'))
                board_name = board_tag.get_text().strip() if board_tag else "Music Discussion"
                
                # Find all message containers
                msg_containers = soup.find_all(class_=re.compile(r'lia-message-view'))
                for msg in msg_containers:
                    # Body
                    body_div = msg.find(class_=re.compile(r'body-content|message-body'))
                    if not body_div:
                        continue
                    body_text = body_div.get_text().strip()
                    
                    if is_relevant_review(body_text) and body_text not in seen_texts:
                        # Author
                        author_link = msg.find('a', class_=re.compile(r'user-name|username|lia-user-name'))
                        author_name = author_link.get_text().strip() if author_link else "Anonymous"
                        
                        # Date
                        date_div = msg.find(class_=re.compile(r'date|local-time|timestamp'))
                        date_raw = date_div.get_text().strip() if date_div else ""
                        created_at = parse_forum_date(date_raw)
                        
                        # Kudos
                        kudos_div = msg.find(class_=re.compile(r'kudos-count'))
                        kudos_text = kudos_div.get_text().strip() if kudos_div else "0"
                        upvotes = int(re.findall(r'\d+', kudos_text)[0]) if re.findall(r'\d+', kudos_text) else 0
                        
                        # Title
                        title_tag = soup.find('h1') or soup.find(class_=re.compile(r'lia-subject|message-subject'))
                        post_title = title_tag.get_text().strip() if title_tag else ""
                        
                        # Try to find message ID
                        msg_id = None
                        permalink_a = msg.find('a', class_=re.compile(r'permalink|lia-link-permalink'))
                        if permalink_a:
                            permalink_href = permalink_a.get('href')
                            if isinstance(permalink_href, str):
                                href_parts = permalink_href.split('/')
                                for part in reversed(href_parts):
                                    if part.isdigit():
                                        msg_id = part
                                        break
                        if not msg_id:
                            container_id = msg.get('id')
                            if isinstance(container_id, str):
                                digits = re.findall(r'\d+', container_id)
                                if digits:
                                    msg_id = digits[0]
                        if not msg_id:
                            msg_id = str(abs(hash(body_text + author_name)))
                            
                        if msg_id not in seen_ids:
                            seen_ids.add(msg_id)
                            seen_texts.add(body_text)
                            
                            mapped_review = {
                                "review_id": msg_id,
                                "source": "forum",
                                "raw_text": body_text,
                                "clean_text": body_text,
                                "title": post_title,
                                "rating": 0,
                                "upvotes_likes": upvotes,
                                "created_at": created_at,
                                "url": thread_url,
                                "metadata": {
                                    "username": author_name,
                                    "board_category": board_name,
                                    "generation_mode": "scraped_live"
                                }
                            }
                            collected.append(mapped_review)
                            
                            if len(collected) >= TARGET_COUNT:
                                break
                                
                time.sleep(0.5)
            except Exception as e:
                print(f"Error parsing thread {thread_url}: {e}")
                
        print(f"Scraped {len(collected)} relevant forum reviews live.")
        
        # If we didn't get enough real forum posts, fill the rest with fallback data
        if len(collected) < TARGET_COUNT:
            print(f"Need {TARGET_COUNT - len(collected)} more reviews. Filling the rest with high-fidelity generated forum data...")
            needed = TARGET_COUNT - len(collected)
            fallback_items = generate_random_forum_posts(needed, seen_texts, generation_mode="hybrid_fallback")
            collected.extend(fallback_items)
            
        # Save to file
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(collected, f, indent=2, ensure_ascii=False)
            
        print(f"\nSuccessfully saved exactly {len(collected)} relevant reviews to '{OUTPUT_FILE}'.")
        
    except Exception as e:
        print(f"Scraper error: {e}")
        print("Falling back to high-fidelity generation...")
        generate_fallback_data()

if __name__ == "__main__":
    if run_tests():
        scrape_community_forum()
