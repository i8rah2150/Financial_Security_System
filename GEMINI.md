# Workspace Rules & Guidelines

## Core Principles
1. **Stack & SDK**: Always build in Python using **Streamlit** and the official **`google-genai`** SDK (targeting `gemini-3.5-flash-lite`).
2. **Code Clarity**: Keep the code clean, readable, modular, and well-commented so every line and section is easy to understand.
3. **Structured Dashboards**: Build structured, interactive dashboards utilizing `st.columns`, `st.tabs`, `st.dataframe`, `st.form`, and interactive checklists/metrics — never a plain chatbot interface.
4. **State Management**: Persist user inputs, uploaded data, and AI analysis results in `st.session_state` so values persist across user interactions and reruns.
5. **Secure API Key Handling**: Read the Gemini API key cleanly from `st.secrets` (`st.secrets.get("GEMINI_API_KEY")`) with a fallback to a sidebar password input (`st.sidebar.text_input(..., type="password")`). Never hardcode keys or use `.env` files.
6. **Resilient API Calls**: Wrap all Gemini API calls in `try/except` blocks accompanied by `st.spinner()` and automatic retry handling with backoff for `429` (rate limit) or transient errors.
7. **Reliable Demo Readiness**: Always include a working "Load Sample Data" button prominently on the main screen to enable instant, deterministic live demonstrations.
