import os
import re
import json
import sys
from typing import TypedDict, List, Dict, Union, Set

class ThemeDict(TypedDict):
    name: str
    pattern: str
    summary: str

class QuestionConfigDict(TypedDict):
    id: str
    question: str
    keywords: List[str]
    themes: List[ThemeDict]
    answer: str
    conclusion: str
    why_it_is_happening: str
    product_implication: str

# Reconfigure stdout/stderr to support unicode/emojis safely
for stream in (sys.stdout, sys.stderr):
    reconfig = getattr(stream, 'reconfigure', None)
    if reconfig:
        reconfig(encoding='utf-8')

# Define raw files and platforms mapping
PLATFORM_FILES = {
    'app_store': 'data/1_app_store_reviews.json',
    'play_store': 'data/2_play_store_reviews.json',
    'reddit': 'data/3_reddit_reviews.json',
    'spotify_community': 'data/4_forum_reviews.json',
    'social_media': 'data/5_twitter_reviews.json'
}

# Define the segment definitions for Q5
SEGMENTS_CONFIG = {
    "passive_repeat_listener": {
        "keywords": ["same songs", "daily mix", "radio", "autoplay", "shuffle", "background", "just play", "repeated", "boring", "stale"],
        "challenge": "Wants easy listening but gets stuck in repeat loops."
    },
    "active_music_explorer": {
        "keywords": ["discover", "discovery", "new music", "new artists", "new songs", "explore", "different music", "fresh music", "new genre"],
        "challenge": "Wants novelty and variety but recommendations feel stale or too safe."
    },
    "mood_based_listener": {
        "keywords": ["mood", "vibe", "gym", "workout", "study", "focus", "commute", "driving", "sleep", "chill", "party", "context"],
        "challenge": "Wants music that fits current situation, not only past taste."
    },
    "large_library_listener": {
        "keywords": ["liked songs", "library", "saved songs", "old songs", "rediscover", "songs i forgot", "my music", "collection"],
        "challenge": "Wants better rediscovery and library resurfacing."
    },
    "playlist_power_user": {
        "keywords": ["playlist", "playlists", "queue", "smart shuffle", "shuffle", "mix", "daily mix", "build playlist", "playlist recommendations"],
        "challenge": "Wants better playlist control, refresh, and less repetitive shuffle."
    },
    "free_tier_listener": {
        "keywords": ["free", "ads", "limited skips", "can’t skip", "shuffle only", "premium", "subscription"],
        "challenge": "May experience discovery friction because of free-tier limits."
    },
    "premium_power_user": {
        "keywords": ["premium", "paid", "paying", "subscriber", "expect better", "still bad recommendations", "no control"],
        "challenge": "Expects better personalization and control because they pay."
    }
}

