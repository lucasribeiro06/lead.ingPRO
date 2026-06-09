# Lead.ing PRO (V2)

Premium [Streamlit](https://streamlit.io/) app for **B2B lead validation and intelligence** powered by Google Gemini.

## Features

- **Email validation** — regex format check
- **B2C detection** — Gmail, Hotmail, Yahoo, Outlook, Live, iCloud (no API call)
- **Corporate classification** — decision-making status + B2B fit (High / Medium / Low)
- **Company insights** — for **High** and **Medium** fit, AI returns a brief company description and why the lead is a strong B2B target
- **Domain deduplication** — one Gemini call per unique corporate domain
- **CSV export** — full results table

## Setup

```powershell
cd C:\Users\Lucas\Projects\gemini-streamlit-app
py -m pip install -r requirements.txt
```

Get a Gemini API key: [Google AI Studio](https://aistudio.google.com/apikey)

## Run

```powershell
py -m streamlit run app.py
```

## Result columns

| Column | Description |
|--------|-------------|
| Original Email | Input address |
| Domain | Host after `@` |
| Validation Status | Invalid, B2C, Corporate, API errors, etc. |
| Decision-Making Status (AI) | Executive, Director, Manager, Specialist/IC, Unknown |
| B2B Fit Level (AI) | High, Medium, Low |
| Company Insight (AI) | Company summary + fit rationale (High/Medium only) |

## Project structure

| File | Role |
|------|------|
| `app.py` | Entry point |
| `ui.py` | Lead.ing PRO branding and layout |
| `validators.py` | Parsing, rows, public domains |
| `classifier.py` | Gemini prompts and batch processing |

## Model

Default: **`gemini-3.1-flash-lite`**. Update `MODEL_NAME` in `classifier.py` if your account uses a different ID — see [Gemini models](https://ai.google.dev/gemini-api/docs/models/gemini).
