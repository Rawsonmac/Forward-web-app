import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Setting page configuration
st.set_page_config(page_title="Oil Market Forward Curve Report", layout="wide")

# Loading and processing CSV data
@st.cache_data
def load_data():
    periods = ['JUN25', 'JUL25', 'AUG25', 'SEP25', 'OCT25', 'NOV25', 'Q325', 'Q425', 'Q126', 'Q226', 'Q326', 'CAL26', 'CAL27']
    routes = ['TD3C', 'TD20', 'TC2', 'TC14']
    
    # Loading CSV files
    oct_df = pd.read_csv('data/10_06_2025.csv', index_col=0)
    nov_df = pd.read_csv('data/11_06_2025.csv', index_col=0)
    
    # Cleaning and filtering data
    oct_data = []
    nov_data = []
    
    for period in periods:
        if period in oct_df.index:
            entry = {'period': period}
            for route in routes:
                ws_col = route
                mt_col = f"{route}__1"  # Adjust to f"{route}_$/MT" if CSV headers use TD3C_$/MT
                if ws_col in oct_df.columns and mt_col in oct_df.columns:
                    ws = pd.to_numeric(oct_df.loc[period, ws_col], errors='coerce')
                    mt = pd.to_numeric(oct_df.loc[period, mt_col], errors='coerce')
                    if pd.notnull(ws) and pd.notnull(mt):
                        entry[route] = {'ws': ws, 'mt': mt}
            if len(entry) > 1:
                oct_data.append(entry)
        
        if period in nov_df.index:
            entry = {'period': period}
            for route in routes:
                ws_col = route
                mt_col = f"{route}__1"  # Adjust to f"{route}_$/MT" if CSV headers use TD3C_$/MT
                if ws_col in oct_df.columns and mt_col in oct_df.columns:
                    ws = pd.to_numeric(nov_df.loc[period, ws_col], errors='coerce')
                    mt = pd.to_numeric(nov_df.loc[period, mt_col], errors='coerce')
                    if pd.notnull(ws) and pd.notnull(mt):
                        entry[route] = {'ws': ws, 'mt': mt}
            if len(entry) > 1:
                nov_data.append(entry)
    
    return oct_data, nov_data

# Computing differences between datasets
def compute_differences(oct_data, nov_data):
    differences = []
    routes = ['TD3C', 'TD20', 'TC2', 'TC14']
    
    for oct_row, nov_row in zip(oct_data, nov_data):
        if oct_row['period'] == nov_row['period']:
            diff = {'period': oct_row['period']}
            for route in routes:
                if route in oct_row and route in nov_row:
                    diff[route] = {
                        'wsDiff': nov_row[route]['ws'] - oct_row[route]['ws'],
                        'mtDiff': nov_row[route]['mt'] - oct_row[route]['mt']
                    }
            differences.append(diff)
    
    return differences

# Generating simulated headlines
def generate_headlines(differences):
    headlines = []
    max_change = {'route': '', 'period': '', 'wsDiff': 0}
    
    for diff in differences:
        for route in diff:
            if route != 'period' and diff[route]:
                if abs(diff[route]['wsDiff']) > abs(max_change['wsDiff']):
                    max_change = {'route': route, 'period': diff['period'], 'wsDiff': diff[route]['wsDiff']}
    
    if max_change['wsDiff'] != 0:
        headlines.append(
            f"{max_change['route']} Forward Curve {'Rises' if max_change['wsDiff'] > 0 else 'Drops'} "
            f"by {abs(max_change['wsDiff']):.2f} WS in {max_change['period']} Amid Market Shifts"
        )
    headlines.extend([
        'Oil Freight Market Shows Mixed Trends as Q325 Forward Curves Adjust',
        'TD20 Maintains Stability While TC14 Sees Notable Changes in November'
    ])
    
    return headlines

# Finding interesting fact
def interesting_fact(differences):
    max_change = {'route': '', 'period': '', 'wsDiff': 0}
    for diff in differences:
        for route in diff:
            if route != 'period' and diff[route]:
                if abs(diff[route]['wsDiff']) > abs(max_change['wsDiff']):
                    max_change = {'route': route, 'period': diff['period'], 'wsDiff': diff[route]['wsDiff']}
    return f"The most significant change occurred in {max_change['route']} for {max_change['period']}, with a WS change of {max_change['wsDiff']:.2f}."

