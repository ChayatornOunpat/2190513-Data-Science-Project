import pandas as pd
import plotly.express as px
import streamlit as st
import textwrap

# =====================================================================
# 1. PAGE CONFIGURATION
# =====================================================================
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
# 2. DATA LOADING & PROCESSING
# =====================================================================
@st.cache_data
def load_data():
    df_main = pd.read_csv("withZ.csv")
    try:
        df_details = pd.read_csv("grouped_nonnormalized_complete.csv")
    except:
        df_details = pd.DataFrame(columns=["company", "title", "value", "z_by_company"])
    return df_main, df_details

df_raw, dff = load_data()

# --- HELPER: NAME NORMALIZER ---
def normalize_name(name):
    if not isinstance(name, str): return ""
    name = name.lower()
    for bad_str in ["public company limited", "pcl", "limited", "company", "(thailand)", "inc.", "corp."]:
        name = name.replace(bad_str, "")
    return name.strip()

# --- 1. COMPANY LOOKUP ---
top_items_map = {}
if not dff.empty:
    dff_sorted = dff.sort_values(by="value", ascending=False)
    for company_name, group in dff_sorted.groupby("company"):
        top_rows = group[['title', 'value', 'z_by_company']].head(3).to_dict('records')
        clean_key = normalize_name(company_name)
        top_items_map[clean_key] = top_rows
        top_items_map[company_name] = top_rows

# --- 2. INDUSTRY LOOKUP ---
top_industry_items_map = {}
dff_with_ind = pd.DataFrame() # Initialize global df for industry lookup

if not dff.empty and not df_raw.empty:
    # A. Map Normalized Company Name -> Industry
    comp_to_ind_map = {}
    for _, row in df_raw.iterrows():
        clean_name = normalize_name(row['company_name'])
        comp_to_ind_map[clean_name] = row['industry']
        comp_to_ind_map[row['company_name']] = row['industry'] # Fallback
    
    # B. Assign Industry to Papers
    dff_ind = dff.copy()
    dff_ind['temp_clean_name'] = dff_ind['company'].apply(normalize_name)
    dff_ind['industry'] = dff_ind['temp_clean_name'].map(comp_to_ind_map)
    
    # Save this for the click-action table in Tab 2
    dff_with_ind = dff_ind.copy()

    # C. Group by Industry and get Top 3 Papers by Value
    dff_ind_sorted = dff_ind.dropna(subset=['industry']).sort_values(by="value", ascending=False)
    
    for ind_name, group in dff_ind_sorted.groupby("industry"):
        top_rows = group[['title', 'value', 'z_by_company']].head(3).to_dict('records')
        top_industry_items_map[ind_name] = top_rows

# =====================================================================
# 3. SIDEBAR CONTROLS
# =====================================================================
with st.sidebar:
    st.header("Dashboard Controls")
    st.markdown("Improve visibility using filters below.")
    
    sectors = ["All Sectors"] + sorted(df_raw["sector"].unique())
    selected_sector = st.selectbox("Filter by Sector", sectors)

    if selected_sector == "All Sectors":
        industries = ["All Industries"] + sorted(df_raw["industry"].unique())
    else:
        industries = ["All Industries"] + sorted(
            df_raw[df_raw["sector"] == selected_sector]["industry"].unique()
        )

    selected_industry = st.selectbox("Filter by Industry", industries)
    search = st.text_input("Search Company", placeholder="Type company name...")

    st.divider()
    st.markdown("#### Download Filtered Data")
    st.download_button(
        label="Download CSV",
        data=df_raw.to_csv(index=False),
        file_name="alignment_data.csv",
        mime="text/csv"
    )

# =====================================================================
# 4. FILTERING LOGIC
# =====================================================================
df_viz = df_raw.copy()

if selected_sector != "All Sectors":
    df_viz = df_viz[df_viz["sector"] == selected_sector]

if selected_industry != "All Industries":
    df_viz = df_viz[df_viz["industry"] == selected_industry]

