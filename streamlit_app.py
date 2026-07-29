import os
import streamlit as st
from google import genai
from google.genai import types

# 1. Page Configuration
st.set_page_config(page_title="Gemma 4 AI Engine", page_icon="⚡", layout="wide")

st.title("⚡ Gemma 4 AI Assistant")
st.caption("Powered by Google AI Studio & Gemma 4 26B")

# 2. Securely retrieve API Key from Streamlit Secrets or Environment Variables
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ API Key missing! Please add `GEMINI_API_KEY` to your Streamlit Secrets.")
    st.stop()

# Initialize the GenAI Client
client = genai.Client(api_key=api_key)

# 3. User Input UI
user_input = st.text_area(
    "Enter your prompt / log / question here:",
    placeholder="Type something for Gemma 4 to analyze...",
    height=150
)

# 4. Generate Button & Streaming Logic
if st.button("🚀 Run Gemma 4", type="primary"):
    if not user_input.strip():
        st.warning("Please enter some text before submitting!")
    else:
        st.subheader("Gemma 4 Output:")
        
        try:
            # Build request payload
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=user_input),
                    ],
                ),
            ]

            tools = [
                types.Tool(googleSearch=types.GoogleSearch()),
            ]

            generate_content_config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_level="HIGH",
                ),
                tools=tools,
            )

            # Generator function to stream text chunk by chunk to Streamlit
            def generate_stream():
                response_stream = client.models.generate_content_stream(
                    model="gemma-4-26b-a4b-it",
                    contents=contents,
                    config=generate_content_config,
                )
                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text

            # Stream the text live to the browser screen!
            st.write_stream(generate_stream)

        except Exception as e:
            st.error(f"An error occurred while calling Gemma 4: {e}")
