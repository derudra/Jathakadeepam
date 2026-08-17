# JathakaDeepam

Initial Streamlit + Prokerala MVP.

## Files

- `streamlit_app.py`
- `requirements.txt`
- `.gitignore`
- `.streamlit/config.toml`

## Secrets

Do NOT add API secrets to GitHub.

Add these in Streamlit Community Cloud → App settings / Advanced settings → Secrets:

```toml
PROKERALA_CLIENT_ID = "your-client-id"
PROKERALA_CLIENT_SECRET = "your-client-secret"
GEMINI_API_KEY = "your-gemini-api-key"
```

Gemini is not connected in this first milestone. The key is included in the secret layout so it is ready for the next build.

## Goal of V1

Enter birth details → resolve coordinates/timezone → call Prokerala → inspect Basic Kundli and Planet Position data.