if search.strip() != "":
    df_viz = df_viz[df_viz["company_name"].str.contains(search, case=False)]

# =====================================================================
# 5. MAIN DASHBOARD UI
# =====================================================================
st.title("University-Industry Alignment Dashboard")
st.caption("Understanding how academic research aligns with market economic value.")
st.divider()

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Companies Analyzed", f"{len(df_viz)}")
with col2: st.metric("Avg Alignment Score", f"{df_viz['total_alignment_score'].mean():.2f}")
with col3: st.metric("Total Market Value", f"฿{df_viz['market_cap'].sum():,.0f}")
with col4: st.metric("High Alignment Companies (Z > 1)", len(df_viz[df_viz["total_alignment_score"] > 1]))

st.divider()

tab1, tab2, tab3 = st.tabs(["Market Map", "Strategic Gap", "Data Table"])

# =====================================================================
# 6. HOVER HELPERS (SHARED)
# =====================================================================
def format_row(c1, c2, c3, color, is_bold=False):
    w1, w2, w3 = 16, 8, 8 
    c1 = str(c1)[:w1]
    c2 = str(c2)[:w2]
    c3 = str(c3)[:w3]
    row_str = f"{c1:<{w1}} {c2:^{w2}} {c3:>{w3}}".replace(" ", "&nbsp;")
    weight = "bold" if is_bold else "normal"
    return f"<span style='color:{color}; font-weight:{weight};'>{row_str}</span><br>"

# --- COMPANY HOVER ---
def build_hover_content(row):
    # Header
    header_text = row['sector'].upper()[:25] 
    html = format_row(header_text, "", "", "#1A237E", is_bold=True)
    html += "<span style='font-size:4px'>&nbsp;</span><br>" 

    # Company Data
    price = f"฿{row['market_cap']/1e9:.0f}B"
    pct = f"{row['total_alignment_score']:.2f}"
    main_color = "#2E7D32" if row['total_alignment_score'] > 0 else "#D32F2F"
    
    html += format_row("Company Name", "Market Cap", "Align. Val", "#000000")
    html += format_row(row['company_name'], price, f"{pct}", main_color, is_bold=True)
    html += "<span style='font-size:4px'>&nbsp;</span><br>"
    
    # Top 3 Papers
    items = top_items_map.get(row['company_name'])
    if not items:
        clean_name = normalize_name(row['company_name'])
        items = top_items_map.get(clean_name, [])
    
    html += format_row("Paper Title", "Val", "Z-Scr", "#999999")
    if items:
        for item in items:
            title = str(item.get('title', '-'))
            val = f"{item.get('value', 0):.2f}"
            z_val = f"{item.get('z_by_company', 0):.2f}"
            html += format_row(title, val, z_val, "black")
        for _ in range(3 - len(items)): html += format_row("", "", "", "white")
    else:
        html += format_row("No Data Found", "-", "-", "#999")
        html += format_row("", "", "", "white")
        html += format_row("", "", "", "white")
    return html

# --- INDUSTRY HOVER ---
def build_industry_hover_content(row):
    # Header
    header_text = str(row['sector']).upper()[:25]
    html = format_row(header_text, "", "", "#1A237E", is_bold=True)
    html += "<span style='font-size:4px'>&nbsp;</span><br>" 
    
    # Industry Data
    price = f"฿{row['market_cap']/1e9:.0f}B"
    pct = f"{row['total_alignment_score']:.2f}"
    main_color = "#2E7D32" if row['total_alignment_score'] > 0 else "#D32F2F"
    
    html += format_row("Industry", "Total Cap", "Avg Align", "#000000")
    html += format_row(row['industry'], price, f"{pct}", main_color, is_bold=True)
    html += "<span style='font-size:4px'>&nbsp;</span><br>"
    
    # Top 3 Papers
    items = top_industry_items_map.get(row['industry'], [])
    
    html += format_row("Paper Title", "Val", "Z-Scr", "#999999")
    if items:
        for item in items:
            title = str(item.get('title', '-'))
            val = f"{item.get('value', 0):.2f}"
            z_val = f"{item.get('z_by_company', 0):.2f}"
            html += format_row(title, val, z_val, "black")
        for _ in range(3 - len(items)): html += format_row("", "", "", "white")
    else:
        html += format_row("No Data Found", "-", "-", "#999")
        html += format_row("", "", "", "white")
        html += format_row("", "", "", "white")
    return html

