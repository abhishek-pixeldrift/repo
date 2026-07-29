import os
import json
import re
import streamlit as st
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. PAGE SETUP & SLEEK SAAS CSS
# ----------------------------------------------------
st.set_page_config(page_title="PrivaGuard | Data Leak Shield", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
    /* Metric Cards */
    .metric-container {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 18px;
        text-align: center;
    }
    .metric-value-high {
        color: #ff4d4d;
        font-size: 2rem;
        font-weight: 800;
    }
    .metric-label {
        color: #8b949e;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* PII Threat Badges */
    .pii-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-left: 4px solid #ff4d4d;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .pii-tag {
        background-color: #21262d;
        color: #f0f6fc;
        border: 1px solid #30363d;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .pii-value {
        color: #ff7b72;
        font-family: monospace;
        font-size: 0.95rem;
    }

    /* --- SLEEK REDACTED TEXT BOX (FIXED) --- */
    .redacted-box {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        color: #e6edf3;
        font-size: 1.05rem;
        line-height: 2.2; /* Spacing out lines for pill badges */
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.3);
    }

    /* Modern Security Pill Badge */
    mark.redact {
        background: linear-gradient(135deg, #3d1b20 0%, #220f12 100%);
        color: #ff7b72;
        border: 1px solid #6e272d;
        padding: 4px 12px;
        border-radius: 20px; /* Rounded pill style */
        font-weight: 600;
        font-size: 0.8rem;
        letter-spacing: 0.5px;
        display: inline-flex;
        align-items: center;
        margin: 0 3px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    /* Warning Callouts */
    .warning-card {
        background-color: rgba(187, 128, 9, 0.1);
        border: 1px solid #bb8009;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        color: #d29922;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ PrivaGuard: Edge Privacy Shield")
st.caption("Enterprise PII Inspector & Redaction Engine • Powered by Gemma 4 26B")

# Securely retrieve API Key
raw_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not raw_key:
    st.error("⚠️ API Key missing! Please add `GEMINI_API_KEY` to your Streamlit Secrets.")
    st.stop()

# Clean key
api_key = raw_key.strip().replace("\n", "").replace("\r", "").replace(" ", "")
client = genai.Client(api_key=api_key)

# ----------------------------------------------------
# 2. SYSTEM PROMPT
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
# 3. WEB UI
# ----------------------------------------------------
user_input = st.text_area(
    "Paste user input, medical notes, or raw server logs to scan for PII leaks:",
    placeholder="e.g., Hi, my name is Rahul Sharma. My email is rahul.sharma99@gmail.com and phone is +91 98765 43210...",
    height=130
)

if st.button("🔍 Run Privacy Audit", type="primary", use_container_width=True):
    if not user_input.strip():
        st.warning("Please enter some text before scanning!")
    else:
        with st.spinner("Analyzing text with Gemma 4..."):
            try:
                contents = [
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=user_input)],
                    ),
                ]

                generate_content_config = types.GenerateContentConfig(
                    system_instruction=privacy_system_instruction,
                    temperature=0.2, 
                )

                response = client.models.generate_content(
                    model="gemma-4-26b-a4b-it",
                    contents=contents,
                    config=generate_content_config,
                )

                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_text)

                st.divider()

                # --- 🎨 DASHBOARD METRICS ROW ---
                col_m1, col_m2, col_m3 = st.columns(3)
                
                risk_score = data.get("risk_score", 0)
                risk_level = data.get("privacy_risk_level", "LOW")

                with col_m1:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">Privacy Risk Score</div>
                        <div class="metric-value-high">{risk_score} / 100</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_m2:
                    color = "#ff4d4d" if risk_level == "HIGH" else "#d29922" if risk_level == "MEDIUM" else "#3fb950"
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">Threat Severity</div>
                        <div style="color: {color}; font-size: 2rem; font-weight: 800;">{risk_level}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with col_m3:
                    pii_count = len(data.get("detected_pii", []))
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-label">PII Entities Leaked</div>
                        <div style="color: #58a6ff; font-size: 2rem; font-weight: 800;">{pii_count}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.write("") 

                # --- 🎨 DETAILS GRID LAYOUT ---
                col_left, col_right = st.columns([1, 1], gap="medium")

                with col_left:
                    st.subheader("🛡️ Sanitized Text (Redacted Output)")
                    
                    # DYNAMIC CLEANER: Converts [REDACTED_ACCOUNT_NUMBER] -> 🔒 ACCOUNT NUMBER pill badge
                    redacted_raw = data.get("redacted_text", "")
                    
                    def make_badge(match):
                        tag_name = match.group(1).replace("[REDACTED_", "").replace("]", "").replace("_", " ")
                        return f'<mark class="redact">🔒 {tag_name}</mark>'
                    
                    styled_redacted = re.sub(r'(\[REDACTED_[A-Z_]+\])', make_badge, redacted_raw)
                    
                    st.markdown(f'<div class="redacted-box">{styled_redacted}</div>', unsafe_allow_html=True)

                    st.write("")
                    st.subheader("💡 Recommended Developer Action")
                    st.info(f"👉 {data.get('action_recommendation', 'No immediate action needed.')}")

                with col_right:
                    st.subheader("🕵️ Detected PII Tokens")
                    pii_list = data.get("detected_pii", [])
                    
                    if pii_list:
                        for pii in pii_list:
                            st.markdown(f"""
                            <div class="pii-card">
                                <span class="pii-tag">{pii.get('type', 'PII')}</span>
                                <span class="pii-value">{pii.get('value', '')}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.success("No sensitive PII tokens identified in payload.")

                    st.write("")
                    st.subheader("📜 Compliance & Regulatory Risks")
                    warnings = data.get("compliance_warnings", [])
                    for warn in warnings:
                        st.markdown(f'<div class="warning-card">⚠️ {warn}</div>', unsafe_allow_html=True)

            except json.JSONDecodeError:
                st.error("❌ Model returned plain text instead of structured JSON.")
                st.code(response.text)
            except Exception as e:
                st.error(f"An error occurred: {e}")
