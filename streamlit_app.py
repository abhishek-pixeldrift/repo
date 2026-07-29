import os
import json
import streamlit as st
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. PAGE SETUP
# ----------------------------------------------------
st.set_page_config(page_title="PrivaGuard | Data Leak Shield", page_icon="🛡️", layout="wide")

st.title("🛡️ PrivaGuard: Edge Privacy Shield")
st.caption("Powered by Google AI Studio & Gemma 4 26B")

# Securely retrieve API Key
raw_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not raw_key:
    st.error("⚠️ API Key missing! Please add `GEMINI_API_KEY` to your Streamlit Secrets.")
    st.stop()

# THE FIX: Strip out any hidden line breaks, spaces, or formatting from the copy-paste
api_key = raw_key.strip().replace("\n", "").replace("\r", "").replace(" ", "")

# Initialize the GenAI Client
client = genai.Client(api_key=api_key)

# ----------------------------------------------------
# 2. SYSTEM PROMPT (THE AI BRAIN)
# ----------------------------------------------------
privacy_system_instruction = """
You are PrivaGuard, an enterprise Privacy Engineering AI powered by Gemma 4.
Your job is to inspect incoming text, customer feedback, medical records, or user forms for sensitive PII (Personally Identifiable Information) and privacy compliance risks.

CRITICAL INSTRUCTION: You must strictly output ONLY valid JSON matching the schema below. Do not include introductory text, markdown formatting, or commentary outside the JSON object.

JSON Schema:
{
  "privacy_risk_level": "HIGH" | "MEDIUM" | "LOW",
  "risk_score": 90,
  "detected_pii": [
    {"type": "Email", "value": "detected email"}
  ],
  "redacted_text": "The full user input with all sensitive PII replaced by tags like [REDACTED_EMAIL].",
  "compliance_warnings": [
    "GDPR Risk: Processing unencrypted email"
  ],
  "action_recommendation": "1-sentence immediate fix for the developer."
}
"""

# ----------------------------------------------------
# 3. WEB UI (USER INPUT)
# ----------------------------------------------------
user_input = st.text_area(
    "Paste user feedback, medical notes, or logs to scan for PII:",
    placeholder="e.g., Hi, my name is Rahul Sharma. Please update my bank account. My email is rahul.sharma99@gmail.com and my phone number is +91 98765 43210...",
    height=150
)

# ----------------------------------------------------
# 4. API CALL & DASHBOARD RENDERING
# ----------------------------------------------------
if st.button("🔍 Scan for Privacy Leaks", type="primary"):
    if not user_input.strip():
        st.warning("Please enter some text before scanning!")
    else:
        with st.spinner("Gemma 4 is analyzing for PII and compliance risks..."):
            try:
                # Build request payload
                contents = [
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=user_input)],
                    ),
                ]

                # Inject System Prompt & enforce low temperature for strict JSON
                generate_content_config = types.GenerateContentConfig(
                    system_instruction=privacy_system_instruction,
                    temperature=0.2, 
                )

                # Fetch response from Gemma
                response = client.models.generate_content(
                    model="gemma-4-26b-a4b-it",
                    contents=contents,
                    config=generate_content_config,
                )

                # Clean the response to ensure it's valid JSON
                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                
                # Convert the text into a Python Dictionary
                data = json.loads(clean_text)

                # --- 🎨 BUILD THE BEAUTIFUL UI DASHBOARD ---
                st.divider()
                st.subheader("📊 Privacy Audit Results")

                # Alert Banner
                risk_level = data.get("privacy_risk_level", "LOW")
                if risk_level == "HIGH":
                    st.error("🚨 **CRITICAL PRIVACY LEAK DETECTED**")
                elif risk_level == "MEDIUM":
                    st.warning("⚠️ **POTENTIAL PRIVACY RISK**")
                else:
                    st.success("✅ **NO MAJOR PII DETECTED**")

                # Metrics Row
                col1, col2 = st.columns(2)
                col1.metric("Risk Score", f"{data.get('risk_score', 0)} / 100")
                col2.metric("Threat Level", risk_level)

                # Split layout for details
                col3, col4 = st.columns(2)
                
                with col3:
                    st.write("### 🛡️ Safe Redacted Text")
                    st.info(data.get("redacted_text", "N/A"))

                    st.write("### 💡 Recommended Action")
                    st.write(f"*{data.get('action_recommendation', 'None')}*")

                with col4:
                    st.write("### 🕵️ Detected PII")
                    st.json(data.get("detected_pii", []))

                    st.write("### 📜 Compliance Warnings")
                    for warning in data.get("compliance_warnings", []):
                        st.write(f"- 🚩 {warning}")

            except json.JSONDecodeError:
                st.error("❌ Failed to parse Gemma's response into JSON. The model returned plain text instead.")
                st.write("Raw Output:", response.text)
            except Exception as e:
                st.error(f"An error occurred while calling Gemma 4: {e}")
