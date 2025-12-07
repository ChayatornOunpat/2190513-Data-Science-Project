import pandas as pd
import plotly.express as px
import streamlit as st



st.set_page_config(
    page_title="University-Industry Alignment",
    layout="wide",

)



st.markdown("""
<style>
.market-map-font {
    font-family: Verdana, sans-serif !important;
    font-weight: 700 !important;   /* Bold */
}
</style>
""", unsafe_allow_html=True)

hide_x_button_css = """
<style>

[data-testid="baseButton-header"] {
    display: none !important;
}

</style>
"""


st.markdown(hide_x_button_css, unsafe_allow_html=True)

# =====================================================================
# DATA LOADING & PROCESSING (UPDATED)
# =====================================================================
@st.cache_data
def load_data():
    # Load your main dashboard data
    df_main = pd.read_csv("withZ.csv")
    
    # Load the new details file
    
    df_details = pd.read_csv("grouped_nonnormalized_complete.csv")
    
        
    return df_main, df_details

df_raw, dff = load_data()

# --- HELPER: NAME NORMALIZER ---
# This helps match "Delta Electronics" with "Delta Electronics (Thailand) PCL"
def normalize_name(name):
    if not isinstance(name, str): return ""
    # Lowercase and remove common corporate suffixes to improve matching chances
    name = name.lower()
    for bad_str in ["public company limited", "pcl", "limited", "company", "(thailand)", "inc.", "corp."]:
        name = name.replace(bad_str, "")
    return name.strip()

# --- CREATE FAST LOOKUP DICTIONARY ---
# Structure: { "normalized_name": [ {title:..., value:..., z:...}, ... ] }
top_items_map = {}

if not dff.empty:
    # 1. Sort by value descending so the best papers come first
    dff_sorted = dff.sort_values(by="value", ascending=False)
    
    # 2. Group by company and store the top 3
    for company_name, group in dff_sorted.groupby("company"):
        # Get top 3 rows
        top_rows = group[['title', 'value', 'z_by_company']].head(3).to_dict('records')
        
        # Store under the normalized name for easier lookup
        clean_key = normalize_name(company_name)
        top_items_map[clean_key] = top_rows
        
        # Also store under the exact original name just in case
        top_items_map[company_name] = top_rows
# sidebar

with st.sidebar:
    st.header("Dashboard Controls")
    st.markdown("Improve visibility using filters below.")
    
    # sector filter
    sectors = ["All Sectors"] + sorted(df_raw["sector"].unique())
    selected_sector = st.selectbox("Filter by Sector", sectors)

    # dynamic industry filter
    if selected_sector == "All Sectors":
        industries = ["All Industries"] + sorted(df_raw["industry"].unique())
    else:
        industries = ["All Industries"] + sorted(
            df_raw[df_raw["sector"] == selected_sector]["industry"].unique()
        )

    selected_industry = st.selectbox("Filter by Industry", industries)

    # search bar
    search = st.text_input("Search Company", placeholder="Type company name...")

    st.divider()

    st.markdown("#### Download Filtered Data")
    st.download_button(
        label="Download CSV",
        data=df_raw.to_csv(index=False),
        file_name="alignment_data.csv",
        mime="text/csv"
    )

# for filtering
df_viz = df_raw.copy()

if selected_sector != "All Sectors":
    df_viz = df_viz[df_viz["sector"] == selected_sector]

if selected_industry != "All Industries":
    df_viz = df_viz[df_viz["industry"] == selected_industry]

if search.strip() != "":
    df_viz = df_viz[df_viz["company_name"].str.contains(search, case=False)]

st.title("University-Industry Alignment Dashboard")
st.caption("Understanding how academic research aligns with market economic value.")
st.divider()

# all cols:
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Companies Analyzed", f"{len(df_viz)}")

with col2:
    st.metric(                                  
        "Avg Alignment Score",
        f"{df_viz['total_alignment_score'].mean():.2f}"
    )

with col3:
    st.metric(
        "Total Market Value",
        f"฿{df_viz['market_cap'].sum():,.0f}"
    )

with col4:
    st.metric(
        "High Alignment Companies (Z > 1)",
        len(df_viz[df_viz["total_alignment_score"] > 1])
    )

st.divider()

# tab bar
tab1, tab2, tab3 = st.tabs([
    "Market Map",
    "Strategic Gap",
    "Data Table"
])

# =====================================================================
# SHARED HOVER LOGIC (Moved outside tabs so both can use it)
# =====================================================================

# 1. HELPER: FORMAT ROW
def format_row(c1, c2, c3, color, is_bold=False):
    # Column Widths
    w1, w2, w3 = 16, 8, 8 
    
    # Truncate text
    c1 = str(c1)[:w1]
    c2 = str(c2)[:w2]
    c3 = str(c3)[:w3]
    
    # Create aligned string with HTML spaces
    row_str = f"{c1:<{w1}} {c2:^{w2}} {c3:>{w3}}".replace(" ", "&nbsp;")
    
    weight = "bold" if is_bold else "normal"
    return f"<span style='color:{color}; font-weight:{weight};'>{row_str}</span><br>"

