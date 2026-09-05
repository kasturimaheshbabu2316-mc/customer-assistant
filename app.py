import streamlit as st
import requests

st.set_page_config(page_title="Support Hub", page_icon="💬", layout="centered")

with st.sidebar:
    st.title("Settings")
    BACKEND_URL = st.text_input("Backend URL", value="http://127.0.0.1:8000")
    try:
        health_res = requests.get(f"{BACKEND_URL}/health", timeout=2)
        if health_res.status_code == 200:
            h_data = health_res.json()
            st.success(f"Backend Connected ({h_data.get('vector_count', 0)} chunks indexed)")
        else:
            st.warning(f"Backend status: {health_res.status_code}")
    except Exception:
        st.error("Backend Offline\nStart with: `python server.py`")

st.title("Customer Service Portal")
st.caption("Powered by Gemini 3 Flash & RAG. Ask about returns, shipping, or support.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! How can I assist you with your order or our policies today?"}
    ]

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("Verified Reference Context"):
                for src in msg["sources"]:
                    st.caption(f"• {src}")

# User input
if user_input := st.chat_input("Type your question here..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Checking verified store policies..."):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/ask",
                    json={"query": user_input},
                    timeout=15
                )
                if res.status_code == 200:
                    data = res.json()
                    answer = data["answer"]
                    sources = data.get("sources", [])

                    st.markdown(answer)
                    if sources:
                        with st.expander("Verified Reference Context"):
                            for s in sources:
                                st.caption(f"• {s}")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                else:
                    st.error(f"Service returned error ({res.status_code}): {res.text}")
            except Exception as e:
                st.error(f"Failed to connect to backend at {BACKEND_URL}: {e}\n\nPlease ensure the backend server is running via `python server.py`.")