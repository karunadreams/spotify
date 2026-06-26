# Spotify Review Discovery Engine

An interactive, Spotify-themed PM insights dashboard and review discovery pipeline that processes raw user feedback from 5 sources, clusters insights into product themes, and synthesizes answers for product management research questions.

## 🎵 Features

- **Multi-source Scraper**: Pipelines to gather reviews and feedback from App Store, Play Store, Reddit, Spotify Community forums, and Twitter/Social media.
- **Theme Clustering & Quote Extraction**: Groups feedback and extracts representative real quotes directly matching target research questions.
- **PM Synthesis Block**: Formulates PM-style Answers, "Why it is Happening", and Product Implications.
- **Interactive Dashboard**: A Spotify dark-themed Streamlit app to explore PM questions, metrics, platform distributions, and raw review details.

---

## 🚀 Setup & Execution

### 1. Prerequisites
Make sure you have Python 3.8+ installed.

### 2. Installation
Clone the repository and install the dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` and fill in your API tokens:
```bash
cp .env.example .env
```
*   **APIFY_API_TOKEN**: Needed if running scrapers that require Apify integration.
*   **groq_api**: Needed if running synthesis scripts.

### 4. Running the Dashboard
Launch the Streamlit dashboard locally:
```bash
python -m streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📂 Project Structure

- `app.py`: Streamlit frontend application.
- `architecture.md`: Detailed documentation of system architecture.
- `data/`: Contains raw JSON reviews and synthesized PM question data under `data/analysis/`.
- `requirements.txt`: Python package dependencies.
- `scrape_*.py`: Individual platform scraper scripts.
