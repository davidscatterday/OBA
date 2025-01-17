from wordcloud import WordCloud
import matplotlib.pyplot as plt
import streamlit as st

# Create some sample text
text = 'Fun, david, david, david, david, fun, awesome, awesome, tubular, astounding, superb, great, amazing, amazing, amazing, amazing'

# Create and generate a word cloud image:
wordcloud = WordCloud().generate(text)

# Create a new figure
fig, ax = plt.subplots()

# Display the generated image:
ax.imshow(wordcloud, interpolation='bilinear')
ax.axis("off")

# Use Streamlit to display the plot
st.pyplot(fig)
