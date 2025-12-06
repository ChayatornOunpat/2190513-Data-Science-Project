import pandas as pd
import plotly.express as px
import streamlit as st

df_viz = pd.read_csv('withZ.csv')

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

st.plotly_chart(fig_scatter, use_container_width=True)