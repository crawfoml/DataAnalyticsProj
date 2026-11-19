import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Page Configuration
st.set_page_config(page_title="NRC Violations Dashboard", layout="wide")

st.title("☢️ NRC Inspection Findings and Violations")
st.markdown("Explore the seasonality and severity of nuclear facility violations.")

# Load Data (Cached for performance)
@st.cache_data
def load_data():
    # Adjust the path based on your repo structure
    return pd.read_csv("data/cleaned_violations_data.csv")

try:
    data = load_data()
    
    # Sidebar Filters
    st.sidebar.header("Filters")
    selected_severity = st.sidebar.multiselect(
        "Select Severity (0 = Green, 1 = High Severity):",
        options=data['High_Severity'].unique(),
        default=data['High_Severity'].unique()
    )
    
    # Apply Filters
    filtered_data = data[data['High_Severity'].isin(selected_severity)]
    
    # Display Metrics
    st.header("Overview")
    col1, col2 = st.columns(2)
    col1.metric("Total Violations", len(filtered_data))
    col2.metric("Unique Sites", filtered_data['Site Name'].nunique())
    
    # Visualizations
    st.header("Seasonal Trends")
    fig, ax = plt.subplots(figsize=(10, 4))
    monthly_counts = filtered_data.groupby('Month').size()
    sns.barplot(x=monthly_counts.index, y=monthly_counts.values, palette='viridis', ax=ax)
    ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    ax.set_ylabel("Number of Violations")
    st.pyplot(fig)
    
    # Data Table
    st.header("Raw Data Preview")
    st.dataframe(filtered_data.head(50))

except FileNotFoundError:
    st.error("Data file not found. Please check the file path to cleaned_violations_data.csv")
