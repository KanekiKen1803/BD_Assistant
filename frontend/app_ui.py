import streamlit as st
import requests
import json

url = "http://127.0.0.1:5000/query"


headers = {
  'Content-Type': 'application/json'
}

st.set_page_config(page_title="ChatBot", page_icon="https://cdn3.iconfinder.com/data/icons/artificial-intelligence-1-2-1/1024/Artificial_intelligence-10-1024.png")

st.title("Accordion Hackathon")

user_query = st.text_area("What would you like to know?")
if st.button('Submit'):
    with st.spinner("Retrieving information"):
        payload = json.dumps({
            "query": user_query
        })
        response = requests.request("POST", url, headers=headers, data=payload, timeout=30)
        result = response.json()["result"].strip(" ")
        st.text_area(label="Result", value=result, height=100)