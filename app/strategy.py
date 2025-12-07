import pandas as pd
import plotly.express as px
import streamlit as st
import textwrap


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


@st.cache_data
def load_data():
    df_main = pd.read_csv("withZ.csv")
    try:
        df_details = pd.read_csv("grouped_nonnormalized_complete.csv")
    except:
        df_details = pd.DataFrame(columns=["company", "title", "value", "z_by_company"])
    return df_main, df_details

df_raw, dff = load_data()


# get unique list of companies (actually have papers)
if not dff.empty:
    search_options = sorted(dff['company'].dropna().unique().tolist())
else:
    search_options = []


def normalize_name(name):
    if not isinstance(name, str): return ""
    name = name.lower()
    for bad_str in ["public company limited", "pcl", "limited", "company", "(thailand)", "inc.", "corp."]:
        name = name.replace(bad_str, "")
    return name.strip()

# for looking up company
top_items_map = {}
if not dff.empty:
    dff_sorted = dff.sort_values(by="value", ascending=False)
    for company_name, group in dff_sorted.groupby("company"):
        top_rows = group[['title', 'value', 'z_by_company']].head(3).to_dict('records')
        clean_key = normalize_name(company_name)
        top_items_map[clean_key] = top_rows
        top_items_map[company_name] = top_rows

# for looking up industry
top_industry_items_map = {}
dff_with_ind = pd.DataFrame() 

if not dff.empty and not df_raw.empty:

    # map normalized Company Name ---> industry
    comp_to_ind_map = {}
    for _, row in df_raw.iterrows():
        clean_name = normalize_name(row['company_name'])
        comp_to_ind_map[clean_name] = row['industry']
        comp_to_ind_map[row['company_name']] = row['industry'] 
    
    # assign industry to paper
    dff_ind = dff.copy()
    dff_ind['temp_clean_name'] = dff_ind['company'].apply(normalize_name)
    dff_ind['industry'] = dff_ind['temp_clean_name'].map(comp_to_ind_map)
    
    # save this for the click-action table in Tab 2
    dff_with_ind = dff_ind.copy()

    # group by industry ---> top 3 papers
    dff_ind_sorted = dff_ind.dropna(subset=['industry']).sort_values(by="value", ascending=False)
    
    for ind_name, group in dff_ind_sorted.groupby("industry"):
        top_rows = group[['title', 'value', 'z_by_company']].head(3).to_dict('records')
        top_industry_items_map[ind_name] = top_rows

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
    search = st.text_input("Search Company", placeholder="Type company name")


    

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


col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Companies Analyzed", f"{len(df_viz)}")
with col2: st.metric("Avg Alignment Score", f"{df_viz['total_alignment_score'].mean():.2f}")
with col3: st.metric("Total Market Value", f"฿{df_viz['market_cap'].sum():,.0f}")
with col4: st.metric("High Alignment Companies", len(df_viz[df_viz["total_alignment_score"] > 1]))



tab1, tab2, tab3 = st.tabs(["Market Map", "Strategic Gap", "Data Table"])


def format_row(c1, c2, c3, color, is_bold=False):
    w1, w2, w3 = 16, 8, 8 
    c1 = str(c1)[:w1]
    c2 = str(c2)[:w2]
    c3 = str(c3)[:w3]
    row_str = f"{c1:<{w1}} {c2:^{w2}} {c3:>{w3}}".replace(" ", "&nbsp;")
    weight = "bold" if is_bold else "normal"
    return f"<span style='color:{color}; font-weight:{weight};'>{row_str}</span><br>"

# Company hover --> the UI popup when u hover ur mouse 
def build_hover_content(row):

    header_text = row['sector'].upper()[:25] 
    html = format_row(header_text, "", "", "#1A237E", is_bold=True)
    html += "<span style='font-size:4px'>&nbsp;</span><br>" 

    price = f"฿{row['market_cap']/1e9:.0f}B"
    pct = f"{row['total_alignment_score']:.2f}"
    main_color = "#2E7D32" if row['total_alignment_score'] > 0 else "#D32F2F"
    
    html += format_row("Company Name", "Market Cap", "Align. Val", "#000000")
    html += format_row(row['company_name'], price, f"{pct}", main_color, is_bold=True)
    html += "<span style='font-size:4px'>&nbsp;</span><br>"

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

# hover func for the industry part
def build_industry_hover_content(row):

    header_text = str(row['sector']).upper()[:25]
    html = format_row(header_text, "", "", "#1A237E", is_bold=True)
    html += "<span style='font-size:4px'>&nbsp;</span><br>" 
    

    price = f"฿{row['market_cap']/1e9:.0f}B"
    pct = f"{row['total_alignment_score']:.2f}"
    main_color = "#2E7D32" if row['total_alignment_score'] > 0 else "#D32F2F"
    
    html += format_row("Industry", "Total Cap", "Avg Align", "#000000")
    html += format_row(row['industry'], price, f"{pct}", main_color, is_bold=True)
    html += "<span style='font-size:4px'>&nbsp;</span><br>"
    

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


df_viz['hover_content'] = df_viz.apply(build_hover_content, axis=1)


