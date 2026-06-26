I am building of a Product Management fellowship project for Spotify.

Project name:
Spotify Review Discovery Engine

First, understand the product problem:
I am acting as a Product Manager on Spotify’s Growth Team. Spotify has millions of users and a strong recommendation system, but many users still listen repeatedly to the same playlists, familiar artists, and already-discovered songs. Spotify’s strategic goal is to increase meaningful music discovery and reduce repetitive listening behavior.

Before proposing any solution, I need to build an AI-powered review discovery engine. This system should analyze public user feedback at scale from sources such as App Store reviews, Play Store reviews, Reddit discussions, Spotify Community posts, and social media conversations.

The goal is to analyze:

App Store reviews
Play Store reviews
Reddit discussions
Community forums
Social media conversations

The goal of this engine is to answer:

Why do users struggle to discover new music?
What are the most common frustrations with Spotify recommendations?
What listening behaviors are users trying to achieve?
What causes users to repeatedly listen to the same content?
Which user segments experience different discovery challenges?
What unmet needs emerge consistently across reviews?

Important product hypothesis:
Spotify is strong at taste matching, but weaker at intent-aware exploration. Users do not simply want more recommendations. They want fresher music that fits their current mood, activity, context, and desired level of novelty.

## Review Scraping Rules

These rules define the criteria for scraping reviews. Only keep a review/comment if it is relevant to Spotify music discovery, recommendations, repeated listening, playlists, shuffle, radio, mood/context, or user control.

### Inclusion Keyword Groups

#### Recommendation Keywords:
- recommendation
- recommendations
- recommended
- recommend
- suggested
- suggestions
- algorithm
- algorithmic
- personalization
- personalized
- for you

#### Repetition Keywords:
- same songs
- same song
- same artists
- same artist
- same genre
- repeated
- repetitive
- repeats
- repeating
- over and over
- again and again
- loop
- stuck
- stale
- boring
- not fresh
- always the same

#### Discovery Keywords:
- discover
- discovery
- discovering
- new music
- new songs
- new artists
- find music
- finding music
- find songs
- explore
- exploration
- fresh music
- fresh songs
- different music

#### Spotify Feature Keywords:
- Discover Weekly
- Daily Mix
- Release Radar
- Smart Shuffle
- Radio
- Song Radio
- Artist Radio
- Autoplay
- DJ
- AI Playlist
- Taste Profile
- Blend
- Made For You
- Liked Songs
- Playlists
- Shuffle

#### Mood/Context/Intent Keywords:
- mood
- vibe
- activity
- context
- gym
- workout
- study
- focus
- commute
- driving
- party
- sleep
- chill
- relax
- sad
- happy
- late night
- background music

#### Feedback/Control Keywords:
- dislike
- hide song
- hide this song
- not interested
- block artist
- remove recommendation
- stop recommending
- train algorithm
- feedback
- control
- customize
- filter
- preference
- improve recommendations

#### Playlist Fatigue Keywords:
- playlist fatigue
- playlist
- playlists
- mix
- mixes
- queue
- library
- liked songs
- shuffle
- smart shuffle
- daily mix

#### Recommendation Quality Keywords:
- bad recommendations
- poor recommendations
- terrible recommendations
- irrelevant
- unrelated
- random
- too random
- too similar
- too safe
- not my taste
- doesn’t match my taste
- wrong songs
- bad algorithm

#### Off-Platform Discovery Workaround Keywords:
- Reddit
- Instagram
- TikTok
- YouTube
- Shazam
- friends
- outside Spotify
- other apps
- Apple Music
- SoundCloud
- Last.fm

### Exclusion Rules
Reject and do not store a record if:
- Text has fewer than 10 words.
- Text contains only emojis.
- Text is only generic praise with no explanation (e.g., "Good app", "Best app", "Nice", "Love Spotify", "5 stars", "Very good").
- Text is only about price/subscription and does not mention discovery, recommendations, repeated songs, playlists, shuffle, radio, or algorithm.
- Text is only about ads and does not mention discovery, recommendations, repeated songs, playlists, shuffle, radio, or algorithm.
- Text is only about login, account, or payment issues.
- Text is only about crashes, bugs, download issues, or offline playback.
- Text is only about lyrics.
- Text is only about podcasts or audiobooks.
- Text is only about UI design and does not mention discovery/recommendations.
- Text is spam, promotional, duplicate, or meaningless.
- Text is not related to music discovery, recommendations, repeated listening, playlists, shuffle, radio, algorithm, mood/context, or user control.

### Important Exception
If a review mentions ads, price, bugs, UI, login, lyrics, podcasts, or downloads but also mentions recommendations, discovery, repeated songs, playlists, shuffle, radio, algorithm, mood/context, or user control, keep it.

**Examples:**
- *Keep:* “Too many ads, but my bigger issue is that Discover Weekly keeps giving me the same songs every week.”
- *Reject:* “Too many ads. I hate this app.”

Build a functional web app called Spotify Review Discovery Engine.

