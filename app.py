import streamlit as st
import requests

st.set_page_config(page_title="Support Hub", page_icon="💬", layout="centered")

BACKEND_URL = st.sidebar.text_input("Backend URL", value="http://localhost:8000")

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
                    st.error("Service temporarily unavailable. Please try again.")
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")