# Apply Global Company Hover
df_viz['hover_content'] = df_viz.apply(build_hover_content, axis=1)

# =====================================================================
# TAB 1: MARKET MAP
# =====================================================================
with tab1:
    st.subheader(f"Market Alignment Map: {selected_sector}")
    st.caption("Box Size → Market Cap | Color → Research Fit (Z-Score)")
    
    def wrap_labels(text, width=15):
        return "<br>".join(textwrap.wrap(str(text), width=width))

    df_viz['wrapped_name'] = df_viz['company_name'].apply(lambda x: wrap_labels(x, width=22))
    red_green_px_scale = [(0, 'red'), (0.5, 'white'), (1, 'green')]

    fig_treemap = px.treemap(
        df_viz,
        path=[px.Constant("All Sectors"), "sector", "industry", "wrapped_name"],
        values="market_cap",
        color="total_alignment_score",
        color_continuous_scale=red_green_px_scale,
        color_continuous_midpoint=df_viz["total_alignment_score"].mean(),
        custom_data=['hover_content', 'company_name']
    )
    fig_treemap.update_traces(
        hovertemplate="%{customdata[0]}<extra></extra>",
        textposition="middle center",
        texttemplate="<b>%{label}</b>",
        textfont=dict(family="Verdana", size=20, color="black")
    )
    fig_treemap.update_layout(
        margin=dict(t=20, l=10, r=10, b=80),
        height=600,
        hoverlabel=dict(bgcolor="white", bordercolor="#1A237E", font_family="Consolas, monospace", font_size=13, align="left"),
        coloraxis_colorbar=dict(title="Alignment Score", orientation="h", yanchor="top", y=-0.05, thickness=15)
    )
    
    # SAFE CLICK ACTION
    event_1 = st.plotly_chart(fig_treemap, use_container_width=True, on_select="rerun", selection_mode="points")

    if isinstance(event_1, dict) and event_1.get("selection") and len(event_1["selection"]["points"]) > 0:
        try:
            selected_point = event_1['selection']['points'][0]
            # customdata[1] is company_name
            if 'customdata' in selected_point and len(selected_point['customdata']) > 1:
                selected_company = selected_point['customdata'][1]
                
                st.markdown(f"### 📄 Top Papers: {selected_company}")
                
                clean_sel = normalize_name(selected_company)
                papers_subset = dff[
                    (dff['company'] == selected_company) | 
                    (dff['company'].apply(normalize_name) == clean_sel)
                ]
                
                if not papers_subset.empty:
                    disp_df = papers_subset[['title', 'areas', 'value']].sort_values('value', ascending=False).head(10)
                    disp_df.columns = ["Title", "Subject Area", "Similarity Score"]
                    st.dataframe(disp_df, use_container_width=True, hide_index=True)
                else:
                    st.info(f"No papers found for {selected_company}")
        except Exception as e:
            st.error(f"Could not load papers: {e}")

