import streamlit as st
from fuzzywuzzy import fuzz
import plotly.graph_objects as go

def get_color(value):
    if 0 <= value <= 33:
        return "red"
    elif 34 <= value <= 66:
        return "yellow"
    else:
        return "green"

def create_gauge(value, title):
    color = get_color(value)
    return go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 14}},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 33], 'color': "lightgray"},
                {'range': [33, 66], 'color': "lightgray"},
                {'range': [66, 100], 'color': "lightgray"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))

def main():
    st.title("Fuzzy Text Matching")

    text1 = st.text_area("Enter Text 1")
    text2 = st.text_area("Enter Text 2")

    if st.button("Compare"):
        if text1 and text2:
            ratio = fuzz.ratio(text1, text2)
            partial_ratio = fuzz.partial_ratio(text1, text2)
            token_sort_ratio = fuzz.token_sort_ratio(text1, text2)
            token_set_ratio = fuzz.token_set_ratio(text1, text2)

            # Create and display gauges in two rows
            row1_col1, row1_col2 = st.columns(2)
            row2_col1, row2_col2 = st.columns(2)

            with row1_col1:
                fig1 = create_gauge(ratio, "Ratio")
                st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

            with row1_col2:
                fig2 = create_gauge(partial_ratio, "Partial Ratio")
                st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

            with row2_col1:
                fig3 = create_gauge(token_sort_ratio, "Token Sort Ratio")
                st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

            with row2_col2:
                fig4 = create_gauge(token_set_ratio, "Token Set Ratio")
                st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})

        else:
            st.warning("Please enter both text snippets.")

if __name__ == "__main__":
    main()



