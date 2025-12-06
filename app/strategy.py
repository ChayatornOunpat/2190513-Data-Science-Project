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

# for loading data
@st.cache_data
def load_data():
    return pd.read_csv("withZ.csv")

df_raw = load_data()

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


with tab1:
    st.subheader(f"Market Alignment Map: {selected_sector}")
    st.caption("Box Size → Market Cap | Color → Research Fit (Z-Score)")

    red_green_px_scale = [
        (0, 'red'),
        (0.5, 'white'),
        (1, 'green')
    ]

    fig_treemap = px.treemap(
        df_viz,
        path=[px.Constant("All Sectors"), "sector", "industry", "company_name"],
        values="market_cap",
        color="total_alignment_score",
        color_continuous_scale=red_green_px_scale,
        color_continuous_midpoint=df_viz["total_alignment_score"].mean(),
        hover_data=["total_alignment_score"],
    )

    fig_treemap.update_layout(
        font=dict(
            family="Verdana",
            size=16,
            color="black"
        )
    )

    fig_treemap.update_traces(
        textfont=dict(
            family="Verdana",
            size=14
        )
    )

    fig_treemap.update_layout(
        margin=dict(t=20, l=10, r=10, b=10),
        height=600,
        coloraxis_colorbar=dict(
            title="Alignment Score",
            orientation="h",
            y=-0.12,
            x=0.5,
            thickness=15,
            len=0.5,
            xanchor="center",
        )
    )

    st.plotly_chart(fig_treemap, use_container_width=True)


with tab2:
    st.subheader("Strategic Gap Analysis")
    st.caption("Top-Right Quadrant = Strong Research + High Market Value")

    fig_scatter = px.scatter(
        df_viz,
        x="total_alignment_score",
        y="market_cap",
        size="market_cap",
        color="industry",
        hover_name="company_name",
        hover_data=["sector", "total_alignment_score"],
        log_y=True,
        labels={
            "total_alignment_score": "Research Alignment (Z-Score)",
            "market_cap": "Market Cap (Log Scale)"
        },
        template="plotly_white"
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
        )
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

    fig_scatter.update_layout(
        height=600
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
