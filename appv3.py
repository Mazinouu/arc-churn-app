"""
AlRajhi Capital — Retention & Churn Analytics  v4
All issues fixed · Python 3.7+ · Plotly 4.x+
"""

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# ── pandas Styler compatibility (applymap renamed to map in pandas 2.1+) ──
def _styler_map(styler, fn, subset):
    """Works on pandas < 2.1 and >= 2.1"""
    try:
        return styler.map(fn, subset=subset)        # pandas >= 2.1
    except AttributeError:
        return styler.applymap(fn, subset=subset)   # pandas < 2.1

# ──────────────────────────────────────────────
# PAGE CONFIG  (first Streamlit call)
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="ARC Churn Intelligence",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject viewport meta for proper mobile scaling
st.markdown(
    '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">',
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# PALETTE
# ──────────────────────────────────────────────
ACCENT   = "#1A56DB"
ACCENTLT = "#EBF1FF"
GREEN    = "#0E9F6E"
GREENLT  = "#EDFAF5"
RED      = "#E02424"
REDLT    = "#FDF2F2"
AMBER    = "#C27803"
AMBERLT  = "#FDF6E7"
PURPLE   = "#7E3AF2"
PURPLELT = "#F3EEFF"
BORDER   = "#E5E7EB"
BG       = "#F4F6FA"
TEXT     = "#111928"
SUB      = "#6B7280"
WHITE    = "#FFFFFF"

TIER_C  = {"Critical": RED,    "High": AMBER,   "Medium": PURPLE,   "Low": GREEN}
TIER_LT = {"Critical": REDLT,  "High": AMBERLT, "Medium": PURPLELT, "Low": GREENLT}
TORDER  = ["Critical", "High", "Medium", "Low"]

# Account-type colour map (4 distinct brand colours)
ACCT_COLORS = {
    "Equities":       ACCENT,
    "Sukuk":          GREEN,
    "Margin Trading": AMBER,
    "Mutual Funds":   PURPLE,
}

def _rgba(h, a):
    h = h.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return "rgba({},{},{},{})".format(r, g, b, a)

# ──────────────────────────────────────────────
# GLOBAL CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
/* ════════════════════════════════════════════════════
   BASE — applies to all screen sizes
   ════════════════════════════════════════════════════ */
html,body,[class*="css"]{
  font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,sans-serif;
  -webkit-text-size-adjust:100%;
}

/* Fluid main container */
.main .block-container{
  padding-top:1.2rem;
  padding-bottom:2rem;
  padding-left:1rem;
  padding-right:1rem;
  max-width:100% !important;
  width:100% !important;
}

/* All images and iframes scale inside their containers */
img, iframe, video { max-width:100%; height:auto; }

/* Plotly charts: always fill their column */
.js-plotly-plot, .plotly, .plot-container { width:100% !important; }

/* ════════════════════════════════════════════════════
   SIDEBAR — rich blue gradient
   ════════════════════════════════════════════════════ */
[data-testid="stSidebar"]{
  background: linear-gradient(170deg,#0e3fa8 0%,#1A56DB 55%,#1d62f0 100%) !important;
  min-width:220px !important;
  max-width:260px !important;
}
[data-testid="stSidebar"] *{color:#ffffff !important;}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3{color:#ffffff !important;font-weight:700 !important;}
[data-testid="stSidebar"] label{
  color:rgba(255,255,255,0.70) !important;
  font-size:.68rem !important;text-transform:uppercase;
  letter-spacing:.08em;font-weight:700 !important;
}

/* Selectbox */
[data-testid="stSidebar"] [data-baseweb="select"] > div:first-child{
  background:#ffffff !important;border:none !important;
  border-radius:8px !important;box-shadow:0 2px 8px rgba(0,0,0,.18) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] *{color:#111928 !important;}
[data-testid="stSidebar"] [data-baseweb="select"] svg{color:#1A56DB !important;}

/* Multiselect */
[data-testid="stSidebar"] [data-baseweb="select"][aria-multiselectable="true"] > div,
[data-testid="stSidebar"] .stMultiSelect > div > div{
  background:#ffffff !important;border:none !important;
  border-radius:8px !important;box-shadow:0 2px 8px rgba(0,0,0,.18) !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"]{
  background:#E02424 !important;border-radius:6px !important;border:none !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"] span{color:#ffffff !important;font-weight:700 !important;}
[data-testid="stSidebar"] [data-baseweb="tag"] svg{color:#ffffff !important;opacity:.9;}
[data-testid="stSidebar"] [data-baseweb="tag"][style*="rgb"]{background:#E02424 !important;}

/* Slider */
[data-testid="stSidebar"] .stSlider > div{padding:0 !important;}
[data-testid="stSidebar"] .stSlider [data-testid="stTickBarMin"],
[data-testid="stSidebar"] .stSlider [data-testid="stTickBarMax"],
[data-testid="stSidebar"] .stSlider [data-testid="stSliderThumbValue"]{
  color:rgba(255,255,255,0.90) !important;font-size:.72rem !important;font-weight:600 !important;
}
[data-testid="stSidebar"] [data-testid="stSlider"] div[role="slider"]{
  background:#E02424 !important;box-shadow:0 0 0 4px rgba(224,36,36,.35) !important;
}
[data-testid="stSidebar"] .stSlider > div > div > div{background:rgba(255,255,255,.20) !important;}
[data-testid="stSidebar"] .stSlider > div > div > div > div{background:#E02424 !important;}

/* Divider & scrollbar */
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,0.18) !important;}
[data-testid="stSidebar"] ::-webkit-scrollbar{width:4px;}
[data-testid="stSidebar"] ::-webkit-scrollbar-track{background:rgba(255,255,255,.08);}
[data-testid="stSidebar"] ::-webkit-scrollbar-thumb{background:rgba(255,255,255,.3);border-radius:4px;}

/* Logo white + glow */
[data-testid="stSidebar"] svg path{fill:#ffffff !important;stroke:none !important;}
[data-testid="stSidebar"] svg circle{fill:#ffffff !important;stroke:none !important;}
[data-testid="stSidebar"] svg rect{fill:#ffffff !important;stroke:none !important;}
[data-testid="stSidebar"] svg *{fill:#ffffff !important;stroke:none !important;}
[data-testid="stSidebar"] img{
  filter:brightness(0) invert(1) drop-shadow(0 0 6px rgba(255,255,255,0.8)) !important;
}

/* ════════════════════════════════════════════════════
   HIDE STREAMLIT CHROME
   ════════════════════════════════════════════════════ */
#MainMenu,header[data-testid="stHeader"],footer,
[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],[data-testid="baseButton-header"],
.stActionButton,a[href*="github"],
button[title="View app source"],button[title="Share this app"],
button[title="Open settings"],
[data-testid="manage-app-button"],[data-testid="stBottom"],
[class*="statusWidget"],[class*="viewerBadge"],[class*="manageApp"],
.st-emotion-cache-1dp5vir,iframe[title="st_app_chrome"]{
  visibility:hidden !important;display:none !important;
}

/* ════════════════════════════════════════════════════
   SCORING LEGEND COLOURS (beat sidebar * override)
   ════════════════════════════════════════════════════ */
.score-legend-crit{color:#FF4444 !important;font-weight:700 !important;}
.score-legend-high{color:#F5C400 !important;font-weight:700 !important;}
.score-legend-med {color:#C084FC !important;font-weight:700 !important;}
.score-legend-low {color:#34D399 !important;font-weight:700 !important;}

/* ════════════════════════════════════════════════════
   COMPONENT STYLES
   ════════════════════════════════════════════════════ */
.kpi{
  background:#fff;border-radius:12px;
  padding:1rem 1.2rem .9rem;
  border:1px solid #E5E7EB;
  box-shadow:0 2px 8px rgba(0,0,0,.05);
  transition:transform .15s,box-shadow .15s;
  height:100%;
}
.kpi:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.08);}
.kpi-lbl{font-size:.67rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.07em;color:#6B7280;margin-bottom:.22rem;}
.kpi-val{font-size:1.85rem;font-weight:800;line-height:1.1;}
.kpi-sub{font-size:.71rem;color:#6B7280;margin-top:.18rem;}
.sec{font-size:.8rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.05em;color:#111928;
  border-left:3px solid #1A56DB;padding-left:.5rem;margin:.1rem 0 .5rem;}
.stTabs [data-baseweb="tab-list"]{gap:3px;background:#fff;
  border-radius:10px;padding:4px;border:1px solid #E5E7EB;
  flex-wrap:wrap;}
.stTabs [data-baseweb="tab"]{border-radius:7px;padding:.38rem .9rem;
  font-weight:600;font-size:.8rem;color:#6B7280;white-space:nowrap;}
.stTabs [aria-selected="true"]{background:#1A56DB !important;color:#fff !important;}
.pill{display:inline-block;padding:2px 10px;border-radius:20px;
  font-size:.7rem;font-weight:700;margin:2px 2px;}
.sb-wrap{background:#E5E7EB;border-radius:5px;height:8px;width:100%;
  overflow:hidden;margin-top:5px;}
.sb-fill{height:8px;border-radius:5px;}
.callout{border-radius:10px;padding:.72rem 1rem;font-size:.82rem;margin-bottom:.8rem;}
.arc-hr{border:none;border-top:1px solid #E5E7EB;margin:.75rem 0 .9rem;}
.stDataFrame{border-radius:10px;overflow:hidden;width:100% !important;}
.stDataFrame > div{overflow-x:auto;}

/* Columns: allow wrapping on small screens */
[data-testid="column"]{min-width:0;}

/* ════════════════════════════════════════════════════
   DESKTOP  ≥ 1200px  — full layout, comfortable spacing
   ════════════════════════════════════════════════════ */
@media (min-width:1200px){
  .main .block-container{padding-left:2rem;padding-right:2rem;}
  .kpi-val{font-size:1.85rem;}
  .kpi-lbl{font-size:.67rem;}
  .sec{font-size:.8rem;}
  .stTabs [data-baseweb="tab"]{font-size:.8rem;padding:.38rem .9rem;}
}

/* ════════════════════════════════════════════════════
   LAPTOP  1025px – 1199px  — slightly tighter
   ════════════════════════════════════════════════════ */
@media (min-width:1025px) and (max-width:1199px){
  .main .block-container{padding-left:1.2rem;padding-right:1.2rem;}
  .kpi-val{font-size:1.6rem;}
  .kpi{padding:.85rem 1rem .8rem;}
  .stTabs [data-baseweb="tab"]{font-size:.75rem;padding:.35rem .7rem;}
}

/* ════════════════════════════════════════════════════
   TABLET  768px – 1024px  — collapse KPI row to 3+2,
   stack some chart pairs
   ════════════════════════════════════════════════════ */
@media (min-width:768px) and (max-width:1024px){
  .main .block-container{padding-left:1rem;padding-right:1rem;}

  /* KPI cards: 3 per row then 2 */
  .kpi-val{font-size:1.4rem;}
  .kpi-lbl{font-size:.63rem;}
  .kpi{padding:.75rem .9rem .7rem;}
  .kpi-sub{font-size:.65rem;}

  /* Tabs wrap to 2 rows comfortably */
  .stTabs [data-baseweb="tab-list"]{flex-wrap:wrap;gap:4px;}
  .stTabs [data-baseweb="tab"]{font-size:.72rem;padding:.32rem .65rem;}

  /* Section titles slightly smaller */
  .sec{font-size:.74rem;}

  /* Sidebar narrower on tablet */
  [data-testid="stSidebar"]{min-width:200px !important;max-width:220px !important;}
  [data-testid="stSidebar"] label{font-size:.62rem !important;}
}

/* ════════════════════════════════════════════════════
   MOBILE  ≤ 767px  — full single-column, large tap targets
   ════════════════════════════════════════════════════ */
@media (max-width:767px){
  .main .block-container{
    padding-left:.6rem !important;
    padding-right:.6rem !important;
    padding-top:.8rem !important;
  }

  /* KPI cards: single column, larger text for readability */
  .kpi-val{font-size:1.55rem;}
  .kpi-lbl{font-size:.65rem;}
  .kpi{padding:.8rem 1rem .75rem;border-radius:10px;}
  .kpi-sub{font-size:.67rem;}

  /* Charts fill full width — Streamlit columns stack automatically */
  .element-container,.stPlotlyChart{width:100% !important;}
  .js-plotly-plot .plotly{width:100% !important;}

  /* Tabs: wrap & shrink for narrow screens */
  .stTabs [data-baseweb="tab-list"]{
    flex-wrap:wrap;gap:3px;padding:3px;
  }
  .stTabs [data-baseweb="tab"]{
    font-size:.68rem;padding:.3rem .55rem;border-radius:6px;
  }

  /* Section titles */
  .sec{font-size:.72rem;letter-spacing:.03em;}

  /* Callout boxes */
  .callout{font-size:.78rem;padding:.65rem .85rem;}

  /* Pills smaller */
  .pill{font-size:.65rem;padding:2px 8px;}

  /* Sidebar: full-width overlay on mobile (Streamlit default behaviour) */
  [data-testid="stSidebar"]{
    min-width:80vw !important;
    max-width:88vw !important;
  }

  /* Dataframe: horizontal scroll on mobile */
  .stDataFrame > div{overflow-x:auto;-webkit-overflow-scrolling:touch;}

  /* Page header logo area */
  .page-hdr-title{font-size:.95rem !important;}
  .page-hdr-sub{font-size:.63rem !important;}

  /* Score bar */
  .sb-wrap{height:10px;}
  .sb-fill{height:10px;}
}

/* ════════════════════════════════════════════════════
   SMALL MOBILE  ≤ 400px  — compact everything further
   ════════════════════════════════════════════════════ */
@media (max-width:400px){
  .main .block-container{padding-left:.4rem !important;padding-right:.4rem !important;}
  .kpi-val{font-size:1.3rem;}
  .kpi{padding:.7rem .8rem .65rem;}
  .stTabs [data-baseweb="tab"]{font-size:.62rem;padding:.28rem .45rem;}
  .sec{font-size:.68rem;}
  .kpi-lbl{font-size:.6rem;}
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# PLOTLY HELPERS
# ──────────────────────────────────────────────
_AXIS = dict(
    title_font=dict(size=12, color=TEXT, family="Segoe UI"),
    tickfont=dict(size=10, color=SUB, family="Segoe UI"),
    showgrid=True, gridcolor=BORDER, gridwidth=1,
    zeroline=False, linecolor=BORDER, linewidth=1, showline=True,
)

def xax(title="", **kw):
    d = dict(_AXIS); d["title_text"] = title; d.update(kw); return d

def yax(title="", **kw):
    d = dict(_AXIS); d["title_text"] = title; d.update(kw); return d

def base_layout(height=320, margin=None, legend=False):
    m = margin or dict(l=58, r=20, t=28, b=52)
    out = dict(
        font=dict(family="Segoe UI, sans-serif", color=TEXT, size=11),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        height=height, margin=m, showlegend=legend,
        hoverlabel=dict(font_size=12, font_family="Segoe UI",
                        bgcolor=WHITE, bordercolor=BORDER),
    )
    if legend:
        out["legend"] = dict(orientation="h", y=1.10, x=0,
                             font=dict(size=10, color=TEXT, family="Segoe UI"),
                             bgcolor="rgba(0,0,0,0)")
    return out

# ──────────────────────────────────────────────
# SCORING ENGINE
# ──────────────────────────────────────────────
def score_portfolio(df):
    d = df.copy()
    d["_pts"] = 0
    d["_why"] = [[] for _ in range(len(d))]

    def add(mask, pts, lbl):
        d.loc[mask, "_pts"] += pts
        for i in d[mask].index:
            d.at[i, "_why"].append((lbl, pts))

    dy = d["Days_Since_Last_Trade"]
    dp = d["Portfolio_Value_Drop_Pct"]
    pv = d["Portfolio_Value"]
    fr = d["Trading_Frequency"]
    ac = d["Account_Type"]

    add(dy >= 30,  15, "No activity 30D")
    add(dy >= 90,  30, "No activity 90D")
    add(dy >= 60,  10, "Low engagement 60D")
    add(dy >= 90,  20, "Severe inactivity 90D")
    add(dp >= 25,  15, "AUM drop >= 25%")
    add(dp >= 50,  25, "AUM drop >= 50%")
    add(fr == "Low", 15, "Low trading frequency")
    add(pv <= pv.quantile(0.05), 20, "Near-zero assets")
    add(dy >= 270, 40, "Strong exit signal 270D+")
    add(ac == "Margin Trading", -15, "Active Margin (mitigant)")

    d["Churn_Score"] = d["_pts"].clip(0, 130)
    d["Risk_Tier"]   = d["Churn_Score"].apply(
        lambda s: "Critical" if s >= 90 else "High" if s >= 60 else "Medium" if s >= 35 else "Low"
    )
    d["Reason_Codes"] = d["_why"].apply(
        lambda rs: [r[0] for r in rs] if rs else ["No significant signals"]
    )
    d["AUM_at_Risk"] = d.apply(
        lambda r: r["Portfolio_Value"] if r["Risk_Tier"] in ("Critical","High") else 0, axis=1
    )
    return d.drop(columns=["_pts","_why"])

@st.cache_data(show_spinner=False)
def load_data(path):
    return score_portfolio(pd.read_excel(path))

# ──────────────────────────────────────────────
# UI COMPONENTS
# ──────────────────────────────────────────────
def logo_header(subtitle):
    p = "ARCLogo_Blue.svg"
    if os.path.exists(p):
        with open(p) as f:
            raw_svg = f.read()
        # Force all SVG elements white + add drop-shadow filter for visibility
        white_svg = raw_svg.replace('fill="#', 'fill="#FFFFFF" data-orig="').replace(
            "fill='#", "fill='#FFFFFF' data-orig='"
        )
        # Simpler approach: wrap in a styled div that applies CSS filter
        logo_el = (
            '<div style="height:44px;width:auto;'
            'filter:brightness(0) invert(1) drop-shadow(0 0 8px rgba(255,255,255,0.9));'
            'display:flex;align-items:center;">'
            + raw_svg +
            '</div>'
        )
    else:
        logo_el = (
            '<div style="background:rgba(255,255,255,0.2);color:#fff;font-weight:900;'
            'font-size:1rem;padding:7px 14px;border-radius:8px;'
            'letter-spacing:.04em;border:2px solid rgba(255,255,255,.5);">ARC</div>'
        )
    st.markdown(
        '<div style="display:flex;align-items:center;gap:12px;'
        'margin-top:4px;margin-bottom:.8rem;">'
        + logo_el +
        '<div>'
        '<div style="font-size:1.12rem;font-weight:800;color:' + TEXT + ';">AlRajhi Capital</div>'
        '<div style="font-size:.69rem;color:' + SUB + ';">' + subtitle + '</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )

def hr():
    st.markdown('<div class="arc-hr"></div>', unsafe_allow_html=True)

def sec(t):
    st.markdown('<div class="sec">' + t + '</div>', unsafe_allow_html=True)

def kpi(label, value, sub="", color=ACCENT):
    st.markdown(
        '<div class="kpi"><div class="kpi-lbl">' + label + '</div>'
        '<div class="kpi-val" style="color:' + color + ';">' + value + '</div>'
        '<div class="kpi-sub">' + sub + '</div></div>',
        unsafe_allow_html=True,
    )

def pill(text, fg, bg):
    return '<span class="pill" style="background:' + bg + ';color:' + fg + ';">' + text + '</span>'

def score_bar_html(score):
    pct = min(score / 130 * 100, 100)
    c = RED if score >= 90 else AMBER if score >= 60 else PURPLE if score >= 35 else GREEN
    return (
        '<div class="sb-wrap"><div class="sb-fill" '
        'style="width:' + "{:.1f}".format(pct) + '%;background:' + c + ';"></div></div>'
    )

def badge_html(tier):
    return pill(tier, TIER_C[tier], TIER_LT[tier])

# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
def sidebar_filters(df):
    st.sidebar.markdown("---")
    st.sidebar.markdown("### &#127775; Filters")

    acct_opts = ["All"] + sorted(df["Account_Type"].unique().tolist())
    sel_acct  = st.sidebar.selectbox("Account Type", acct_opts)

    tiers = st.sidebar.multiselect("Risk Tier", TORDER, default=TORDER)

    lo, hi = int(df["Churn_Score"].min()), int(df["Churn_Score"].max())
    rng = st.sidebar.slider("Churn Score", lo, hi, (lo, hi))

    st.sidebar.markdown("---")
    # CSS classes beat the sidebar * override — colours guaranteed visible
    st.sidebar.markdown(
        '<div style="font-size:.74rem;line-height:2.0;padding:.05rem 0;">'
        '<div style="font-size:.79rem;font-weight:800;color:#ffffff;'
        'letter-spacing:.03em;margin-bottom:.3rem;">&#9776; Scoring Model v1</div>'
        '<div style="background:rgba(0,0,0,.18);border-radius:10px;padding:.55rem .8rem;">'
        '<div><span class="score-legend-crit">&#11044; Critical</span>'
        '<span style="color:rgba(255,255,255,.85);"> &nbsp;&ge; 90 pts</span></div>'
        '<div><span class="score-legend-high">&#11044; High</span>'
        '<span style="color:rgba(255,255,255,.85);"> &nbsp;&ge; 60 pts</span></div>'
        '<div><span class="score-legend-med">&#11044; Medium</span>'
        '<span style="color:rgba(255,255,255,.85);"> &nbsp;&ge; 35 pts</span></div>'
        '<div><span class="score-legend-low">&#11044; Low</span>'
        '<span style="color:rgba(255,255,255,.85);"> &nbsp;&lt; 35 pts</span></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    mask = pd.Series(True, index=df.index)
    if sel_acct != "All":
        mask &= df["Account_Type"] == sel_acct
    if tiers:
        mask &= df["Risk_Tier"].isin(tiers)
    mask &= df["Churn_Score"].between(rng[0], rng[1])
    return df[mask].copy()

# ══════════════════════════════════════════════
# TAB 1 — RETENTION OVERVIEW
# ══════════════════════════════════════════════
def tab_overview(df):
    logo_header("Retention & Churn Overview")
    hr()

    total     = len(df)
    n_crit    = int((df["Risk_Tier"] == "Critical").sum())
    n_high    = int((df["Risk_Tier"] == "High").sum())
    aum_risk  = float(df["AUM_at_Risk"].sum())
    avg_sc    = float(df["Churn_Score"].mean())
    churn_pct = float((df["Churn_Status"] == "Yes").sum()) / total * 100 if total else 0.0

    # ── KPIs ──────────────────────────────────
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: kpi("Total Clients",   "{:,}".format(total),            "in current filter",         ACCENT)
    with c2: kpi("Critical Risk",   "{:,}".format(n_crit),           "immediate action required", RED)
    with c3: kpi("High Risk",       "{:,}".format(n_high),           "follow-up within 1 week",   AMBER)
    with c4: kpi("AUM at Risk",     "SAR {:.1f}M".format(aum_risk/1e6), "critical + high tiers",  RED)
    with c5: kpi("Avg Churn Score", "{:.0f}".format(avg_sc),         "churn rate {:.0f}%".format(churn_pct), PURPLE)

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

    # ── Row 1: Donut | AUM bar ─────────────────
    col1, col2 = st.columns(2)

    with col1:
        sec("Risk Tier Distribution")
        cnts = df["Risk_Tier"].value_counts().reindex(TORDER).fillna(0)
        fig = go.Figure(go.Pie(
            labels=list(cnts.index), values=list(cnts.values), hole=0.60,
            marker=dict(colors=[TIER_C[t] for t in cnts.index],
                        line=dict(color=WHITE, width=2)),
            textinfo="percent+label",
            textfont=dict(size=11, color=WHITE, family="Segoe UI"),
            hovertemplate="<b>%{label}</b><br>Clients: %{value}<br>%{percent}<extra></extra>",
        ))
        fig.add_annotation(
            text="<b>{}</b><br><span style='font-size:10px'>Clients</span>".format(total),
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=17, color=TEXT, family="Segoe UI"),
        )
        lay = base_layout(310, dict(l=10,r=10,t=10,b=42), legend=True)
        lay["legend"] = dict(orientation="h", x=0.05, y=-0.06,
                             font=dict(size=11, color=TEXT, family="Segoe UI"),
                             bgcolor="rgba(0,0,0,0)")
        fig.update_layout(**lay)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        sec("AUM Exposure by Risk Tier (SAR Millions)")
        aum_t = df.groupby("Risk_Tier")["Portfolio_Value"].sum().reindex(TORDER).fillna(0)
        fig2  = go.Figure(go.Bar(
            x=list(aum_t.index), y=[v/1e6 for v in aum_t.values],
            marker_color=[TIER_C[t] for t in aum_t.index], marker_line_width=0,
            text=["SAR {:.1f}M".format(v/1e6) for v in aum_t.values],
            textposition="outside",
            textfont=dict(size=11, color=TEXT, family="Segoe UI"),
            hovertemplate="<b>%{x}</b><br>SAR %{y:.1f}M<extra></extra>",
        ))
        lay2 = base_layout(310, dict(l=60,r=20,t=28,b=52))
        lay2["xaxis"] = xax("Risk Tier")
        lay2["yaxis"] = yax("SAR (Millions)", range=[0, float(aum_t.max())/1e6*1.22])
        fig2.update_layout(**lay2)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2: Churn rate | Score distribution ──
    col3, col4 = st.columns(2)

    with col3:
        sec("Churn Rate by Account Type")
        cr = df.groupby("Account_Type").apply(
            lambda x: float((x["Churn_Status"] == "Yes").sum()) / len(x) * 100
        ).sort_values(ascending=True)
        bar_c = [ACCT_COLORS.get(a, ACCENT) for a in cr.index]
        fig3 = go.Figure(go.Bar(
            x=list(cr.values), y=list(cr.index), orientation="h",
            marker_color=bar_c, marker_line_width=0,
            text=["{:.1f}%".format(v) for v in cr.values],
            textposition="outside",
            textfont=dict(size=11, color=TEXT, family="Segoe UI"),
            hovertemplate="<b>%{y}</b><br>Churn Rate: %{x:.1f}%<extra></extra>",
        ))
        lay3 = base_layout(290, dict(l=115,r=45,t=20,b=52))
        lay3["xaxis"] = xax("Churn Rate (%)", range=[0, 112], showgrid=True)
        lay3["yaxis"] = yax("", showgrid=False)
        fig3.update_layout(**lay3)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        sec("Churn Score Distribution by Risk Tier")
        fig4 = go.Figure()
        for tier in TORDER:
            sub = df.loc[df["Risk_Tier"] == tier, "Churn_Score"]
            if sub.empty: continue
            fig4.add_trace(go.Histogram(
                x=list(sub), name=tier, nbinsx=15,
                marker_color=TIER_C[tier], marker_line_width=0, opacity=0.85,
                hovertemplate="<b>" + tier + "</b><br>Score:%{x}<br>Count:%{y}<extra></extra>",
            ))
        for xv, lbl, col in [(35,"Medium",PURPLE),(60,"High",AMBER),(90,"Critical",RED)]:
            fig4.add_vline(x=xv, line_dash="dash", line_color=col, line_width=1.4,
                           annotation_text=lbl, annotation_position="top right",
                           annotation_font=dict(size=9, color=col, family="Segoe UI"))
        lay4 = base_layout(290, dict(l=58,r=20,t=32,b=52), legend=True)
        lay4["xaxis"]   = xax("Churn Score")
        lay4["yaxis"]   = yax("Number of Clients")
        lay4["barmode"] = "stack"
        fig4.update_layout(**lay4)
        st.plotly_chart(fig4, use_container_width=True)

    # ── Row 3: Avg score | AUM heatmap ─────────
    col5, col6 = st.columns(2)

    with col5:
        sec("Average Churn Score by Account Type")
        avg_sc2 = df.groupby("Account_Type")["Churn_Score"].mean().sort_values(ascending=False)
        bar_c2  = [ACCT_COLORS.get(a, ACCENT) for a in avg_sc2.index]
        fig5 = go.Figure(go.Bar(
            x=list(avg_sc2.index), y=list(avg_sc2.values),
            marker_color=bar_c2, marker_line_width=0,
            text=["{:.0f}".format(v) for v in avg_sc2.values],
            textposition="outside",
            textfont=dict(size=12, color=TEXT, family="Segoe UI"),
            hovertemplate="<b>%{x}</b><br>Avg Score: %{y:.1f}<extra></extra>",
        ))
        lay5 = base_layout(290, dict(l=58,r=20,t=20,b=52))
        lay5["xaxis"] = xax("Account Type")
        lay5["yaxis"] = yax("Average Churn Score", range=[0, float(avg_sc2.max())*1.25])
        fig5.update_layout(**lay5)
        st.plotly_chart(fig5, use_container_width=True)

    with col6:
        sec("AUM at Risk — Account Type x Trading Frequency (SAR M)")
        piv = (
            df.groupby(["Account_Type","Trading_Frequency"])["AUM_at_Risk"]
            .sum().unstack(fill_value=0) / 1e6
        )
        for col_n in ["High","Medium","Low"]:
            if col_n not in piv.columns:
                piv[col_n] = 0.0
        piv = piv[["High","Medium","Low"]]
        fig6 = go.Figure(go.Heatmap(
            z=piv.values.tolist(), x=piv.columns.tolist(), y=piv.index.tolist(),
            colorscale=[[0,GREENLT],[0.35,AMBERLT],[0.7,"#FECACA"],[1,RED]],
            text=[["SAR {:.1f}M".format(v) for v in row_] for row_ in piv.values],
            texttemplate="%{text}",
            textfont=dict(size=11, color=TEXT, family="Segoe UI"),
            hovertemplate="<b>%{y} | %{x}</b><br>%{text}<extra></extra>",
            showscale=True,
            colorbar=dict(
                title=dict(text="SAR M", font=dict(size=11, color=TEXT)),
                tickfont=dict(size=10, color=SUB), len=0.8,
            ),
        ))
        lay6 = base_layout(290, dict(l=115,r=80,t=20,b=52))
        lay6["xaxis"] = xax("Trading Frequency", showgrid=False)
        lay6["yaxis"] = yax("Account Type",       showgrid=False)
        fig6.update_layout(**lay6)
        st.plotly_chart(fig6, use_container_width=True)

    # ── Business Value ──────────────────────────
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    sec("What This Platform Delivers")
    BV = [
        ("🌡️","Early Warning",    "Identify clients cooling before full inactivity.",      ACCENT, ACCENTLT),
        ("⚖️","Severity Priority","Prioritise retention by tier, not equal treatment.",     AMBER,  AMBERLT),
        ("💼","AUM at Risk",      "Quantify exposed assets and product relationships.",     RED,    REDLT),
        ("🏷️","Reason Codes",     "Clear codes for RM campaigns and dashboards.",           PURPLE, PURPLELT),
        ("🔬","Model Foundation", "Transparent base ready for ML calibration.",            GREEN,  GREENLT),
    ]
    bv_cols = st.columns(5)
    for col, (icon,title,desc,fg,bg) in zip(bv_cols, BV):
        with col:
            st.markdown(
                '<div class="kpi" style="border-top:3px solid ' + fg + ';padding:.8rem 1rem;">'
                '<div style="font-size:1.3rem">' + icon + '</div>'
                '<div style="font-weight:700;font-size:.82rem;color:' + fg + ';margin:.3rem 0 .12rem">' + title + '</div>'
                '<div style="font-size:.72rem;color:' + SUB + ';line-height:1.45">' + desc + '</div>'
                '</div>',
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════
# TAB 2 — CLIENT RISK REGISTRY
# ══════════════════════════════════════════════
def tab_registry(df):
    logo_header("Client Risk Registry")
    hr()

    st.markdown(
        '<div class="callout" style="background:' + ACCENTLT + ';border:1px solid ' + _rgba(ACCENT,0.25) + ';color:#1e3a8a;">'
        '<b>&#128203; {:,} clients</b> match the current filter — sorted by Churn Score (highest first). '
        'Export below for CRM upload.</div>'.format(len(df)),
        unsafe_allow_html=True,
    )

    disp = df[[
        "Customer_ID","Account_Type","Age",
        "Portfolio_Value","Days_Since_Last_Trade",
        "Portfolio_Value_Drop_Pct","Trading_Frequency",
        "Churn_Score","Risk_Tier","Churn_Status",
    ]].sort_values("Churn_Score", ascending=False).copy()

    disp["Portfolio_Value"]          = disp["Portfolio_Value"].apply(lambda x: "SAR {:,.0f}".format(x))
    disp["Portfolio_Value_Drop_Pct"] = disp["Portfolio_Value_Drop_Pct"].apply(lambda x: "{:.1f}%".format(x))
    disp["Churn_Score"]              = disp["Churn_Score"].astype(int)

    def _ts(v):
        return "background-color:{};color:{};font-weight:700;border-radius:4px;".format(
            TIER_LT.get(v,"#eee"), TIER_C.get(v,TEXT)
        )
    def _ss(v):
        c = RED if v>=90 else AMBER if v>=60 else PURPLE if v>=35 else GREEN
        return "color:{};font-weight:800;".format(c)

    styled = (
        disp.style
        .pipe(_styler_map, _ts, subset=["Risk_Tier"])
        .pipe(_styler_map, _ss, subset=["Churn_Score"])
        .set_properties(**{"font-size":"0.8rem"})
    )
    st.dataframe(styled, use_container_width=True, height=500)
    csv = df.drop(columns=["Reason_Codes","AUM_at_Risk"]).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️  Export Scored Client List (CSV)", csv, "arc_churn_scored.csv", "text/csv")

# ══════════════════════════════════════════════
# TAB 3 — CLIENT DEEP DIVE
# ══════════════════════════════════════════════
def tab_deepdive(df):
    logo_header("Client Deep Dive")
    hr()

    ids = df.sort_values("Churn_Score", ascending=False)["Customer_ID"].astype(str).tolist()
    if not ids:
        st.warning("No clients in current filter.")
        return

    sel  = st.selectbox("Select Client ID (highest risk first)", ids, key="dd_sel")
    row  = df[df["Customer_ID"].astype(str) == sel].iloc[0]
    tier = str(row["Risk_Tier"])
    tc   = TIER_C[tier]
    tlt  = TIER_LT[tier]
    score = int(row["Churn_Score"])

    # Build header WITHOUT nested .format() to avoid tuple index error
    acct_age_str = str(row["Account_Type"]) + " &nbsp;&#183;&nbsp; Age " + str(int(row["Age"]))
    badge_str    = badge_html(tier)
    sbar_str     = score_bar_html(score)

    header_html = (
        '<div class="kpi" style="border-top:5px solid ' + tc + ';margin-bottom:.9rem;padding:1rem 1.3rem;">'
        '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.8rem;">'
        '<div>'
        '<div style="font-size:1.4rem;font-weight:900;color:' + TEXT + ';">' + sel + '</div>'
        '<div style="font-size:.82rem;color:' + SUB + ';">' + acct_age_str + '</div>'
        '</div>'
        '<div style="text-align:right;">'
        '<div style="font-size:2.5rem;font-weight:900;line-height:1;color:' + tc + ';">' + str(score) + '</div>'
        '<div style="margin-top:.22rem;">' + badge_str + ' <span style="font-size:.74rem;color:' + SUB + ';">Churn Score</span></div>'
        '</div>'
        '</div>'
        '<div style="margin-top:.85rem;">'
        '<div style="font-size:.65rem;color:' + SUB + ';font-weight:700;text-transform:uppercase;'
        'letter-spacing:.06em;margin-bottom:3px;">Score Gauge (0 – 130)</div>'
        + sbar_str +
        '</div></div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # KPIs
    m1,m2,m3,m4 = st.columns(4)
    with m1: kpi("Portfolio Value",  "SAR {:,.0f}".format(float(row["Portfolio_Value"])),   "",                  ACCENT)
    with m2: kpi("Days Since Trade", "{:.0f} days".format(float(row["Days_Since_Last_Trade"])), "of inactivity", AMBER)
    with m3: kpi("AUM Drop",        "{:.1f}%".format(float(row["Portfolio_Value_Drop_Pct"])),  "portfolio decline",RED)
    with m4: kpi("Service Calls",   "{:,}".format(int(row["Customer_Service_Calls"])),          "contacts logged", PURPLE)

    st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)

    # Reason codes
    sec("Churn Signal Reason Codes")
    REASON_MAP = [
        ("mitigant", GREEN,  GREENLT),
        ("270",      RED,    REDLT),
        ("exit",     RED,    REDLT),
        ("50%",      RED,    REDLT),
        ("90D",      AMBER,  AMBERLT),
        ("25%",      AMBER,  AMBERLT),
    ]
    pills_html = ""
    for reason in row["Reason_Codes"]:
        fg, bg = PURPLE, PURPLELT
        for kw, f, b in REASON_MAP:
            if kw.lower() in reason.lower():
                fg, bg = f, b
                break
        pills_html += pill(reason, fg, bg)
    if not pills_html:
        pills_html = pill("No significant signals", GREEN, GREENLT)
    st.markdown(pills_html, unsafe_allow_html=True)

    st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    # Radar
    with col_l:
        sec("Client vs Segment Benchmark (0–10)")
        seg  = df[df["Account_Type"] == row["Account_Type"]]
        cats = ["Days Inactive","AUM Drop %","Service Calls","Churn Score","Portfolio"]
        COLS = ["Days_Since_Last_Trade","Portfolio_Value_Drop_Pct",
                "Customer_Service_Calls","Churn_Score","Portfolio_Value"]

        def norm(val, col_name):
            lo_ = float(df[col_name].min()); hi_ = float(df[col_name].max())
            return round((float(val) - lo_) / (hi_ - lo_ + 1e-9) * 10, 2)

        cv = [norm(row[c], c) for c in COLS]
        sv = [norm(seg[c].mean(), c) for c in COLS]

        fig_r = go.Figure()
        fig_r.add_trace(go.Scatterpolar(
            r=sv+[sv[0]], theta=cats+[cats[0]], fill="toself",
            name=str(row["Account_Type"])+" Avg",
            line=dict(color=ACCENT, width=2),
            fillcolor=_rgba(ACCENT, 0.12),
        ))
        fig_r.add_trace(go.Scatterpolar(
            r=cv+[cv[0]], theta=cats+[cats[0]], fill="toself",
            name=sel,
            line=dict(color=tc, width=2.5),
            fillcolor=_rgba(tc, 0.18),
        ))
        fig_r.update_layout(
            polar=dict(
                bgcolor=WHITE,
                radialaxis=dict(visible=True, range=[0,10],
                                tickfont=dict(size=9,color=SUB,family="Segoe UI"),
                                gridcolor=BORDER),
                angularaxis=dict(tickfont=dict(size=10,color=TEXT,family="Segoe UI")),
            ),
            showlegend=True,
            legend=dict(orientation="h",y=-0.14,x=0.05,
                        font=dict(size=10,color=TEXT,family="Segoe UI"),
                        bgcolor="rgba(0,0,0,0)"),
            paper_bgcolor=WHITE, plot_bgcolor=WHITE,
            margin=dict(l=60,r=60,t=28,b=65), height=360,
            font=dict(family="Segoe UI",color=TEXT),
        )
        st.plotly_chart(fig_r, use_container_width=True)

    # Score contribution waterfall
    with col_r:
        sec("Score Contribution by Signal")
        RULE_MAP = {
            "No activity 30D":           ("Inactive 30D",       15),
            "No activity 90D":           ("Inactive 90D",       30),
            "Low engagement 60D":        ("Low Engagement 60D", 10),
            "Severe inactivity 90D":     ("Severe 90D",         20),
            "AUM drop >= 25%":           ("AUM Drop >=25%",     15),
            "AUM drop >= 50%":           ("AUM Drop >=50%",     25),
            "Low trading frequency":     ("Low Frequency",      15),
            "Near-zero assets":          ("Near-Zero Assets",   20),
            "Strong exit signal 270D+":  ("Exit Signal 270D+",  40),
            "Active Margin (mitigant)":  ("Margin Mitigant",   -15),
        }
        active = [(RULE_MAP[r][0], RULE_MAP[r][1])
                  for r in row["Reason_Codes"] if r in RULE_MAP]
        if active:
            labels = [a[0] for a in active]
            values = [a[1] for a in active]
            bar_colors = [GREEN if v<0 else RED if v>=25 else AMBER for v in values]
            fig_w = go.Figure(go.Bar(
                x=values, y=labels, orientation="h",
                marker_color=bar_colors, marker_line_width=0,
                text=["{}{}pts".format("+" if v>0 else "", v) for v in values],
                textposition="outside",
                textfont=dict(size=11, color=TEXT, family="Segoe UI"),
                hovertemplate="<b>%{y}</b><br>Points: %{x}<extra></extra>",
            ))
            x_lo = float(min(values)) * 1.6 - 4
            x_hi = float(max(values)) * 1.6 + 4
            lay_w = base_layout(360, dict(l=145,r=55,t=20,b=52))
            lay_w["xaxis"] = xax("Score Points", range=[x_lo, x_hi])
            lay_w["yaxis"] = yax("", showgrid=False, autorange="reversed")
            fig_w.update_layout(**lay_w)
            fig_w.add_vline(x=0, line_color=BORDER, line_width=1.5)
            st.plotly_chart(fig_w, use_container_width=True)
        else:
            st.info("No scoring rules triggered for this client.")

    # RM recommendation
    sec("Relationship Manager Recommendation")
    RM_REC = {
        "Critical": (RED,    REDLT,    "🚨 Immediate outreach — Senior RM call within 48 hours. Prepare a retention offer: fee waiver or complimentary portfolio advisory session."),
        "High":     (AMBER,  AMBERLT,  "⚠️ Schedule RM follow-up within 1 week. Share personalised market insights and review product mix for upgrade opportunities."),
        "Medium":   (PURPLE, PURPLELT, "📋 Add to next engagement campaign cycle. Digital nudge via app/email with portfolio recap and available services."),
        "Low":      (GREEN,  GREENLT,  "✅ Monitor via standard dashboard. No immediate action — maintain routine engagement cadence."),
    }
    fg, bg, msg = RM_REC[tier]
    st.markdown(
        '<div style="background:' + bg + ';border-left:5px solid ' + fg + ';'
        'padding:.9rem 1.2rem;border-radius:0 10px 10px 0;'
        'color:' + fg + ';font-weight:600;font-size:.88rem;line-height:1.5;">'
        + msg + '</div>',
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════
# TAB 4 — SCORING MODEL
# ══════════════════════════════════════════════
def tab_model(df):
    logo_header("Churn Scoring Model — Version 1")
    hr()

    st.markdown(
        '<div class="callout" style="background:' + ACCENTLT + ';border:1px solid ' + _rgba(ACCENT,0.3) + ';color:#1e3a8a;">'
        '<b>Model Philosophy —</b> Version 1 uses a <b>transparent, rule-based scoring</b> approach. '
        'Every point is traceable to a business condition. This creates a calibration-ready foundation '
        'upgradeable to a predictive ML model after backtesting.</div>',
        unsafe_allow_html=True,
    )

    sec("Scoring Rules")
    RULES = [
        ("No activity 30D",           "+15", "Light inactivity warning.",                            AMBER,  AMBERLT),
        ("No activity 90D",           "+30", "Material inactivity concern.",                          RED,    REDLT),
        ("No login / engagement 60D", "+10", "Lower digital engagement signal.",                      AMBER,  AMBERLT),
        ("No login / engagement 90D", "+20", "Severe digital inactivity.",                            RED,    REDLT),
        ("AUM drop 30D >= 25%",       "+15", "Recent asset reduction.",                               AMBER,  AMBERLT),
        ("AUM drop 90D >= 50%",       "+25", "Material asset reduction.",                             RED,    REDLT),
        ("Product abandonment",       "+15", "Low trading frequency signals disengagement.",          PURPLE, PURPLELT),
        ("Near-zero assets",          "+20", "Limited remaining portfolio value (bottom 5%).",        RED,    REDLT),
        ("Strong exit signal 270D+",  "+40", "Major exit-style behaviour — extended inactivity.",     RED,    REDLT),
        ("Active Margin Trading",     "−15", "Mitigates false positives for strategic accounts.",     GREEN,  GREENLT),
    ]

    hdr = (
        '<div style="display:grid;grid-template-columns:2.1fr .5fr 2.9fr;'
        'background:' + BG + ';border:1px solid ' + BORDER + ';border-radius:10px 10px 0 0;overflow:hidden;">'
        '<div style="padding:.48rem 1rem;font-size:.66rem;font-weight:700;'
        'text-transform:uppercase;letter-spacing:.06em;color:' + SUB + ';">Condition</div>'
        '<div style="padding:.48rem .5rem;font-size:.66rem;font-weight:700;'
        'text-transform:uppercase;letter-spacing:.06em;color:' + SUB + ';">Points</div>'
        '<div style="padding:.48rem 1rem;font-size:.66rem;font-weight:700;'
        'text-transform:uppercase;letter-spacing:.06em;color:' + SUB + ';">Business Logic</div>'
        '</div>'
    )
    rows_html = ""
    for i, (cond, pts, logic, fg, bg) in enumerate(RULES):
        br = "border-radius:0 0 10px 10px;" if i == len(RULES)-1 else ""
        rows_html += (
            '<div style="display:grid;grid-template-columns:2.1fr .5fr 2.9fr;'
            'background:' + WHITE + ';border:1px solid ' + BORDER + ';border-top:none;' + br + '">'
            '<div style="padding:.54rem 1rem;font-size:.81rem;font-weight:500;">' + cond + '</div>'
            '<div style="padding:.54rem .5rem;">'
            '<span style="background:' + bg + ';color:' + fg + ';padding:2px 10px;'
            'border-radius:20px;font-size:.78rem;font-weight:700;">' + pts + '</span>'
            '</div>'
            '<div style="padding:.54rem 1rem;font-size:.79rem;color:' + SUB + ';">' + logic + '</div>'
            '</div>'
        )
    st.markdown(hdr + rows_html, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    sec("Risk Tier Thresholds")
    THRESH = [
        ("Critical",">=90",  "Immediate RM action — 48 hrs",  RED,    REDLT),
        ("High",    "60-89", "Follow-up within 1 week",        AMBER,  AMBERLT),
        ("Medium",  "35-59", "Next campaign cycle",            PURPLE, PURPLELT),
        ("Low",     "< 35",  "Standard monitoring",            GREEN,  GREENLT),
    ]
    t_cols = st.columns(4)
    for col, (tier,rng,desc,fg,bg) in zip(t_cols, THRESH):
        with col:
            st.markdown(
                '<div class="kpi" style="border-top:4px solid ' + fg + ';text-align:center;padding:.9rem 1rem;">'
                '<div style="font-size:1.6rem;font-weight:900;color:' + fg + ';">' + rng + '</div>'
                '<div style="font-weight:700;font-size:.86rem;color:' + TEXT + ';margin:.2rem 0;">' + tier + '</div>'
                '<div style="font-size:.72rem;color:' + SUB + ';">' + desc + '</div>'
                '</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:.9rem'></div>", unsafe_allow_html=True)
    sec("Score Distribution Across Portfolio")
    fig_h = go.Figure()
    for tier in TORDER:
        sub = df.loc[df["Risk_Tier"] == tier, "Churn_Score"]
        if sub.empty: continue
        fig_h.add_trace(go.Histogram(
            x=list(sub), name=tier, nbinsx=22,
            marker_color=TIER_C[tier], marker_line_width=0, opacity=0.85,
            hovertemplate="<b>" + tier + "</b><br>Score:%{x}<br>Count:%{y}<extra></extra>",
        ))
    for xv, lbl, col in [(35,"Medium",PURPLE),(60,"High",AMBER),(90,"Critical",RED)]:
        fig_h.add_vline(x=xv, line_dash="dash", line_color=col, line_width=1.4,
                        annotation_text=lbl, annotation_position="top right",
                        annotation_font=dict(size=9, color=col, family="Segoe UI"))
    lay_h = base_layout(340, dict(l=58,r=20,t=32,b=52), legend=True)
    lay_h["xaxis"]   = xax("Churn Score")
    lay_h["yaxis"]   = yax("Number of Clients")
    lay_h["barmode"] = "stack"
    fig_h.update_layout(**lay_h)
    st.plotly_chart(fig_h, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 5 — SEGMENT ANALYTICS
# ══════════════════════════════════════════════
def tab_segments(df):
    logo_header("Segment Analytics")
    hr()

    col1, col2 = st.columns(2)

    with col1:
        sec("Inactivity vs AUM Drop — Churn Signal Map")
        fig_sc = go.Figure()
        for tier in TORDER:
            sub = df[df["Risk_Tier"] == tier]
            if sub.empty: continue
            fig_sc.add_trace(go.Scatter(
                x=list(sub["Days_Since_Last_Trade"]),
                y=list(sub["Portfolio_Value_Drop_Pct"]),
                mode="markers", name=tier,
                marker=dict(
                    size=[float(s)/8+5 for s in sub["Churn_Score"]],
                    color=TIER_C[tier], opacity=0.75,
                    line=dict(width=0.5, color=WHITE),
                ),
                customdata=sub[["Customer_ID","Account_Type","Churn_Score"]].values.tolist(),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>Type: %{customdata[1]}<br>"
                    "Days Inactive: %{x}<br>AUM Drop: %{y:.1f}%<br>"
                    "Score: %{customdata[2]}<extra></extra>"
                ),
            ))
        fig_sc.add_vline(x=90, line_dash="dot", line_color=SUB, line_width=1.1, opacity=0.5)
        fig_sc.add_hline(y=25, line_dash="dot", line_color=SUB, line_width=1.1, opacity=0.5)
        fig_sc.add_annotation(x=310, y=37, text="High Risk Zone", showarrow=False,
                               font=dict(size=10, color=RED, family="Segoe UI"))
        lay_sc = base_layout(340, dict(l=60,r=20,t=28,b=52), legend=True)
        lay_sc["xaxis"] = xax("Days Since Last Trade")
        lay_sc["yaxis"] = yax("AUM Drop (%)")
        fig_sc.update_layout(**lay_sc)
        st.plotly_chart(fig_sc, use_container_width=True)

    with col2:
        sec("Client Count by Account Type & Risk Tier")
        ct = df.groupby(["Account_Type","Risk_Tier"]).size().reset_index(name="Count")
        fig_ct = go.Figure()
        for tier in TORDER:
            sub = ct[ct["Risk_Tier"] == tier]
            if sub.empty: continue
            fig_ct.add_trace(go.Bar(
                x=list(sub["Account_Type"]), y=list(sub["Count"]),
                name=tier, marker_color=TIER_C[tier], marker_line_width=0,
                hovertemplate="<b>" + tier + "</b><br>%{x}<br>Clients: %{y}<extra></extra>",
            ))
        lay_ct = base_layout(340, dict(l=58,r=20,t=28,b=52), legend=True)
        lay_ct["xaxis"]   = xax("Account Type")
        lay_ct["yaxis"]   = yax("Number of Clients")
        lay_ct["barmode"] = "stack"
        fig_ct.update_layout(**lay_ct)
        st.plotly_chart(fig_ct, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        sec("Avg Days Inactive by Account Type & Risk Tier")
        avg_d = df.groupby(["Account_Type","Risk_Tier"])["Days_Since_Last_Trade"].mean().reset_index()
        fig_ad = go.Figure()
        for tier in TORDER:
            sub = avg_d[avg_d["Risk_Tier"] == tier]
            if sub.empty: continue
            fig_ad.add_trace(go.Bar(
                x=list(sub["Account_Type"]), y=list(sub["Days_Since_Last_Trade"]),
                name=tier, marker_color=TIER_C[tier], marker_line_width=0,
                text=["{:.0f}d".format(v) for v in sub["Days_Since_Last_Trade"]],
                textposition="inside",
                textfont=dict(size=9, color=WHITE, family="Segoe UI"),
                hovertemplate="<b>" + tier + "</b><br>%{x}<br>Avg Days: %{y:.0f}<extra></extra>",
            ))
        lay_ad = base_layout(320, dict(l=60,r=20,t=28,b=52), legend=True)
        lay_ad["xaxis"]   = xax("Account Type")
        lay_ad["yaxis"]   = yax("Avg Days Since Last Trade")
        lay_ad["barmode"] = "group"
        fig_ad.update_layout(**lay_ad)
        st.plotly_chart(fig_ad, use_container_width=True)

    with col4:
        sec("Portfolio Value Distribution by Risk Tier (SAR M)")
        fig_pv = go.Figure()
        for tier in TORDER:
            sub = df.loc[df["Risk_Tier"] == tier, "Portfolio_Value"] / 1e6
            if sub.empty: continue
            fig_pv.add_trace(go.Box(
                y=list(sub), name=tier,
                marker_color=TIER_C[tier],
                line=dict(color=TIER_C[tier], width=2),
                fillcolor=_rgba(TIER_C[tier], 0.13),
                boxmean=True,
                hovertemplate="<b>" + tier + "</b><br>SAR %{y:.2f}M<extra></extra>",
            ))
        lay_pv = base_layout(320, dict(l=60,r=20,t=28,b=52))
        lay_pv["xaxis"]      = xax("Risk Tier")
        lay_pv["yaxis"]      = yax("Portfolio Value (SAR M)")
        lay_pv["showlegend"] = False
        fig_pv.update_layout(**lay_pv)
        st.plotly_chart(fig_pv, use_container_width=True)

    sec("AUM Concentration — Churn Score vs Portfolio Value  (bubble size = AUM drop %)")
    fig_bub = go.Figure()
    for tier in TORDER:
        sub = df[df["Risk_Tier"] == tier]
        if sub.empty: continue
        fig_bub.add_trace(go.Scatter(
            x=list(sub["Churn_Score"]),
            y=[float(v)/1e6 for v in sub["Portfolio_Value"]],
            mode="markers", name=tier,
            marker=dict(
                size=[float(p)/2+5 for p in sub["Portfolio_Value_Drop_Pct"]],
                color=TIER_C[tier], opacity=0.70,
                line=dict(width=0.5, color=WHITE),
            ),
            customdata=sub[["Customer_ID","Account_Type","Portfolio_Value_Drop_Pct"]].values.tolist(),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>Type: %{customdata[1]}<br>"
                "Score: %{x}<br>Portfolio: SAR %{y:.2f}M<br>"
                "AUM Drop: %{customdata[2]:.1f}%<extra></extra>"
            ),
        ))
    lay_bub = base_layout(380, dict(l=60,r=20,t=32,b=52), legend=True)
    lay_bub["xaxis"] = xax("Churn Score")
    lay_bub["yaxis"] = yax("Portfolio Value (SAR Millions)")
    fig_bub.update_layout(**lay_bub)
    st.plotly_chart(fig_bub, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 6 — RM ACTION CENTRE
# ══════════════════════════════════════════════
def tab_rm(df):
    logo_header("RM Action Centre")
    hr()

    st.markdown(
        '<div class="callout" style="background:' + AMBERLT + ';border:1px solid ' + _rgba(AMBER,0.3) + ';color:#78350f;">'
        '<b>&#128161; How to use:</b> Filter by tier or account type to build targeted RM campaign lists. '
        'Priority clients sorted by Churn Score descending. Export for CRM upload.</div>',
        unsafe_allow_html=True,
    )

    for tier, fg, bg, msg in [
        ("Critical", RED,    REDLT,    "&#128222; Senior RM call within 48 hours"),
        ("High",     AMBER,  AMBERLT,  "&#128197; RM follow-up within 1 week"),
        ("Medium",   PURPLE, PURPLELT, "&#128140; Add to next digital campaign"),
    ]:
        cnt = int((df["Risk_Tier"] == tier).sum())
        aum = float(df.loc[df["Risk_Tier"] == tier, "Portfolio_Value"].sum())
        if cnt == 0: continue
        st.markdown(
            '<div style="background:' + bg + ';border-left:5px solid ' + fg + ';'
            'border-radius:0 10px 10px 0;padding:.68rem 1.1rem;margin:.3rem 0;'
            'display:flex;justify-content:space-between;align-items:center;">'
            '<div>'
            '<span style="font-weight:800;color:' + fg + ';font-size:.88rem;">' + tier + '</span>'
            '<span style="color:' + SUB + ';font-size:.78rem;margin-left:.8rem;">' + msg + '</span>'
            '</div>'
            '<div style="text-align:right;">'
            '<div style="font-weight:800;color:' + fg + ';font-size:.88rem;">SAR {:.1f}M AUM</div>'.format(aum/1e6) +
            '<div style="font-size:.72rem;color:' + SUB + ';">{:,} clients</div>'.format(cnt) +
            '</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:.85rem'></div>", unsafe_allow_html=True)

    cl, cr = st.columns(2)

    with cl:
        sec("Action Queue Size by Tier")
        tc_s = df["Risk_Tier"].value_counts().reindex(TORDER).fillna(0)
        fig_q = go.Figure(go.Bar(
            x=list(tc_s.index), y=list(tc_s.values),
            marker_color=[TIER_C[t] for t in tc_s.index], marker_line_width=0,
            text=[str(int(v)) for v in tc_s.values], textposition="outside",
            textfont=dict(size=13, color=TEXT, family="Segoe UI"),
            hovertemplate="<b>%{x}</b><br>Clients: %{y}<extra></extra>",
        ))
        lay_q = base_layout(265, dict(l=58,r=20,t=20,b=52))
        lay_q["xaxis"] = xax("Risk Tier")
        lay_q["yaxis"] = yax("Number of Clients", range=[0, float(tc_s.max())*1.28])
        fig_q.update_layout(**lay_q)
        st.plotly_chart(fig_q, use_container_width=True)

    with cr:
        sec("AUM at Risk by Tier (SAR Millions)")
        aum_r = df.groupby("Risk_Tier")["AUM_at_Risk"].sum().reindex(TORDER).fillna(0)
        fig_ar = go.Figure(go.Bar(
            x=list(aum_r.index), y=[v/1e6 for v in aum_r.values],
            marker_color=[TIER_C[t] for t in aum_r.index], marker_line_width=0,
            text=["SAR {:.1f}M".format(v/1e6) for v in aum_r.values], textposition="outside",
            textfont=dict(size=11, color=TEXT, family="Segoe UI"),
            hovertemplate="<b>%{x}</b><br>SAR %{y:.1f}M<extra></extra>",
        ))
        lay_ar = base_layout(265, dict(l=60,r=20,t=20,b=52))
        lay_ar["xaxis"] = xax("Risk Tier")
        lay_ar["yaxis"] = yax("SAR (Millions)", range=[0, float(aum_r.max())/1e6*1.25])
        fig_ar.update_layout(**lay_ar)
        st.plotly_chart(fig_ar, use_container_width=True)

    st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)
    sec("Campaign Client List")
    f1, f2 = st.columns(2)
    with f1:
        tier_f = st.selectbox("Filter by Risk Tier",    ["All"]+TORDER, key="rm_tier")
    with f2:
        acct_opts = ["All"]+sorted(df["Account_Type"].unique().tolist())
        acct_f = st.selectbox("Filter by Account Type", acct_opts,      key="rm_acct")

    rm = df.copy()
    if tier_f != "All": rm = rm[rm["Risk_Tier"] == tier_f]
    if acct_f != "All": rm = rm[rm["Account_Type"] == acct_f]

    rm_d = rm[[
        "Customer_ID","Account_Type","Risk_Tier","Churn_Score",
        "Portfolio_Value","Days_Since_Last_Trade",
        "Portfolio_Value_Drop_Pct","Customer_Service_Calls",
    ]].sort_values("Churn_Score", ascending=False).copy()
    rm_d["Portfolio_Value"]          = rm_d["Portfolio_Value"].apply(lambda x: "SAR {:,.0f}".format(x))
    rm_d["Portfolio_Value_Drop_Pct"] = rm_d["Portfolio_Value_Drop_Pct"].apply(lambda x: "{:.1f}%".format(x))

    def _ts(v):
        return "background-color:{};color:{};font-weight:700;".format(
            TIER_LT.get(v,"#eee"), TIER_C.get(v,TEXT))

    st.dataframe(_styler_map(rm_d.style, _ts, subset=["Risk_Tier"]),
                 use_container_width=True, height=430)

    csv_rm = (
        rm[["Customer_ID","Account_Type","Risk_Tier","Churn_Score",
            "Portfolio_Value","Days_Since_Last_Trade"]]
        .sort_values("Churn_Score", ascending=False)
        .to_csv(index=False).encode("utf-8")
    )
    st.download_button(
        "⬇️  Export RM Campaign List (CSV)", csv_rm,
        "arc_rm_{}.csv".format(tier_f.lower()), "text/csv",
    )

# ══════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════
def main():
    DATA = "Alrajhi_Capital_Churn_Demo_Data.xlsx"
    if not os.path.exists(DATA):
        st.error("Data file not found: `{}` — place it in the same folder as this script.".format(DATA))
        st.stop()

    with st.spinner("Loading and scoring client portfolio…"):
        full_df = load_data(DATA)

    with st.sidebar:
        logo_header("Retention Intelligence")
        st.markdown(
            '<div style="font-size:.69rem;color:rgba(255,255,255,.7);margin-top:.05rem;">'
            'Scoring Model v1 &nbsp;&#183;&nbsp; {:,} clients loaded</div>'.format(len(full_df)),
            unsafe_allow_html=True,
        )

    fdf = sidebar_filters(full_df)
    if fdf.empty:
        st.warning("No clients match the current filters — adjust sidebar selections.")
        st.stop()

    t1,t2,t3,t4,t5,t6 = st.tabs([
        "📊  Retention Overview",
        "📋  Client Risk Registry",
        "🔍  Client Deep Dive",
        "⚙️  Scoring Model",
        "📈  Segment Analytics",
        "📞  RM Action Centre",
    ])
    with t1: tab_overview(fdf)
    with t2: tab_registry(fdf)
    with t3: tab_deepdive(fdf)
    with t4: tab_model(fdf)
    with t5: tab_segments(fdf)
    with t6: tab_rm(fdf)

if __name__ == "__main__":
    main()
