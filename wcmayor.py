import streamlit as st
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import nltk
from nltk.corpus import stopwords
import re

# Download stopwords
nltk.download('stopwords')

# Streamlit app
st.title("NYC Mayor's Office News Word Cloud")

# Function to fetch and parse webpage content
@st.cache_data
def fetch_webpage_content(urls):
    all_text = ""
    for url in urls:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        all_text += soup.get_text() + " "
    return all_text

# Function to preprocess text
def preprocess_text(text):
    # Remove special characters and digits
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # Convert to lowercase
    text = text.lower()
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    words = text.split()
    words = [word for word in words if word not in stop_words]
    return ' '.join(words)

# Function to generate word cloud
def generate_wordcloud(text):
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    return fig

# Main app
urls = [
    "https://www.nyc.gov/office-of-the-mayor/news/816-24/mayor-adams-lawsuit-against-major-online-distributor-illegally-selling-disposable",
    "https://www.nyc.gov/office-of-the-mayor/news/814-24/mayor-adams-on-likely-overwhelming-passage-propositions-1-2-3-4-5",
    "https://www.nyc.gov/office-of-the-mayor/news/684-003/emergency-executive-order-684",
    "https://www.nyc.gov/office-of-the-mayor/news/810-24/mayor-adams-signs-legislation-protect-hotel-workers-guests-strengthen-tourism-industry#/0",
    "https://www.nyc.gov/office-of-the-mayor/news/805-24/transcript-mayor-adams-urges-new-yorkers-call-911-combat-subway-surfing-highlights"
]

# Fetch and display raw content
raw_content = fetch_webpage_content(urls)
st.subheader("Raw Content")
st.text_area("", raw_content[:20000] + "...", height=200)  # Display first 1000 characters

# Preprocess text
processed_text = preprocess_text(raw_content)

# Generate and display word cloud
st.subheader("Word Cloud")
fig = generate_wordcloud(processed_text)
st.pyplot(fig)

# Display most common words
st.subheader("Most Common Words")
word_freq = nltk.FreqDist(processed_text.split())
common_words = word_freq.most_common(10)
for word, freq in common_words:
    st.write(f"{word}: {freq}")

# Display scraped URLs
st.subheader("Scraped URLs")
for url in urls:
    st.write(url)