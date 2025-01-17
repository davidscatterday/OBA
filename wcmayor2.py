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
    # Remove "new york city"
    text = text.replace("new york city", "")
    # Remove "new york city"
    text = text.replace("nyc", "")
    # Remove "new york city"
    text = text.replace("new york", "")
    # Remove "new york city"
    text = text.replace("mayor", "")
    # Remove "new york city"
    text = text.replace("city", "")
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
    "https://www.bxtimes.com/week-in-rewind-may-17/",
    "https://anhd.org/report/new-era-nyc-affordable-housing-policy-analyzing-mayors-housing-plan",
    "https://www.nyc.gov/office-of-the-mayor/news/816-24/mayor-adams-lawsuit-against-major-online-distributor-illegally-selling-disposable",
    "https://www.nyc.gov/office-of-the-mayor/news/814-24/mayor-adams-on-likely-overwhelming-passage-propositions-1-2-3-4-5",
    "https://www.nyc.gov/office-of-the-mayor/news/684-003/emergency-executive-order-684",
    "https://www.nyc.gov/office-of-the-mayor/news/795-24/mayor-adams-how-nyc-moves-new-data-driven-plan-streamline-developing-major",
    "https://www.nyc.gov/site/housing/index.page#:~:text=The%20plan%20included%20strategies%20to,to%20the%20State's%20rent%20stabilization"
]

# Fetch and display raw content
raw_content = fetch_webpage_content(urls)


# Preprocess text
processed_text = preprocess_text(raw_content)

# Generate and display word cloud
st.subheader("Word Cloud")
fig = generate_wordcloud(processed_text)
st.pyplot(fig)

# Provide a non-empty label for the text area
st.text_area("Raw Webpage Content", raw_content[:1000] + "...", height=200)  # Display first 1000 characters

# Display scraped URLs
st.subheader("Scraped URLs")
for url in urls:
    st.write(url)

# Display most common words
st.subheader("Most Common Words")
word_freq = nltk.FreqDist(processed_text.split())
common_words = word_freq.most_common(10)
for word, freq in common_words:
    st.write(f"{word}: {freq}")

