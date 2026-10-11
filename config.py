import os

import streamlit as st
from dotenv import load_dotenv
from google import genai


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("GEMINI_API_KEY not found in .env file.")
    st.stop()

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.5-flash-lite"