import streamlit as st
import feedparser
import sqlite3
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# ---------------- CONFIG ----------------
st.set_page_config(page_title="🌍 Multilingual News Hub", layout="wide")

# ---------------- CUSTOM UI ----------------
st.markdown("""
<style>
body {
    background-color: #0E1117;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* News Channel Ticker */
.ticker {
    background-color: #E50914;
    color: white;
    padding: 10px;
    font-weight: bold;
    overflow: hidden;
    white-space: nowrap;
    margin-bottom: 20px;
}
.ticker span {
    display: inline-block;
    padding-right: 50px;
    animation: ticker 15s linear infinite;
}
@keyframes ticker {
    0% { transform: translateX(100%); }
    100% { transform: translateX(-100%); }
}

/* Main Title */
h1 {
    color: #FFD700;
    font-weight: 700;
    text-transform: uppercase;
    border-bottom: 3px solid #FFD700;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

/* News cards */
.card {
    padding: 20px;
    border-radius: 12px;
    background-color: #1c1f26;
    margin-bottom: 25px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.4);
    transition: transform 0.2s ease-in-out;
}
.card:hover {
    transform: scale(1.01);
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #1c1f26;
    padding: 20px;
    border-right: 2px solid #E50914;
}
[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    color: #FFD700;
    font-weight: bold;
    text-transform: uppercase;
    margin-bottom: 15px;
}
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
    background-color: #0E1117;
    color: white;
    border-radius: 8px;
    border: 1px solid #FFD700;
    padding: 5px;
}
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"]:hover {
    border-color: #E50914;
}
[data-testid="stSidebar"] p {
    color: #ccc;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("""
<div class="ticker">
    <span>📢 Live News in Hindi • Telugu • Urdu • English</span>
</div>
""", unsafe_allow_html=True)

st.title("🌍 Multilingual News Hub")

# ---------------- DATABASE ----------------
conn = sqlite3.connect('news.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title_en TEXT,
    title_hi TEXT,
    title_te TEXT,
    title_ur TEXT,
    source TEXT,
    url TEXT UNIQUE
)
''')
conn.commit()

# ---------------- FUNCTIONS ----------------
def fetch_news_rss():
    feeds = [
        "https://globalvoices.org/feed/",
        "https://www.voanews.com/rss",
        "https://news.un.org/feed/subscribe/en/news/all/rss.xml"
    ]
    articles = []
    for feed in feeds:
        parsed = feedparser.parse(feed)
        for entry in parsed.entries[:5]:
            articles.append({
                "title": entry.title,
                "summary": getattr(entry, "summary", ""),
                "link": entry.link,
                "source": parsed.feed.get("title", "Unknown Source")
            })
    return articles

def fetch_full_article(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = [p.get_text().strip() for p in soup.find_all("p")]

        blacklist = ["donation", "subscribe", "privacy policy", "newsletter",
                     "authors", "email", "website", "powered by", "support"]
        clean_paragraphs = [
            p for p in paragraphs
            if p and not any(bad.lower() in p.lower() for bad in blacklist)
        ]
        return "\n".join(clean_paragraphs).strip()
    except Exception:
        return ""

@st.cache_data
def translate_all(text):
    try:
        hi = GoogleTranslator(source='auto', target='hi').translate(text)
        te = GoogleTranslator(source='auto', target='te').translate(text)
        ur = GoogleTranslator(source='auto', target='ur').translate(text)
    except Exception:
        return None, None, None
    return hi, te, ur

def save_news(en, hi, te, ur, source, url):
    try:
        c.execute(
            "INSERT INTO news (title_en, title_hi, title_te, title_ur, source, url) VALUES (?, ?, ?, ?, ?, ?)",
            (en, hi, te, ur, source, url)
        )
        conn.commit()
    except:
        st.warning("Already saved!")

def delete_news(news_id):
    c.execute("DELETE FROM news WHERE id=?", (news_id,))
    conn.commit()

# ---------------- UI ----------------
page = st.sidebar.selectbox("Select Page", ["Live News", "Saved News"])
language = st.sidebar.selectbox("Select Language", ["English", "Hindi", "Telugu", "Urdu"])

# Saved Articles Counter
c.execute("SELECT COUNT(*) FROM news")
count = c.fetchone()[0]
st.sidebar.markdown(f"<p style='color:#FFD700;font-weight:bold;'>📊 Saved Articles: {count}</p>", unsafe_allow_html=True)

if page == "Live News":
    st.subheader("🗞️ Latest Global Headlines")
    articles = fetch_news_rss()

    for i, article in enumerate(articles):
        title = article["title"]
        source = article["source"]
        link = article["link"]

        full_text = fetch_full_article(link) or article["summary"]

        hi_title, te_title, ur_title = translate_all(title)
        hi_text, te_text, ur_text = translate_all(full_text)

        # Skip if translation failed
        if not all([hi_title, te_title, ur_title, hi_text, te_text, ur_text]):
            continue

        st.markdown("<div class='card'>", unsafe_allow_html=True)

        if language == "English":
            st.subheader(title)
            st.write(full_text)
        elif language == "Hindi":
            st.subheader(hi_title)
            st.write(hi_text)
        elif language == "Telugu":
            st.subheader(te_title)
            st.write(te_text)
        elif language == "Urdu":
            st.markdown(f"<p style='direction: rtl; text-align: right;'>{ur_title}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='direction: rtl; text-align: right;'>{ur_text}</p>", unsafe_allow_html=True)

        st.write("**Source:**", source)
        if st.button("💾 Save", key=f"{link}_{i}"):
            save_news(title, hi_title, te_title, ur_title, source, link)
            st.success("Saved Successfully!")

        st.markdown("</div>", unsafe_allow_html=True)

elif page == "Saved News":
    st.subheader("📂 Saved Articles")
    c.execute("SELECT * FROM news")
    rows = c.fetchall()

    for row in rows:
        st.markdown("<div class='card'>", unsafe_allow_html=True)

        if language == "English":
            st.subheader(row[1])
        elif language == "Hindi":
            st.subheader(row[2])
        elif language == "Telugu":
            st.subheader(row[3])
        elif language == "Urdu":
            st.markdown(f"<p style='direction: rtl; text-align: right;'>{row[4]}</p>", unsafe_allow_html=True)

        st.write("**Source:**", row[5])

        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("🗑️ Unsave", key=f"del_{row[0]}"):
                delete_news(row[0])
                st.success("Article removed!")
        with col2:
            st.write(f"🔗 [Read Original]({row[6]})")

        st.markdown("</div>", unsafe_allow_html=True)
