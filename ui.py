"""Lead.ing PRO — brand-aligned Streamlit UI."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from classifier import MODEL_NAME, process_leads
from validators import COL_B2B, COL_STATUS

APP_VERSION = "V2"
PRODUCT_NAME = "Lead.ing PRO"

# Brand palette (logo-aligned)
NAVY = "#1E3A8A"
GREEN = "#10B981"
GRAY = "#4B5563"  # user listed #4BS563 — interpreted as #4B5563
MUTED = "#A1A1AA"
SURFACE = "#F8FAFC"
TEXT = "#111827"
BG = "#FDFCF1"

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
LOGO_CANDIDATES = (
    "logo.png",
    "logo.jpg",
    "logo.jpeg",
    "logo.jfif",
    "logo.webp",
    "logo.svg",
    "Logo.png",
    "Logo.jpg",
)


def _logo_path() -> Path | None:
    """Resolve logo from assets/ (fixed names first, then any logo* image)."""
    if not ASSETS_DIR.is_dir():
        return None
    for name in LOGO_CANDIDATES:
        path = ASSETS_DIR / name
        if path.is_file():
            return path
    for pattern in ("logo.*", "Logo.*", "*logo*"):
        matches = sorted(ASSETS_DIR.glob(pattern))
        for path in matches:
            if path.is_file() and path.suffix.lower() in {
                ".png",
                ".jpg",
                ".jpeg",
                ".jfif",
                ".webp",
                ".gif",
                ".svg",
            }:
                return path
    return None


def _logo_cache_key(path: Path) -> str:
    """Change key when the file changes so Streamlit shows the new logo."""
    return f"logo-{path.stat().st_mtime_ns}"


def show_logo(path: Path, *, slot: str = "main") -> None:
    st.image(
        str(path),
        width="stretch"
    )


def inject_theme() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

        :root {{
            --lead-navy: {NAVY};
            --lead-green: {GREEN};
            --lead-gray: {GRAY};
            --lead-muted: {MUTED};
            --lead-surface: {SURFACE};
            --lead-text: {TEXT};
            --lead-bg: {BG};
        }}

        .stApp {{
            background: linear-gradient(180deg, {BG} 0%, {SURFACE} 100%);
            color: {TEXT};
            font-family: 'Plus Jakarta Sans', sans-serif;
        }}

        [data-testid="stHeader"] {{
            background: rgba(253, 252, 241, 0.92);
            border-bottom: 1px solid rgba(30, 58, 138, 0.08);
        }}

        [data-testid="stSidebar"] {{
            background: {SURFACE};
            border-right: 1px solid rgba(30, 58, 138, 0.1);
        }}

        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] label {{
            color: {TEXT} !important;
        }}

        [data-testid="stSidebar"] .stCaption {{
            color: {GRAY} !important;
        }}

        h1, h2, h3, h4, label, p, span {{
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }}

        h2, h3, h4 {{
            color: {NAVY} !important;
            font-weight: 700 !important;
        }}

        .lead-hero {{
            display: flex;
            align-items: center;
            gap: 1.75rem;
            padding: 1.5rem 2rem;
            margin-bottom: 1.5rem;
            border-radius: 16px;
            background: #ffffff;
            border: 1px solid rgba(30, 58, 138, 0.1);
            box-shadow: 0 4px 24px rgba(30, 58, 138, 0.06);
        }}

        .lead-hero-copy {{
            flex: 1;
            min-width: 0;
        }}

        .lead-badge {{
            display: inline-block;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: {NAVY};
            background: rgba(30, 58, 138, 0.08);
            border: 1px solid rgba(30, 58, 138, 0.15);
            padding: 0.28rem 0.7rem;
            border-radius: 999px;
            margin-bottom: 0.65rem;
        }}

        .lead-hero .tagline {{
            color: {GRAY};
            font-size: 1rem;
            line-height: 1.55;
            margin: 0;
            max-width: 42rem;
        }}

        .lead-section-label {{
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: {GREEN};
            margin-bottom: 0.35rem;
        }}

        .lead-panel {{
            background: #ffffff;
            border: 1px solid rgba(30, 58, 138, 0.1);
            border-radius: 14px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 12px rgba(17, 24, 39, 0.04);
        }}

        .lead-footer {{
            text-align: center;
            color: {MUTED};
            font-size: 0.8rem;
            padding: 2rem 0 0.5rem;
        }}

        div[data-testid="stMetric"] {{
            background: #ffffff;
            border: 1px solid rgba(30, 58, 138, 0.1);
            border-top: 3px solid {GREEN};
            border-radius: 12px;
            padding: 0.85rem 1rem;
            box-shadow: 0 2px 8px rgba(17, 24, 39, 0.04);
        }}

        div[data-testid="stMetric"] label {{
            color: {GRAY} !important;
            font-size: 0.8rem !important;
        }}

        div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
            color: {NAVY} !important;
            font-weight: 700 !important;
        }}

        .stButton > button[kind="primary"] {{
            background: linear-gradient(90deg, {NAVY} 0%, {GREEN} 100%) !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 700 !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            padding: 0.7rem 1.5rem !important;
            border-radius: 10px !important;
            box-shadow: 0 6px 20px rgba(30, 58, 138, 0.25);
        }}

        .stButton > button[kind="primary"]:hover {{
            filter: brightness(1.05);
            box-shadow: 0 8px 28px rgba(16, 185, 129, 0.3);
        }}

        .stDownloadButton > button {{
            border: 1px solid {NAVY} !important;
            color: {NAVY} !important;
            background: #ffffff !important;
            font-weight: 600 !important;
            border-radius: 10px !important;
        }}

        .stTextArea textarea, .stTextInput input {{
            border-radius: 10px !important;
            border-color: rgba(161, 161, 170, 0.6) !important;
        }}

        .stTextArea textarea:focus, .stTextInput input:focus {{
            border-color: {GREEN} !important;
            box-shadow: 0 0 0 1px {GREEN} !important;
        }}

        hr {{
            border-color: rgba(30, 58, 138, 0.1) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    logo = _logo_path()
    col_logo, col_copy = st.columns([1, 2.2], vertical_alignment="center")

    with col_logo:
        if logo:
            show_logo(logo, slot="hero")
        else:
            st.markdown(
                f'<p style="color:{MUTED};font-size:0.85rem;">Logo not found in assets/</p>',
                unsafe_allow_html=True,
            )

    with col_copy:
        st.markdown(
            f"""
            <div class="lead-hero-copy">
                <span class="lead-badge">{APP_VERSION} · B2B Lead Intelligence</span>
                <p class="tagline">
                    Validate leads by domain, score B2B fit, infer decision-making roles,
                    and surface company insights for your highest-value targets.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_sidebar() -> None:
    with st.sidebar:
        logo = _logo_path()
        if logo:
            show_logo(logo, slot="sidebar")
        else:
            st.markdown(f"### {PRODUCT_NAME}")
        st.caption(f"{APP_VERSION} · Lead validation & B2B scoring")
        st.divider()
        st.markdown(
            '<p class="lead-section-label">Workflow</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            1. Paste emails (one per line)  
            2. Add your **Gemini API key**  
            3. Click **Analyze Leads**

            Public inboxes are flagged instantly — no API usage.
            """
        )
        st.divider()
        with st.expander("Engine", expanded=False):
            st.caption(f"Model: `{MODEL_NAME}`")
            st.caption("One API call per unique corporate domain.")
            st.caption("High/Medium fit includes AI company insights.")


def render_input_panel() -> tuple[str, str]:
    st.markdown(
        '<p class="lead-section-label">Input</p>',
        unsafe_allow_html=True,
    )
    col_main, col_key = st.columns([1.6, 1], gap="large")

    with col_main:
        with st.container(border=True):
            st.markdown("##### Lead list")
            emails_raw = st.text_area(
                "Emails",
                height=200,
                placeholder="ceo@acmecorp.com\nsales@startup.io\nuser@gmail.com",
                help="One email address per line.",
                label_visibility="collapsed",
            )

    with col_key:
        with st.container(border=True):
            st.markdown("##### API credentials")
            api_key = st.text_input(
                "Gemini API key",
                type="password",
                placeholder="AIza…",
                help="Session-only. Required for corporate domains.",
            )
            st.caption(
                f'<span style="color:{GRAY}">'
                '<a href="https://aistudio.google.com/apikey" style="color:{NAVY}">Get a key</a>'
                " · Never stored on disk</span>",
                unsafe_allow_html=True,
            )

    return emails_raw, api_key


def render_metrics(df) -> None:
    total = len(df)
    corporate = (df[COL_STATUS] == "Corporate Email").sum()
    high = (df[COL_B2B] == "High").sum()
    medium = (df[COL_B2B] == "Medium").sum()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total leads", total)
    c2.metric("Corporate", int(corporate))
    c3.metric("High fit", int(high))
    c4.metric("Medium fit", int(medium))


def render_results() -> None:
    if "results_df" not in st.session_state or st.session_state["results_df"].empty:
        return

    st.markdown("---")
    st.markdown(
        '<p class="lead-section-label">Results</p>',
        unsafe_allow_html=True,
    )
    st.markdown("##### Analysis output")

    df = st.session_state["results_df"]
    render_metrics(df)

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            "Company Insight (AI)": st.column_config.TextColumn(
                "Company Insight (AI)",
                width="large",
                help="Brief company context and fit rationale (High/Medium only).",
            ),
            "B2B Fit Level (AI)": st.column_config.TextColumn(
                "B2B Fit Level (AI)",
                help="High, Medium, or Low B2B commercial fit.",
            ),
        },
    )

    st.download_button(
        label="Download CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="leading_pro_leads.csv",
        mime="text/csv",
        width="stretch",
    )

    with st.expander("Status breakdown"):
        st.bar_chart(df[COL_STATUS].value_counts(), color=GREEN)


def render_footer() -> None:
    st.markdown(
        f'<p class="lead-footer">{PRODUCT_NAME} {APP_VERSION} · Powered by Gemini</p>',
        unsafe_allow_html=True,
    )


def run_app() -> None:
    logo = _logo_path()
    st.set_page_config(
        page_title=f"{PRODUCT_NAME} — B2B Lead Intelligence",
        page_icon=str(logo) if logo else "◆",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_theme()
    render_sidebar()
    render_hero()

    emails_raw, api_key = render_input_panel()

    st.markdown(
        '<p class="lead-section-label">Run</p>',
        unsafe_allow_html=True,
    )
    if st.button("Analyze Leads", type="primary", width="stretch"):
        with st.spinner("Processing your lead list…"):
            df = process_leads(emails_raw, api_key)
        if df is not None and not df.empty:
            st.session_state["results_df"] = df
            st.success(f"Analyzed {len(df)} lead(s).")
        elif df is not None:
            st.session_state.pop("results_df", None)

    render_results()
    render_footer()