with tab1:
    st.subheader(f"Market Alignment Map: {selected_sector}")
    st.caption("Box Size → Market Cap | Color → Research Fit")
    
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
    
    st.plotly_chart(fig_treemap, use_container_width=True)


    st.divider()
    st.markdown("Search Papers by Company")
    
    t1_selection = st.selectbox(
        "Select a company to find papers", 
        options=search_options, 
        index=None, 
        placeholder="Type or select company",
        key="search_t1"
    )
    
    if t1_selection:

        t1_subset = dff[dff['company'] == t1_selection]
        

        if t1_subset.empty:
             clean_sel = normalize_name(t1_selection)
             t1_subset = dff[dff['company'].apply(normalize_name) == clean_sel]

        if not t1_subset.empty:
            st.markdown(f"**Found {len(t1_subset)} papers for '{t1_selection}'**")
            disp_t1 = t1_subset[['title', 'areas', 'value']].sort_values('value', ascending=False).head(10)

            disp_t1['areas'] = disp_t1['areas'].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x).replace("[","").replace("]","").replace("'",""))
            disp_t1.columns = ["Title", "Subject Area", "Similarity Score"]
            st.dataframe(disp_t1, use_container_width=True, hide_index=True)
        else:
            st.warning(f"No papers found for '{t1_selection}'")


with tab2:
    col_t1, col_t2 = st.columns([0.8, 0.2])
    with col_t1:
        st.subheader("Strategic Gap Analysis")
        st.caption("Top-Right Quadrant = Strong Research + High Market Value")
    with col_t2:
        view_mode = st.radio("View Type", ["Company View", "Industry View"], horizontal=True)

    if view_mode == "Industry View":

        df_plot = df_viz.groupby("industry").agg({
            'market_cap': 'sum',
            'total_alignment_score': 'mean',
            'sector': 'first' 
        }).reset_index()
        
        df_plot['hover_content'] = df_plot.apply(build_industry_hover_content, axis=1)
        
        x_col, y_col, size_col, color_col = "total_alignment_score", "market_cap", "market_cap", "industry"
        custom_data_cols = ['hover_content', 'industry']
        
    else:

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

    event_2 = st.plotly_chart(fig_scatter, use_container_width=True, on_select="rerun", selection_mode="points")

    if isinstance(event_2, dict) and event_2.get("selection") and len(event_2["selection"]["points"]) > 0:
        try:
            point = event_2['selection']['points'][0]
            if 'customdata' in point and len(point['customdata']) > 1:
                selected_id = point['customdata'][1]
                
                if view_mode == "Industry View":
                      st.markdown(f"Top Papers for Industry: {selected_id}")
                      if not dff_with_ind.empty:
                          papers_subset = dff_with_ind[dff_with_ind['industry'] == selected_id]
                          if not papers_subset.empty:
                              disp_df = papers_subset[['title', 'areas', 'value']].sort_values('value', ascending=False).head(10)

                              disp_df['areas'] = disp_df['areas'].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x).replace("[","").replace("]","").replace("'",""))
                              disp_df.columns = ["Title", "Subject Area", "Similarity Score"]
                              st.dataframe(disp_df, use_container_width=True, hide_index=True)
                          else:
                              st.info(f"No papers found for industry: {selected_id}")
                else:
                      st.markdown(f"Top Papers: {selected_id}")
                      clean_sel = normalize_name(selected_id)
                      papers_subset = dff[
                        (dff['company'] == selected_id) | 
                        (dff['company'].apply(normalize_name) == clean_sel)
                      ]
                      if not papers_subset.empty:
                          disp_df = papers_subset[['title', 'areas', 'value']].sort_values('value', ascending=False).head(10)

                          disp_df['areas'] = disp_df['areas'].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x).replace("[","").replace("]","").replace("'",""))
                          disp_df.columns = ["Title", "Subject Area", "Similarity Score"]
                          st.dataframe(disp_df, use_container_width=True, hide_index=True)
                      else:
                          st.info(f"No papers found for {selected_id}")
        except Exception as e:
            st.error(f"Error loading details: {e}")



    st.markdown("Search Papers by Company")
    
    t2_selection = st.selectbox(
        "Select a company to find papers:", 
        options=search_options, 
        index=None, 
        placeholder="Type or select company",
        key="search_t2"
    )
    
    if t2_selection:

        t2_subset = dff[dff['company'] == t2_selection]
        

        if t2_subset.empty:
             clean_sel = normalize_name(t2_selection)
             t2_subset = dff[dff['company'].apply(normalize_name) == clean_sel]

        if not t2_subset.empty:
            st.markdown(f"**Found {len(t2_subset)} papers for '{t2_selection}'**")
            disp_t2 = t2_subset[['title', 'areas', 'value']].sort_values('value', ascending=False).head(10)

            disp_t2['areas'] = disp_t2['areas'].apply(lambda x: ", ".join(x) if isinstance(x, list) else str(x).replace("[","").replace("]","").replace("'",""))
            disp_t2.columns = ["Title", "Subject Area", "Similarity Score"]
            st.dataframe(disp_t2, use_container_width=True, hide_index=True)
        else:
            st.warning(f"No papers found for '{t2_selection}'")

with tab3:
    st.subheader("Underlying Data (Filtered)")
    st.caption("Sorted by Alignment Score")

    st.dataframe(
        df_viz[[
            "company_name", "sector", "industry", "market_cap", "total_alignment_score"
        ]].sort_values("total_alignment_score", ascending=False),
        use_container_width=True
    )
    
