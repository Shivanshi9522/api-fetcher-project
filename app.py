import streamlit as st
import pandas as pd
from api_fetcher import APIFetcher

st.title("Smart API Data Fetcher 🌙")
api_url = st.text_input("Enter API URL", "https://api.github.com/users/shivanshi/repos")
endpoint = st.text_input("Endpoint (optional)", "")

if st.button("Fetch Data"):
    with st.spinner("Fetching..."):
        fetcher = APIFetcher(api_url)
        data = fetcher.fetch_with_retry(endpoint)

        if data:
            df = pd.json_normalize(data)
            keep = ['name', 'description', 'language', 'stargazers_count', 'forks_count', 'html_url', 'created_at']
            df = df[[c for c in keep if c in df.columns]]
            st.success(f"Fetched {len(df)} rows!")
            st.dataframe(df.head())
            if 'language' in df.columns:
             st.bar_chart(df['language'].value_counts())

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, "data.csv", "text/csv")

            # Auto chart if numeric columns exist
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            if len(numeric_cols) >= 1:
                st.bar_chart(df[numeric_cols[0]])
        else:
            st.error("Failed to fetch data. Check URL or logs.")