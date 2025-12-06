import pandas as pd
import plotly.express as px
import streamlit as st

df_viz = pd.read_csv('withZ.csv')

red_green_px_scale = [
    (0, 'red'),
    (0.5, 'white'),
    (1, 'green')
]

fig_treemap = px.treemap(
    df_viz,
    path=[px.Constant("All Sectors"), 'sector', 'industry', 'company_name'], # Hierarchy
    values='market_cap',                # Size of the box = Economic Value
    color='total_alignment_score',      # Color = Our Research Relevance
    color_continuous_scale=red_green_px_scale,    # Red (Low) to Green (High)
    color_continuous_midpoint=df_viz['total_alignment_score'].mean(), # Center the color scale
    hover_data=['total_alignment_score'],
    title="Market Map: Economic Value vs. Research Fit"
)

# fig_treemap.update_traces(root_color="white")
fig_treemap.update_layout(margin=dict(t=100, l=150, r=150, b=100))
fig_treemap.update_layout(
    coloraxis_colorbar=dict(
        orientation="h",        # Horizontal orientation
        yanchor="bottom",
        y=-0.3,                 # Push below the chart
        xanchor="center",
        x=0.5,                  # Center it
        thickness=10,           # Make it thinner to look cleaner
        title_side="top"        # Put the label ('total_alignment_score') above the bar
    ),
    margin=dict(t=50, l=25, r=25, b=50) # Ensure bottom margin exists
)
# st.plotly_chart(fig_treemap, use_container_width=True)


fig_scatter = px.scatter(
    df_viz,
    x="total_alignment_score",      # X-Axis: Our Research Strength
    y="market_cap",                 # Y-Axis: Market Demand/Size
    size="market_cap",              # Bubble Size: Reinforces Y-axis visual
    color="industry",               # Color: distinct by Industry (e.g. Energy vs Tech)
    hover_name="company_name",           # Tooltip Header
    hover_data=["sector", "total_alignment_score"], # Extra info on hover
    log_y=True,                     # CRITICAL: Use Log Scale for Market Cap (huge variance)
    title="Research Alignment vs. Market Value",
    labels={
        "total_alignment_score": "Research Alignment (Cumulative Z-Score)",
        "market_cap": "Company Market Cap (THB)"
    },
    template="plotly_white"
)

# Add Quadrant Lines (The "Gap" Analysis)
# Vertical Line = Median Alignment Score
fig_scatter.add_vline(x=df_viz['total_alignment_score'].median(), line_dash="dash", line_color="gray")
# Horizontal Line = Median Market Cap
fig_scatter.add_hline(y=df_viz['market_cap'].median(), line_dash="dash", line_color="gray")
# fig_scatter.update_layout(
#     legend=dict(
#         orientation="h",        # Force horizontal orientation
#         yanchor="bottom",       
#         y=-0.3,                 # Push below the x-axis (negative value)
#         xanchor="center",       
#         x=0.5                   # Center horizontally
#     ),
#     margin=dict(b=10)           # Add bottom margin so the legend isn't cut off
# )
# st.plotly_chart(fig_scatter, use_container_width=True)



st.title("Proj: University-Industry Alignment Dashboard")

# Top Level Filters
selected_sector = st.selectbox("Filter by Sector", ["All"] + list(df_viz['sector'].unique()))

if selected_sector != "All":
    df_viz = df_viz[df_viz['sector'] == selected_sector]

with st.container():
    # Row 1: The "Market View" (Treemap)
    st.header("1. Market Alignment Map")
    st.write("Size = Company Value | Color = Research Fit (Green = Strong)")
    st.plotly_chart(fig_treemap, use_container_width=True)

with st.container():
    # Row 2: The "Gap" Analysis (Scatter)
    st.header("2. Strategic Gap Analysis")
    st.write("Are we researching what the market values?")
    st.plotly_chart(fig_scatter, use_container_width=True)