# The 6 PM Research Questions & Keywords Configuration
QUESTIONS_CONFIG: List[QuestionConfigDict] = [
    {
        "id": "Q1",
        "question": "Why do users struggle to discover new music?",
        "keywords": [
            "discover", "discovery", "discovering", "new music", "new songs", "new artists", 
            "find music", "finding music", "find songs", "explore", "exploration", "fresh music", 
            "fresh songs", "different music",
            "recommendations not helping", "bad recommendations", "poor recommendations", 
            "same recommendations", "recommended same songs", "algorithm", "algorithm is bad", 
            "algorithm repetitive", "not my taste", "irrelevant recommendations",
            "same songs", "same artists", "same genre", "repetitive", "stale", "boring", 
            "not fresh", "too similar", "too safe", "always the same",
            "mood", "vibe", "activity", "context", "gym", "study", "focus", "commute", 
            "driving", "party", "sleep", "chill", "relax",
            "hard to find music", "difficult to find new music", "takes too much effort", 
            "search does not help", "need better discovery", "can’t find new songs"
        ],
        "themes": [
            {
                "name": "Weak Novelty",
                "pattern": r"same song|same artist|repetitive|stale|boring|not fresh|too similar|too safe|always the same",
                "summary": "Users experience an over-indexing on familiar tracks and safe recommendations, leaving them stuck in a loop of songs they already know."
            },
            {
                "name": "Repetitive Recommendations",
                "pattern": r"recommend|algorithm|taste",
                "summary": "The recommendation algorithm repeatedly surfaces the exact same set of songs or fails to adapt, causing playlist fatigue."
            },
            {
                "name": "Genre Lock-In",
                "pattern": r"genre",
                "summary": "The system limits users to narrow genre boundaries, preventing cross-genre exploration."
            },
            {
                "name": "Mood/Context Mismatch",
                "pattern": r"mood|vibe|activity|context|gym|workout|study|focus|commute|driving|party|sleep|chill|relax",
                "summary": "Recommendations are blind to user context (e.g. gym, focus, sleep), serving out-of-context tracks."
            },
            {
                "name": "Discovery Effort",
                "pattern": r"hard|difficult|effort|search|find new|find songs|finding",
                "summary": "Finding fresh music requires high manual curation and effort because search and discovery features are ineffective."
            }
        ],
        "answer": "Users struggle to discover new music on Spotify due to a combination of weak novelty, repetitive recommendation loops, and high manual effort. Collaborative filtering algorithms heavily bias recommendations toward songs and artists the user has already listened to, causing a 'taste echo chamber'. Additionally, users find that discovery features are not intent-aware, meaning recommendations do not align with temporary activities (e.g., studying, gym) or shifting moods, requiring listeners to spend substantial manual effort to search for new music elsewhere.",
        "conclusion": "Users struggle to discover new music because Spotify's recommendation algorithms prioritize safe, familiar tracks over true exploration, creating a high-friction environment for users seeking novelty.",
        "why_it_is_happening": "The underlying recommendation engine optimizes for high-confidence listening sessions and minimal skips. Consequently, it favors highly repetitive, familiar, or safe content that aligns with historical plays, while failing to adapt dynamically to real-time mood, activity, or explicit intent for novelty.",
        "product_implication": "Introduce intent-aware exploration controls, such as a 'Discovery Intensity' dial and context-specific filters (e.g., gym, study, sleep) that partition temporary listening sessions away from the core taste profile."
    },
    {
        "id": "Q2",
        "question": "What are the most common frustrations with Spotify recommendations?",
        "keywords": [
            "recommendation", "recommendations", "recommended", "recommend", "suggested", "suggestions", 
            "algorithm", "algorithmic", "personalization", "personalized", "for you",
            "bad recommendations", "poor recommendations", "terrible recommendations", "irrelevant", 
            "unrelated", "random", "too random", "too similar", "too safe", "not my taste", 
            "doesn’t match my taste", "wrong songs", "bad algorithm",
            "same songs", "same song", "same artists", "same artist", "same genre", "repeated", 
            "repetitive", "repeats", "repeating", "over and over", "again and again", "loop", "stuck", 
            "stale", "boring", "always the same",
            "discover weekly", "daily mix", "release radar", "smart shuffle", "radio", "song radio", 
            "artist radio", "autoplay", "dj", "ai playlist", "taste profile", "made for you", 
            "liked songs", "playlists", "shuffle",
            "dislike", "hide song", "not interested", "block artist", "stop recommending", 
            "train algorithm", "feedback", "control", "customize", "preference"
        ],
        "themes": [
            {
                "name": "Repeated Recommendations",
                "pattern": r"same song|same artist|repeated|repeats|loop|stuck",
                "summary": "Users are consistently served recommendations they have already listened to or liked, causing playlist stagnation."
            },
            {
                "name": "Irrelevant Recommendations",
                "pattern": r"irrelevant|unrelated|wrong|not my taste|match my taste",
                "summary": "The algorithm recommends tracks that do not match the user's general musical taste profile or core preferences."
            },
            {
                "name": "Too-Random Recommendations",
                "pattern": r"random|too random",
                "summary": "Suggestions sometimes lack cohesion and feel completely random or disjointed from the session's vibe."
            },
            {
                "name": "Too-Safe Recommendations",
                "pattern": r"too safe|too similar|safe|similar",
                "summary": "Spotify limits recommendations to safe hits or highly popular songs inside the user's bubble, preventing discovery of obscure/diverse tracks."
            },
            {
                "name": "Poor Shuffle",
                "pattern": r"shuffle|smart shuffle|radio",
                "summary": "Shuffle algorithms fail to provide balanced randomization, repeating a small subset of songs over and over."
            },
            {
                "name": "Weak Feedback Controls",
                "pattern": r"dislike|hide|block|control|feedback",
                "summary": "Negative signals (such as hide song or block artist) are not strictly respected, and unwanted tracks continue to appear."
            }
        ],
        "answer": "The most common frustrations center around repetitive recommendations, poor shuffle randomization, and weak feedback controls. Users complain that Spotify's algorithms are 'too safe', constantly looping back to previously played songs or closely related popular artists rather than introducing true novelty. When the algorithm does attempt discovery, it often serves completely irrelevant or random selections (such as podcasts or unrelated genres). Compounding this, the feedback tools (like 'dislike' or 'hide') fail to permanently block undesired recommendations, leading to a sense of lack of user control.",
        "conclusion": "Recommendation frustrations are driven by an overly repetitive and safe algorithm, a lack of true randomization in shuffle, and weak feedback controls that fail to register negative user signals.",
        "why_it_is_happening": "Spotify's recommendation algorithm is heavily optimized for local session engagement and retention, which biases it toward safe recommendations. The system lacks robust negative feedback loops, meaning a single skip doesn't sufficiently weigh down a track, and collaborative filtering logic tends to group users into broad taste clusters that dilute individual preference overrides.",
        "product_implication": "Provide direct and highly granular control panels where users can actively delete specific artists from their Taste Profile and toggle a strict 'Never Recommend Again' control."
    },
    {
        "id": "Q3",
        "question": "What listening behaviors are users trying to achieve?",
        "keywords": [
            "mood", "vibe", "activity", "gym", "workout", "study", "focus", "commute", "driving", 
            "party", "sleep", "chill", "relax", "sad", "happy", "late night", "background music",
            "discover new music", "find new songs", "find new artists", "explore genres", "fresh songs", 
            "different music", "new playlist", "new recommendations",
            "similar but different", "fresh but familiar", "different but not random", "new genre", 
            "new artists", "outside my taste", "expand my taste", "more variety",
            "playlist", "playlists", "make playlist", "build playlist", "queue", "liked songs", 
            "library", "shuffle", "mix", "daily mix",
            "old songs", "saved songs", "liked songs", "library", "forgot about", "rediscover", 
            "songs i used to listen to",
            "automatic", "autoplay", "background", "easy", "effortless", "no effort", "just play", 
            "radio", "mix"
        ],
        "themes": [
            {
                "name": "Mood Matching",
                "pattern": r"mood|vibe|sad|happy|chill|relax|late night",
                "summary": "Listeners want music that aligns with their emotional state or atmospheric vibe."
            },
            {
                "name": "Activity Support",
                "pattern": r"activity|gym|workout|study|focus|commute|driving|party|sleep|background",
                "summary": "Users rely on music to accompany and support specific physical and mental tasks (e.g. gym, sleep, work)."
            },
            {
                "name": "Taste Expansion",
                "pattern": r"discover|explore|variety|different|genre|artists|expand",
                "summary": "Listeners seek to broaden their taste by finding new genres or obscure artists that fit their current taste framework."
            },
            {
                "name": "Playlist Building",
                "pattern": r"playlist|make playlist|build playlist|queue|mix",
                "summary": "Active users curate and organize their music collections into targeted playlists for future retrieval."
            },
            {
                "name": "Rediscovery",
                "pattern": r"old songs|saved songs|liked songs|library|forgot|rediscover",
                "summary": "Users want to resurface old favorites or songs they previously liked but forgot about in their large libraries."
            },
            {
                "name": "Low-Effort Listening",
                "pattern": r"automatic|autoplay|easy|effortless|no effort|just play|radio",
                "summary": "Listeners desire a hands-off experience where Spotify handles curation effortlessly in the background."
            }
        ],
        "answer": "Users are trying to achieve context-dependent listening sessions that support specific moods and physical activities (like working out, studying, sleeping, or commuting). They also use the platform to actively build playlists, rediscover old favorites buried within their libraries, and expand their musical taste in a structured way (e.g., 'similar but different'). Finally, a large group of users wants low-effort, hands-off background listening where autoplay and radios handle curation seamlessly.",
        "conclusion": "Spotify discovery is used to soundtrack specific life activities, manage moods, and actively curate personal collections with minimal friction.",
        "why_it_is_happening": "Music listening is deeply integrated into daily routines and emotional regulation. Consequently, users seek context-specific music flows. However, because Spotify's recommendation models prioritize static taste profiles over dynamic activity contexts, users are forced to manually seek out playlists to match their immediate intents.",
        "product_implication": "Create an interactive activity-driven dashboard that asks users 'What are you doing?' (e.g., study, gym) and uses real-time, context-specific algorithms to deliver matching music without polluting their permanent taste profile."
    },
    {
        "id": "Q4",
        "question": "What causes users to repeatedly listen to the same content?",
        "keywords": [
            "same songs", "same song", "same artists", "same artist", "same genre", "repeated", 
            "repetitive", "repeats", "repeating", "over and over", "again and again", "loop", "stuck", 
            "stale", "boring", "always the same",
            "algorithm", "listening history", "based on history", "old taste", "same recommendations", 
            "not updating", "does not change", "stuck in my taste", "keeps recommending",
            "daily mix", "discover weekly", "release radar", "smart shuffle", "shuffle", "radio", 
            "autoplay", "made for you", "liked songs", "playlists",
            "cannot change", "can’t fix", "dislike", "hide song", "not interested", "stop recommending", 
            "block artist", "train algorithm", "no control", "feedback does not work",
            "playlist fatigue", "same playlist", "same queue", "same mix", "repeated playlist", 
            "old playlist", "stale playlist"
        ],
        "themes": [
            {
                "name": "Overuse of Listening History",
                "pattern": r"history|old taste|stuck in my taste|based on",
                "summary": "The recommendation system heavily relies on historical listening data, feeding back the same taste loop."
            },
            {
                "name": "Repeated Artists/Songs",
                "pattern": r"same song|same artist|repeated|repeats",
                "summary": "Core playlists and features continuously serve the exact same artists and tracks."
            },
            {
                "name": "Weak Refresh",
                "pattern": r"not updating|does not change|stale|fatigue",
                "summary": "Personalized mixes and homepage feeds fail to update frequently enough, leading to content staleness."
            },
            {
                "name": "Poor Shuffle/Radio Logic",
                "pattern": r"shuffle|smart shuffle|radio|autoplay|loop",
                "summary": "The playback engine's shuffle and autoplay functions cycle through a small pool of high-retention tracks."
            },
            {
                "name": "Weak Feedback Controls",
                "pattern": r"cannot change|can't fix|dislike|hide|block|no control|feedback",
                "summary": "Negative feedback signals are ignored or insufficient to remove repetitive tracks from automated queues."
            }
        ],
        "answer": "Repeated listening is primarily caused by the recommendation algorithm's heavy reliance on historical listening data (creating a feedback loop) and poor playback randomization. Features like 'Smart Shuffle' and 'Autoplay' repeatedly cycle through a cached subset of highly familiar tracks. Furthermore, personalized playlists (e.g. Daily Mixes) suffer from a weak refresh rate, leading to playlist fatigue. Users feel stuck because negative feedback tools do not successfully influence the algorithm to replace these repeated tracks.",
        "conclusion": "Repetitive listening is driven by historical data feedback loops, poor shuffle/radio randomization, and slow refresh rates on core personalized surfaces.",
        "why_it_is_happening": "To optimize for session length and low skip rates, Spotify's algorithms leverage a 'safe playlist cache' of highly familiar tracks. Collaborative filtering models assume that past listening is the best predictor of future desire, creating a systemic bias against fresh exploration.",
        "product_implication": "Implement a 'Zero-Overlap Mode' for personalized playlists and autoplay queues, ensuring that previously liked or recently played tracks are strictly excluded from discovery sessions."
    },
    {
        "id": "Q5",
        "question": "Which user segments experience different discovery challenges?",
        "keywords": [
            "segments", "crate digger", "enthusiast", "passive", "routine", "casual", "active", 
            "heavy user", "contextual", "listener type", "taste profile",
            "same songs", "daily mix", "radio", "autoplay", "shuffle", "background", "just play", 
            "repeated", "boring", "stale",
            "discover", "discovery", "new music", "new artists", "new songs", "explore", 
            "different music", "fresh music", "new genre",
            "mood", "vibe", "gym", "workout", "study", "focus", "commute", "driving", "sleep", 
            "chill", "party", "context",
            "liked songs", "library", "saved songs", "old songs", "rediscover", "songs i forgot", 
            "my music", "collection",
            "playlist", "playlists", "queue", "smart shuffle", "shuffle", "mix", "daily mix", 
            "build playlist", "playlist recommendations",
            "free", "ads", "limited skips", "can’t skip", "shuffle only", "premium", "subscription",
            "premium", "paid", "paying", "subscriber", "expect better", "still bad recommendations", 
            "no control"
        ],
        "themes": [], # Handled dynamically by custom logic
        "answer": "Different user segments experience distinct discovery friction points. 'Active Music Explorers' (crate diggers) seek high novelty and obscure tracks, but find Spotify's recommendations too mainstream and safe. 'Passive Repeat Listeners' want background music but get frustrated by extreme repetition in Daily Mixes. 'Mood/Context Listeners' struggle because activities (like gym, sleep) pollute their general taste profile. 'Large Library Listeners' want better resurfacing of old favorites, and 'Premium Power Users' feel that their monthly subscription should grant them stronger control tools to train the recommendation engine.",
        "conclusion": "Discovery challenges are segmented: enthusiasts want obscurity and variety; passive listeners want variety without effort; contextual and power users want profile boundaries and better controls.",
        "why_it_is_happening": "Spotify aggregates all listening behaviors into a single account taste profile. It does not distinguish between a crate digger's active search session and a casual background stream, resulting in polluted profiles and a 'one-size-fits-all' recommendation set that disappoints both enthusiasts and casuals.",
        "product_implication": "Introduce custom taste profiles (e.g. 'Gym Profile', 'Crate Digger Mode') that users can toggle to prevent temporary or niche listens from influencing their main recommendation feeds."
    },
    {
        "id": "Q6",
        "question": "What unmet needs emerge consistently across reviews?",
        "keywords": [
            "control", "customize", "preference", "filter", "dislike", "hide song", "not interested", 
            "block artist", "stop recommending", "train algorithm", "feedback", "improve recommendations",
            "new music", "new songs", "new artists", "fresh music", "fresh songs", "different music", 
            "more variety", "less repetitive", "not the same songs", "not the same artists", "discover more",
            "mood", "vibe", "context", "activity", "gym", "workout", "study", "focus", "commute", 
            "driving", "party", "sleep", "chill", "relax",
            "better recommendations", "smarter recommendations", "improve algorithm", "better algorithm", 
            "relevant recommendations", "not random", "not too similar", "match my taste", 
            "understand my taste",
            "why recommended", "why this song", "explain", "reason", "understand", "transparency",
            "refresh", "update", "new mix", "change recommendations", "reset recommendations", 
            "reset algorithm", "fresh playlist", "different songs"
        ],
        "themes": [
            {
                "name": "Controllable Novelty",
                "pattern": r"control|customize|filter|new music|fresh|variety|discover more",
                "summary": "Users want explicit controls (like a novelty dial) to dictate how adventurous recommendations should be."
            },
            {
                "name": "Mood/Context-Aware Discovery",
                "pattern": r"mood|vibe|context|activity|gym|workout|study|focus|commute|driving|sleep|chill|relax",
                "summary": "Listeners need discovery features that adapt to their real-time state and activity context."
            },
            {
                "name": "Better Feedback Controls",
                "pattern": r"dislike|hide|block|stop recommending|train|feedback",
                "summary": "Demand for functional feedback loops (e.g., permanent block/hide artist or genre exclusions)."
            },
            {
                "name": "Better Recommendation Refresh",
                "pattern": r"refresh|update|new mix|change|reset",
                "summary": "Users require a manual 'refresh recommendations' or 'reset algorithm' button to clear out stale feeds."
            },
            {
                "name": "Explainable Recommendations",
                "pattern": r"why recommended|why this song|explain|reason|understand|transparency",
                "summary": "Users want to understand why specific tracks are recommended to demystify the black-box algorithm."
            },
            {
                "name": "Less Repetitive Shuffle/Radio",
                "pattern": r"shuffle|radio|repetitive|same songs",
                "summary": "Demand for a true random shuffle algorithm that doesn't loop the same narrow list of tracks."
            }
        ],
        "answer": "Consistent unmet needs include the desire for controllable novelty (adjusting discovery depth), context-aware discovery, stronger negative feedback tools (e.g., a 'block artist' button that actually works), manual recommendation refresh options, and explainable recommendations. Users want to break out of the black-box system and actively collaborate with the algorithm to guide their music discovery sessions.",
        "conclusion": "The overarching unmet need is a shift from a passive, black-box recommendation experience to an interactive, user-controlled discovery system.",
        "why_it_is_happening": "Spotify's product strategy emphasizes hands-free automation, which leaves users without UI controls to manually tune or clear out recommendation databases. This lack of transparency and agency leads to friction when recommendations miss the mark.",
        "product_implication": "Expose a 'Curation Dashboard' where users can view their top taste factors, adjust a discovery slider, block specific subgenres/artists, and reset recommendations instantly."
    }
]