# =====================================================================
# TAB 2: STRATEGIC GAP
# =====================================================================
with tab2:
    col_t1, col_t2 = st.columns([0.8, 0.2])
    with col_t1:
        st.subheader("Strategic Gap Analysis")
        st.caption("Top-Right Quadrant = Strong Research + High Market Value")
    with col_t2:
        view_mode = st.radio("View Type", ["Company View", "Industry View"], horizontal=True)

    if view_mode == "Industry View":
        # Industry View Logic
        df_plot = df_viz.groupby("industry").agg({
            'market_cap': 'sum',
            'total_alignment_score': 'mean',
            'sector': 'first' 
        }).reset_index()
        
        df_plot['hover_content'] = df_plot.apply(build_industry_hover_content, axis=1)
        
        x_col, y_col, size_col, color_col = "total_alignment_score", "market_cap", "market_cap", "industry"
        custom_data_cols = ['hover_content', 'industry']
        
    else:
        # Company View Logic
        df_plot = df_viz
        x_col, y_col, size_col, color_col = "total_alignment_score", "market_cap", "market_cap", "industry"
        custom_data_cols = ['hover_content', 'company_name']

    fig_scatter = px.scatter(
        df_plot,
        x=x_col, y=y_col, size=size_col, color=color_col,
        custom_data=custom_data_cols,
        log_y=True,
        labels={
            "total_alignment_score": "Research Alignment (Z-Score)",
            "market_cap": "Market Cap (Log Scale)"
        },
        template="plotly_white"
    )

    fig_scatter.update_traces(hovertemplate="%{customdata[0]}<extra></extra>")
    fig_scatter.update_layout(
        legend=dict(orientation="v", y=0.5, x=1.15, xanchor="left", yanchor="middle"),
        font=dict(family="Inter, sans-serif", size=15),
        hoverlabel=dict(bgcolor="white", bordercolor="#1A237E", font_family="Consolas, monospace", font_size=13, align="left"),
        height=600
    )

    median_score = df_plot[x_col].median()
    median_cap = df_plot[y_col].median()
    fig_scatter.add_vline(x=median_score, line_dash="dash", line_color="gray", annotation_text="Median Score")
    fig_scatter.add_hline(y=median_cap, line_dash="dash", line_color="gray", annotation_text="Median Cap")

    # SAFE CLICK ACTION
    event_2 = st.plotly_chart(fig_scatter, use_container_width=True, on_select="rerun", selection_mode="points")

    if isinstance(event_2, dict) and event_2.get("selection") and len(event_2["selection"]["points"]) > 0:
        try:
            point = event_2['selection']['points'][0]
            if 'customdata' in point and len(point['customdata']) > 1:
                selected_id = point['customdata'][1]
                
                if view_mode == "Industry View":
                     st.markdown(f"### 🏭 Top Papers for Industry: {selected_id}")
                     if not dff_with_ind.empty:
                         papers_subset = dff_with_ind[dff_with_ind['industry'] == selected_id]
                         if not papers_subset.empty:
                             disp_df = papers_subset[['title', 'areas', 'value']].sort_values('value', ascending=False).head(10)
                             disp_df.columns = ["Title", "Subject Area", "Similarity Score"]
                             st.dataframe(disp_df, use_container_width=True, hide_index=True)
                         else:
                             st.info(f"No papers found for industry: {selected_id}")
                else:
                     st.markdown(f"### 📄 Top Papers: {selected_id}")
                     clean_sel = normalize_name(selected_id)
                     papers_subset = dff[
                        (dff['company'] == selected_id) | 
                        (dff['company'].apply(normalize_name) == clean_sel)
                     ]
                     if not papers_subset.empty:
                         disp_df = papers_subset[['title', 'areas', 'value']].sort_values('value', ascending=False).head(10)
                         disp_df.columns = ["Title", "Subject Area", "Similarity Score"]
                         st.dataframe(disp_df, use_container_width=True, hide_index=True)
                     else:
                         st.info(f"No papers found for {selected_id}")
        except Exception as e:
            st.error(f"Error loading details: {e}")

# =====================================================================
# TAB 3: DATA TABLE
# =====================================================================
with tab3:
    st.subheader("Underlying Data (Filtered)")
    st.caption("Sorted by Alignment Score")

    st.dataframe(
        df_viz[[
            "company_name", "sector", "industry", "market_cap", "total_alignment_score"
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
