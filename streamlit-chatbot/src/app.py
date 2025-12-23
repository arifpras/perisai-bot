# Streamlit Bond Chatbot
# Connects to FastAPI backend on Render Cloud (https://perisai-api.onrender.com/chat)

import streamlit as st
import requests
import base64
import os
from io import BytesIO

# Configuration - can be overridden via environment variable
# Production: uses Render cloud API
# Development: can override with BOND_API_URL env var to use localhost
API_URL = os.environ.get("BOND_API_URL", "https://perisai-api.onrender.com/chat")
API_TIMEOUT = 30

# Page config
st.set_page_config(
    page_title="Bond Chatbot",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("📈 Bond Price & Yield Chatbot")
st.markdown("Ask questions about bond prices, yields, and generate plots!")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "rows" in message and message["rows"]:
            # Format rows as WhatsApp-style text (handles both POINT and RANGE queries)
            rows_text = []
            for row in message["rows"]:
                if "date" in row:
                    # RANGE query — include date
                    rows_text.append(f"🔹 {row['series']} | {row['tenor']} | {row['date']} | Price: {row['price']:.2f} | Yield: {row['yield']:.2f}%")
                else:
                    # POINT query — no date
                    rows_text.append(f"🔹 {row['series']} | {row['tenor']} | Price: {row['price']:.2f} | Yield: {row['yield']:.2f}%")
            st.markdown(f"```\n" + "\n".join(rows_text) + "\n```")
        if "image" in message and message["image"]:
            st.image(message["image"])

# Chat input
if prompt := st.chat_input("Ask about bond prices or yields (e.g., 'plot yield 10 year May 2023')"):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Call API
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Use custom API URL if set, otherwise use default
                api_url = st.session_state.get("custom_api_url", API_URL)
                
                response = requests.post(
                    api_url,
                    json={"q": prompt},
                    timeout=API_TIMEOUT
                )
                response.raise_for_status()
                data = response.json()
                
                # Display text response
                text = data.get("text", "No response text")
                st.markdown(text)
                
                # Display rows if present (for POINT and RANGE queries) — WhatsApp-style text
                rows = data.get("rows")
                if rows:
                    rows_text = []
                    for row in rows:
                        if "date" in row:
                            # RANGE query — include date
                            rows_text.append(f"🔹 {row['series']} | {row['tenor']} | {row['date']} | Price: {row['price']:.2f} | Yield: {row['yield']:.2f}%")
                        else:
                            # POINT query — no date
                            rows_text.append(f"🔹 {row['series']} | {row['tenor']} | Price: {row['price']:.2f} | Yield: {row['yield']:.2f}%")
                    st.markdown(f"```\n" + "\n".join(rows_text) + "\n```")
                
                # Display image if present
                image_data = None
                img_b64 = data.get("image_base64") or data.get("image") or data.get("imageBase64")
                if img_b64:
                    try:
                        img_bytes = base64.b64decode(img_b64)
                        image_data = BytesIO(img_bytes)
                        st.image(image_data)
                    except Exception as e:
                        st.error(f"Failed to decode image: {e}")
                
                # Add assistant message to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": text,
                    "image": image_data,
                    "rows": rows
                })
                
            except requests.exceptions.ConnectionError:
                error_msg = "❌ Cannot connect to API server. Make sure it's running:\n```bash\nuvicorn app_fastapi:app --reload --port 8000\n```"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
            except requests.exceptions.Timeout:
                error_msg = "⏱️ Request timed out. Try a simpler query."
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# Sidebar with examples
with st.sidebar:
    st.header("🔧 Configuration")
    
    # Show current API endpoint
    st.info(f"**API:** `{API_URL}`")
    
    # Option to override API URL
    with st.expander("Change API URL"):
        custom_host = st.text_input("Backend Host", value="perisai-api.onrender.com", help="e.g., perisai-api.onrender.com or localhost for development")
        custom_port = st.text_input("Backend Port", value="443", help="Usually 443 for cloud, 8000 for localhost")
        protocol = st.selectbox("Protocol", options=["https", "http"], index=0)
        if st.button("Update API URL"):
            st.session_state.custom_api_url = f"{protocol}://{custom_host}:{custom_port}/chat"
            st.success(f"API URL updated to: {st.session_state.custom_api_url}")
            st.rerun()
    
    st.divider()
    st.header("📝 Example Queries")
    examples = [
        "plot yield 10 year May 2023",
        "average yield Q1 2023",
        "yield 10 year 2023-05-10",
        "plot 10 year 2023",
        "average yield 10 year May 2023",
    ]
    
    st.markdown("Try these:")
    for ex in examples:
        st.code(ex, language="text")
    
    st.divider()
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🌐 Network Access")
    st.markdown("""
    **Cloud Deployment:**
    - API: `https://perisai-api.onrender.com` (Render)
    - Streamlit: `perisai-bot.streamlit.app` (Streamlit Cloud)
    
    **For local development:**
    1. Start FastAPI locally: `uvicorn app_fastapi:app --host 0.0.0.0 --port 8000`
    2. Start Streamlit: `streamlit run streamlit-chatbot/src/app.py --server.address 0.0.0.0`
    3. Find your IP: `ipconfig getifaddr en0`
    4. Access from other computers: `http://<your-ip>:8501`
    5. Update API URL above to: `http://<your-ip>:8000`
    """)
    st.markdown("---")
    st.markdown("Make sure your FastAPI server is running!")