# 2. GENERATE HOVER HTML
def build_hover_content(row):
    # --- A. HEADER ---
    header_text = row['sector'].upper()[:25] 
    html = format_row(header_text, "", "", "#1A237E", is_bold=True)
    html += "<span style='font-size:4px'>&nbsp;</span><br>" 

    # --- B. COMPANY ROW ---
    price = f"฿{row['market_cap']/1e9:.0f}B"
    pct = f"{row['total_alignment_score']:.2f}"
    
    # Color Logic
    main_color = "#2E7D32" if row['total_alignment_score'] > 0 else "#D32F2F"
    
    html += format_row("Company Name", "Market Cap", "Align. Val", "#000000")
    html += format_row(row['company_name'], price, f"{pct}", main_color, is_bold=True)
    html += "<span style='font-size:4px'>&nbsp;</span><br>"
    
    # --- C. TOP 3 PAPERS LOOKUP ---
    items = top_items_map.get(row['company_name'])
    
    # Fallback to normalized name if exact match fails
    if not items:
        clean_name = normalize_name(row['company_name'])
        items = top_items_map.get(clean_name, [])
    
    html += format_row("Paper Title", "Val", "Z-Scr", "#999999")

    # --- D. RENDER ITEMS ---
    if items:
        for item in items:
            title = str(item.get('title', '-'))
            val = f"{item.get('value', 0):.2f}"
            z_val = f"{item.get('z_by_company', 0):.2f}"
            html += format_row(title, val, z_val, "black")
            
        # Pad with empty rows if fewer than 3 items found
        for _ in range(3 - len(items)):
             html += format_row("", "", "", "white")
    else:
        # Fallback if no match found
        html += format_row("No Data Found", "-", "-", "#999")
        html += format_row("", "", "", "white")
        html += format_row("", "", "", "white")

    return html

# 3. APPLY GLOBALLY (Before Tabs render)
df_viz['hover_content'] = df_viz.apply(build_hover_content, axis=1)


# =====================================================================
# TAB 1: MARKET MAP
# =====================================================================
with tab1:
    st.subheader(f"Market Alignment Map: {selected_sector}")
    st.caption("Box Size → Market Cap | Color → Research Fit (Z-Score)")

    red_green_px_scale = [(0, 'red'), (0.5, 'white'), (1, 'green')]

    import textwrap

    def wrap_labels(text, width=15):
        """Inserts <br> every 'width' characters to wrap text."""
        return "<br>".join(textwrap.wrap(str(text), width=width))

    # Create a new column specifically for the Chart Labels
    df_viz['wrapped_name'] = df_viz['company_name'].apply(lambda x: wrap_labels(x, width=22))

    fig_treemap = px.treemap(
        df_viz,
        path=[px.Constant("All Sectors"), "sector", "industry", "wrapped_name"],
        values="market_cap",
        color="total_alignment_score",
        color_continuous_scale=red_green_px_scale,
        color_continuous_midpoint=df_viz["total_alignment_score"].mean(),
        custom_data=['hover_content']
    )
    fig_treemap.update_traces(
        hovertemplate="%{customdata[0]}<extra></extra>",
        textposition="middle center",       # 1. Centers the text
        texttemplate="<b>%{label}</b>",     # 2. Bolds the text (HTML tags)
        textfont=dict(                      # 3. Sets Font Size & Family
            family="Verdana",
            size=20,  
            color="black" 
        )
    )

    fig_treemap.update_layout(
        margin=dict(t=20, l=10, r=10, b=80),
        height=600,
        hoverlabel=dict(
            bgcolor="white",             
            bordercolor="#1A237E",       
            font_family="Consolas, 'Courier New', monospace", 
            font_size=13,
            align="left"
        ),
        coloraxis_colorbar=dict(
            title="Alignment Score",
            orientation="h",
            yanchor="top",
            y=-0.05,
            thickness=15
        )
    )

    st.plotly_chart(fig_treemap, use_container_width=True)