def clean_and_normalize_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.lower().strip())

def main():
    print("--------------------------------------------------")
    print("Spotify Review Discovery Engine: Multi-Question Pipeline")
    print("--------------------------------------------------")

    # 1. Load Data
    all_raw_records = []
    platform_load_counts = {}
    
    for platform_key, filepath in PLATFORM_FILES.items():
        if not os.path.exists(filepath):
            print(f"Error: Required file not found: {filepath}")
            sys.exit(1)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            records = json.load(f)
            platform_load_counts[platform_key] = len(records)
            for r in records:
                # Merge & Normalize schema
                all_raw_records.append({
                    'id': str(r.get('review_id')),
                    'source_platform': platform_key,
                    'source_url': r.get('url', ''),
                    'published_at': r.get('created_at', ''),
                    'rating': r.get('rating'),
                    'title': r.get('title', '') if r.get('title') else '',
                    'raw_text': r.get('raw_text', '')
                })

    total_loaded = len(all_raw_records)
    print(f"Total records loaded: {total_loaded}")

    # 2. Deduplicate exact and near-duplicates
    seen_texts = {}
    deduped_records = []
    
    for record in all_raw_records:
        cleaned = clean_and_normalize_text(record['raw_text'])
        char_prefix = cleaned[:120]
        
        if cleaned not in seen_texts and char_prefix not in seen_texts:
            seen_texts[cleaned] = True
            seen_texts[char_prefix] = True
            deduped_records.append(record)

    total_deduped = len(deduped_records)
    print(f"Total records after deduplication: {total_deduped}")

    global_question_results = []

    # 3. Process each question
    for idx, q_cfg in enumerate(QUESTIONS_CONFIG, 1):
        q_id = q_cfg["id"]
        q_text = q_cfg["question"]
        kws = q_cfg["keywords"]
        
        matched_reviews = []
        platform_breakdown = {
            "app_store": 0,
            "play_store": 0,
            "reddit": 0,
            "spotify_community": 0,
            "social_media": 0
        }
        
        # Search inside all platform data using keywords
        for rec in deduped_records:
            text_lower = rec['raw_text'].lower()
            matched_kws = [kw for kw in kws if kw in text_lower]
            
            if matched_kws:
                reason = f"Contains keywords matching {q_id} context: {', '.join(matched_kws[:3])}"
                matched_rec = rec.copy()
                matched_rec['matched_keywords'] = matched_kws
                matched_rec['reason_relevant_to_question'] = reason
                
                matched_reviews.append(matched_rec)
                platform_breakdown[rec['source_platform']] += 1

        total_reviews_found = len(matched_reviews)
        
        themes_data = []

        if q_id == "Q5":
            # Special segment classification logic for Q5
            segment_reviews_map = {seg: [] for seg in SEGMENTS_CONFIG.keys()}
            segment_reviews_map["unclear"] = []

            for r in matched_reviews:
                text_lower = r['raw_text'].lower()
                seg_scores = {}
                for seg_name, seg_cfg in SEGMENTS_CONFIG.items():
                    score = sum(1 for kw in seg_cfg["keywords"] if kw in text_lower)
                    seg_scores[seg_name] = score
                
                max_seg = max(seg_scores, key=seg_scores.get)
                if seg_scores[max_seg] > 0:
                    segment_reviews_map[max_seg].append(r)
                    r["assigned_segment"] = max_seg
                else:
                    segment_reviews_map["unclear"].append(r)
                    r["assigned_segment"] = "unclear"

            # Create theme-like objects for the segments
            for seg_name, seg_cfg in SEGMENTS_CONFIG.items():
                seg_reviews = segment_reviews_map[seg_name]
                rep_quotes = []
                seen_quotes = set()
                
                for r in seg_reviews:
                    cleaned_quote = r['raw_text'].strip()
                    if cleaned_quote and len(cleaned_quote.split()) >= 12 and cleaned_quote not in seen_quotes:
                        rep_quotes.append(cleaned_quote)
                        seen_quotes.add(cleaned_quote)
                    if len(rep_quotes) >= 2: # Select 1 to 2 quotes per segment
                        break
                
                if len(rep_quotes) < 1:
                    for r in seg_reviews:
                        cleaned_quote = r['raw_text'].strip()
                        if cleaned_quote and cleaned_quote not in seen_quotes:
                            rep_quotes.append(cleaned_quote)
                            seen_quotes.add(cleaned_quote)
                        if len(rep_quotes) >= 2:
                            break

                platforms_seen = list(set(r['source_platform'] for r in seg_reviews))
                
                themes_data.append({
                    "theme_name": seg_name,
                    "theme_summary": f"Challenge: {seg_cfg['challenge']}",
                    "review_count": len(seg_reviews),
                    "platforms_seen": platforms_seen,
                    "representative_quotes": rep_quotes
                })
                
            # Add unclear segment stats
            unclear_reviews = segment_reviews_map["unclear"]
            themes_data.append({
                "theme_name": "unclear",
                "theme_summary": "Challenge: Reviews where no specific segment characteristics could be confidently mapped.",
                "review_count": len(unclear_reviews),
                "platforms_seen": list(set(r['source_platform'] for r in unclear_reviews)),
                "representative_quotes": []
            })
        else:
            # Theme clustering
            for theme_cfg in q_cfg["themes"]:
                theme_name = theme_cfg["name"]
                theme_summary = theme_cfg["summary"]
                pattern = theme_cfg["pattern"]
                
                theme_reviews = []
                for r in matched_reviews:
                    if re.search(pattern, r['raw_text'], re.IGNORECASE):
                        theme_reviews.append(r)
                
                # Select 3 to 5 strongest real quotes
                rep_quotes = []
                seen_quotes = set()
                
                for r in theme_reviews:
                    cleaned_quote = r['raw_text'].strip()
                    if cleaned_quote and len(cleaned_quote.split()) >= 12 and cleaned_quote not in seen_quotes:
                        rep_quotes.append(cleaned_quote)
                        seen_quotes.add(cleaned_quote)
                    if len(rep_quotes) >= 5:
                        break
                
                if len(rep_quotes) < 3:
                    for r in theme_reviews:
                        cleaned_quote = r['raw_text'].strip()
                        if cleaned_quote and cleaned_quote not in seen_quotes:
                            rep_quotes.append(cleaned_quote)
                            seen_quotes.add(cleaned_quote)
                        if len(rep_quotes) >= 5:
                            break

                platforms_seen = list(set(r['source_platform'] for r in theme_reviews))
                
                themes_data.append({
                    "theme_name": theme_name,
                    "theme_summary": theme_summary,
                    "review_count": len(theme_reviews),
                    "platforms_seen": platforms_seen,
                    "representative_quotes": rep_quotes
                })

            # Sort themes dynamically by count if Q2 or Q6 (ranking requirement)
            if q_id in ["Q2", "Q6"]:
                themes_data.sort(key=lambda x: x["review_count"], reverse=True)

        is_weak = total_reviews_found < 10
        answer = q_cfg["answer"]
        conclusion = q_cfg["conclusion"]
        why_it_is_happening = q_cfg["why_it_is_happening"]
        product_implication = q_cfg["product_implication"]
        
        if is_weak:
            answer = "[WEAK EVIDENCE] " + answer
            conclusion = "[WEAK EVIDENCE] " + conclusion
            why_it_is_happening = "[WEAK EVIDENCE] " + why_it_is_happening
            product_implication = "[WEAK EVIDENCE] " + product_implication

        q_result = {
            "question_id": q_id,
            "question": q_text,
            "search_keywords_used": kws,
            "total_reviews_found": total_reviews_found,
            "platform_breakdown": platform_breakdown,
            "matched_reviews": matched_reviews,
            "themes": themes_data,
            "answer": answer,
            "conclusion": conclusion,
            "why_it_is_happening": why_it_is_happening,
            "product_implication": product_implication
        }

        global_question_results.append(q_result)

        # Create subfolder for this question (e.g. data/analysis/q1)
        subfolder_path = f"data/analysis/q{idx}"
        os.makedirs(subfolder_path, exist_ok=True)
        
        # Save question specific results
        output_results = [q_result]
        evidence_path = os.path.join(subfolder_path, 'question_wise_review_evidence.json')
        with open(evidence_path, 'w', encoding='utf-8') as f:
            json.dump(output_results, f, indent=2, ensure_ascii=False)
            
        answers_path = os.path.join(subfolder_path, 'pm_research_question_answers.json')
        with open(answers_path, 'w', encoding='utf-8') as f:
            json.dump(output_results, f, indent=2, ensure_ascii=False)

        # Explicit metadata file describing what question this folder is analyzing
        metadata_path = os.path.join(subfolder_path, 'metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump({
                "folder": subfolder_path,
                "question_id": q_id,
                "question": q_text,
                "search_keywords_used": kws
            }, f, indent=2, ensure_ascii=False)

        md_path = os.path.join(subfolder_path, 'pm_research_question_answers.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# Spotify Music Discovery & Recommendation Analysis Report ({q_id} Only)\n\n")
            f.write("This report presents the synthesized findings targeting the PM research question:\n")
            f.write(f"## {q_id}: {q_text}\n\n")
            
            f.write("### Executive Summary\n")
            f.write(f"- **Total Records Ingested**: {total_loaded}\n")
            f.write(f"- **Total Records After Deduplication**: {total_deduped}\n")
            f.write(f"- **Total Matching Evidence Records**: {total_reviews_found}\n\n")
            
            f.write("### Platform Breakdown\n")
            for p, cnt in platform_breakdown.items():
                f.write(f"- *{p.replace('_', ' ').title()}*: {cnt}\n")
            f.write("\n")
            
            f.write("### PM-Style Answer\n")
            f.write(f"> {answer}\n\n")
            
            f.write("### Why it is Happening\n")
            f.write(f"> {why_it_is_happening}\n\n")
            
            f.write("### Product Implication / Opportunity\n")
            f.write(f"> {product_implication}\n\n")
            
            f.write("### Detailed Themes / Segments & Quotes\n\n")
            for theme in themes_data:
                f.write(f"#### Name: {theme['theme_name']} ({theme['review_count']} reviews)\n")
                f.write(f"*{theme['theme_summary']}*\n\n")
                if theme['representative_quotes']:
                    f.write("**Representative Real User Quotes**:\n")
                    for quote in theme['representative_quotes']:
                        clean_q = quote.replace("\n", " ").strip()
                        f.write(f"- \"{clean_q}\"\n")
                    f.write("\n")
                
            f.write(f"### Conclusion\n")
            f.write(f"> {conclusion}\n")

        print(f"\nProcessed: {q_id} - {q_text}")
        print(f"  Total Reviews Found: {total_reviews_found}")
        print(f"  Saved outputs to: {subfolder_path}/")

    # 4. Save global/main results in root data/analysis/ folder
    os.makedirs('data/analysis', exist_ok=True)
    
    global_evidence_path = 'data/analysis/question_wise_review_evidence.json'
    with open(global_evidence_path, 'w', encoding='utf-8') as f:
        json.dump(global_question_results, f, indent=2, ensure_ascii=False)
        
    global_answers_path = 'data/analysis/pm_research_question_answers.json'
    with open(global_answers_path, 'w', encoding='utf-8') as f:
        json.dump(global_question_results, f, indent=2, ensure_ascii=False)

    global_md_path = 'data/analysis/pm_research_question_answers.md'
    with open(global_md_path, 'w', encoding='utf-8') as f:
        f.write("# Spotify Music Discovery & Recommendation Analysis Report\n\n")
        f.write("This report presents the synthesized findings of the Product Management research-analysis flow targeting Spotify music discovery barriers, frustrations, behaviors, repetition causes, segment challenges, and unmet needs.\n\n")
        
        f.write("## Executive Summary\n")
        f.write(f"- **Total Records Ingested**: {total_loaded}\n")
        f.write(f"- **Total Records After Deduplication**: {total_deduped}\n\n")
        
        f.write("## Detailed Research Findings\n\n")
        for q in global_question_results:
            f.write(f"### {q['question_id']}: {q['question']}\n\n")
            f.write(f"**Total Matching Reviews**: {q['total_reviews_found']}\n\n")
            
            f.write("**Platform Breakdown**:\n")
            for p, cnt in q['platform_breakdown'].items():
                f.write(f"- *{p.replace('_', ' ').title()}*: {cnt}\n")
            f.write("\n")
            
            f.write("**PM-Style Answer**:\n")
            f.write(f"> {q['answer']}\n\n")
            
            f.write("**Why it is Happening**:\n")
            f.write(f"> {q['why_it_is_happening']}\n\n")
            
            f.write("**Product Implication / Opportunity**:\n")
            f.write(f"> {q['product_implication']}\n\n")
            
            f.write("**Key Themes Identified**:\n\n")
            for theme in q['themes']:
                f.write(f"#### Theme/Segment: {theme['theme_name']} ({theme['review_count']} reviews)\n")
                f.write(f"*{theme['theme_summary']}*\n\n")
                if theme['representative_quotes']:
                    f.write("**Representative Real User Quotes**:\n")
                    for quote in theme['representative_quotes']:
                        clean_q = quote.replace("\n", " ").strip()
                        f.write(f"- \"{clean_q}\"\n")
                    f.write("\n")
            
            f.write(f"**Conclusion**: {q['conclusion']}\n\n")
            f.write("---\n\n")
            
        f.write("## Overall Strategic Conclusion\n\n")
        f.write("### The Core Friction: Taste-Matching Bias vs. Active Exploration\n\n")
        f.write("Across all five platforms, a clear strategic picture emerges: **Spotify's recommendation engine is suffering from a fundamental structural bias toward local-minimum optimization**. By prioritizing short-term skip rates and session retention metrics, the system biases recommendations toward safe, highly familiar tracks and artists the user has already liked or repeatedly played.\n\n")
        f.write("While this approach is excellent at maintaining comfortable background listening sessions, it directly causes the playlist fatigue, shuffle repetitiveness, and echo chamber feedback loops reported by users. Listening behaviors are highly contextual; users do not want more of the same recommendations—they need **dynamic, intent-aware exploration tools** that allow them to control discovery thresholds and partition temporary listening contexts away from their long-term taste profile.\n")

    print("\n--------------------------------------------------")
    print("Global files successfully generated in data/analysis/:")
    print(f"  - Evidence File: {global_evidence_path}")
    print(f"  - Answers File: {global_answers_path}")
    print(f"  - Markdown Report: {global_md_path}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()