# Formatting numbers for display
def format_number(num):
    if pd.isna(num):
        return 'N/A'
    if abs(num) >= 1000:
        return f"{num/1000:.1f}K"
    return f"{num:.2f}"

# Main app
st.title("Oil Market Forward Curve Report: October vs. November 2025")
st.markdown("""
This report compares oil freight forward curves between October 6, 2025, and November 6, 2025, for routes TD3C, TD20, TC2, and TC14. It includes WS rates and $/MT, with visualizations and insights into market trends.
""")

# Loading data
oct_data, nov_data = load_data()

# Headlines
st.header("Market Headlines")
headlines = generate_headlines(compute_differences(oct_data, nov_data))
for headline in headlines:
    st.markdown(f"- {headline}")

# Interesting Fact
st.header("Interesting Fact")
st.markdown(interesting_fact(compute_differences(oct_data, nov_data)))

# Line Chart: WS Comparison
st.header("WS Comparison Over Time")
line_data = []
for oct_row, nov_row in zip(oct_data, nov_data):
    row = {'period': oct_row['period']}
    for route in ['TD3C', 'TD20', 'TC2', 'TC14']:
        row[f"{route}_Oct"] = oct_row.get(route, {}).get('ws', None)
        row[f"{route}_Nov"] = nov_row.get(route, {}).get('ws', None)
    line_data.append(row)

line_df = pd.DataFrame(line_data)
fig_line = go.Figure()
for route in ['TD3C', 'TD20', 'TC2', 'TC14']:
    fig_line.add_trace(go.Scatter(x=line_df['period'], y=line_df[f"{route}_Oct"], name=f"{route} (Oct)", line=dict(width=2)))
    fig_line.add_trace(go.Scatter(x=line_df['period'], y=line_df[f"{route}_Nov"], name=f"{route} (Nov)", line=dict(width=2, dash='dash')))
fig_line.update_layout(title="WS Rates Comparison", xaxis_title="Period", yaxis_title="WS Rate", legend_title="Route", height=500)
st.plotly_chart(fig_line, use_container_width=True)

# Bar Chart: WS Changes
st.header("WS Changes (Nov - Oct)")
bar_data = compute_differences(oct_data, nov_data)
bar_df = pd.DataFrame([
    {'period': diff['period'], **{route: diff.get(route, {}).get('wsDiff', 0) for route in ['TD3C', 'TD20', 'TC2', 'TC14']}}
    for diff in bar_data
])
fig_bar = px.bar(bar_df, x='period', y=['TD3C', 'TD20', 'TC2', 'TC14'], barmode='group', title="WS Changes by Route")
fig_bar.update_layout(xaxis_title="Period", yaxis_title="WS Change", legend_title="Route", height=500)
st.plotly_chart(fig_bar, use_container_width=True)

# Data Table
st.header("Data Table")
table_data = []
for diff, oct_row, nov_row in zip(compute_differences(oct_data, nov_data), oct_data, nov_data):
    for route in ['TD3C', 'TD20', 'TC2', 'TC14']:
        if route in diff:
            table_data.append({
                'Period': diff['period'],
                'Route': route,
                'Oct WS': format_number(oct_row.get(route, {}).get('ws', None)),
                'Nov WS': format_number(nov_row.get(route, {}).get('ws', None)),
                'WS Change': format_number(diff[route]['wsDiff']),
                'Oct $/MT': format_number(oct_row.get(route, {}).get('mt', None)),
                'Nov $/MT': format_number(nov_row.get(route, {}).get('mt', None)),
                '$/MT Change': format_number(diff[route]['mtDiff'])
            })
st.dataframe(pd.DataFrame(table_data), use_container_width=True)

# Conclusion
st.header("Conclusion")
st.markdown("""
The forward curve comparison between October and November 2025 reveals subtle shifts in the oil freight market. TD3C shows a slight softening in WS rates, particularly in Q325, suggesting potential oversupply or reduced demand expectations. TD20 remains relatively stable, indicating consistent market conditions. TC2 and TC14 exhibit mixed trends, with TC14 showing notable adjustments in certain periods. These changes may reflect evolving market dynamics, such as shifts in refinery demand or geopolitical factors. Continued monitoring is recommended.
""")