# =====================================================================
# TAB 2: STRATEGIC GAP (UPDATED WITH CUSTOM HOVER)
# =====================================================================
with tab2:
    st.subheader("Strategic Gap Analysis")
    st.caption("Top-Right Quadrant = Strong Research + High Market Value")
    
    fig_scatter = px.scatter(
        df_viz,
        x="total_alignment_score",
        y="market_cap",
        size="market_cap",
        color="industry",
        # CHANGED: Use custom_data instead of standard hover_name
        custom_data=['hover_content'],
        log_y=True,
        labels={
            "total_alignment_score": "Research Alignment (Z-Score)",
            "market_cap": "Market Cap (Log Scale)"
        },
        template="plotly_white"
    )

    # NEW: Apply the same styling as Tab 1
    fig_scatter.update_traces(
        hovertemplate="%{customdata[0]}<extra></extra>"
    )

    fig_scatter.update_layout(
        legend=dict(
            orientation="v",
            y=0.5,
            x=1.15,
            xanchor="left",
            yanchor="middle"
        ),
        font=dict(
            family="Inter, sans-serif",
            size=15
        ),
        # NEW: Hover Label Styling
        hoverlabel=dict(
            bgcolor="white",             
            bordercolor="#1A237E",       
            font_family="Consolas, 'Courier New', monospace", 
            font_size=13,
            align="left"
        ),
        height=600
    )

    median_score = df_viz["total_alignment_score"].median()
    median_cap = df_viz["market_cap"].median()

    fig_scatter.add_vline(
        x=median_score,
        line_dash="dash",
        line_color="gray",
        annotation_text="Median Score"
    )

    fig_scatter.add_hline(
        y=median_cap,
        line_dash="dash",
        line_color="gray",
        annotation_text="Median Cap"
    )

    st.plotly_chart(fig_scatter, use_container_width=True)


with tab3:
    st.subheader("Underlying Data (Filtered)")
    st.caption("Sorted by Alignment Score")

    st.dataframe(
        df_viz[[
            "company_name",
            "sector",
            "industry",
            "market_cap",
            "total_alignment_score"
        ]].sort_values("total_alignment_score", ascending=False),
        use_container_width=True
    )
# ============================================================
# FIXED: CUSTOM 5-ROW HOVER BOX — SAFE (no f-string CSS parsing error)
# ============================================================

def custom_hover_box(
    title_text="COMMUNICATION SERVICES – INTERNET CONTENT & INFORMATION",
    title_color="white",
    title_bg="#1A237E",
    # rows: 4 rows after the title, each row is (left, middle, right, bg_color, text_color, text_size)
    rows=[
        ("GOOGL", "321.27", "+1.15%", "#2E7D32", "white", "20px"),
        ("META", "673.42", "+1.80%", "white", "black", "18px"),
        ("MTCH", "34.52", "+1.89%", "white", "black", "18px"),
        ("ROW4", "Mid", "Right", "white", "black", "18px"),
    ]
):
    # Ensure rows has exactly 4 items (after the title) to give total 5 rows (1 title + 4 data rows)
    if len(rows) < 4:
        # pad with empty rows if user passed fewer
        rows = rows + [("", "", "", "white", "black", "18px")] * (4 - len(rows))
    elif len(rows) > 4:
        rows = rows[:4]

    # CSS as a plain string (no f-string) so { } in CSS don't break Python parsing
    css = """
    <style>
    .hover-wrapper {
        position: relative;
        display: inline-block;
    }
    .hover-box {
        visibility: hidden;
        opacity: 0;
        transition: 0.25s ease-in-out;
        position: absolute;
        top: 0;
        left: 120%;
        width: 430px;
        background: #fff;
        border-radius: 6px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.35);
        z-index: 999;
        font-family: Verdana, sans-serif;
    }
    .hover-wrapper:hover .hover-box {
        visibility: visible;
        opacity: 1;
    }
    .hover-title {
        padding: 12px 15px;
        font-size: 18px;
        font-weight: 700;
        border-bottom: 1px solid #ccc;
    }
    .hover-row {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        padding: 10px 15px;
        border-bottom: 1px solid #e5e5e5;
        font-weight: 600;
        font-family: Verdana, sans-serif;
    }
    </style>
    """

    # Title HTML (we'll inject background and color via inline styles)
    title_html = (
        '<div class="hover-title" '
        f'style="background:{title_bg}; color:{title_color};">'
        f'{title_text}'
        '</div>'
    )

    # Build rows html safely using a loop (we can use f-strings here)
    rows_html = ""
    for left, mid, right, bg, tc, ts in rows:
        # protect empty strings
        left = left or ""
        mid = mid or ""
        right = right or ""
        bg = bg or "white"
        tc = tc or "black"
        ts = ts or "16px"

        # Each row uses inline styles (no braces in the template)
        rows_html += (
            f'<div class="hover-row" style="background:{bg}; color:{tc}; font-size:{ts};">'
            f'<div style="overflow:hidden; text-overflow:ellipsis;">{left}</div>'
            f'<div style="text-align:center; overflow:hidden; text-overflow:ellipsis;">{mid}</div>'
            f'<div style="text-align:right; overflow:hidden; text-overflow:ellipsis;">{right}</div>'
            f'</div>'
        )

    # Final HTML assembly (concatenate strings; no f-string containing CSS braces)
    html = (
        css
        + '<div class="hover-wrapper">'
        + '<button style="padding:10px 20px; font-size:16px; cursor:pointer;">Hover Here</button>'
        + '<div class="hover-box">'
        + title_html
        + rows_html
        + '</div></div>'
    )

    st.markdown(html, unsafe_allow_html=True)


# Example usage — place anywhere after your main code (don't modify existing code)
# st.write("### Example Custom Hover Box (fixed)")
# custom_hover_box()
