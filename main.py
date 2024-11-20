import pandas as pd
import streamlit as st
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SHEET_URL = "YOUR_GOOGLE_SHEET_URL_HERE"
SERVICE_ACCOUNT_FILE = "path_to_your_service_account.json"

def load_google_sheet():
    try:
        credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
        service = build('sheets', 'v4', credentials=credentials)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SHEET_URL.split('/')[-2], range="Sheet1").execute()
        data = result.get('values', [])
        df = pd.DataFrame(data[1:], columns=data[0])  
        return df
    except Exception as e:
        st.error(f"Error accessing Google Sheet: {e}")
        st.stop()

def get_static_data():
    data = {
        'Time created': [1, 2, 1, 3, 1],
        'Dev bought own token (SOL)': [0.5, 1.2, 0.8, 1.5, 0.2],
        'Dev sold %': [100, 50, 100, 90, 100],
        'ATH market cap': [50000000, 200000000, 300000000, 100000000, 45000000],
        'ROI': [10, 8, 5, 15, 20],
        'X\'s': [2, 5, 3, 7, 10],
    }
    return pd.DataFrame(data)

def generate_filters(data):
    st.subheader('Define Signal Combination Filters:')
    filters = []
    available_columns = ['Time created', 'Dev bought own token (SOL)', 'Dev sold %']
    
    with st.form("filter_form"):
        num_filters = st.number_input("Number of filter conditions", min_value=1, max_value=5, step=1, value=1)
        for i in range(num_filters):
            col = st.selectbox(f"Column {i+1}", available_columns, key=f"col_{i}")
            condition = st.selectbox(
                f"Condition {i+1}",
                ["==", "<=", ">="],
                key=f"cond_{i}"
            )
            value = st.text_input(f"Value {i+1}", key=f"value_{i}")
            filters.append((col, condition, value))
        
        submit = st.form_submit_button("Generate Filtered Data")
    
    if submit:
        filtered_data = data.copy()
        for col, condition, value in filters:
            try:
                if condition == "==":
                    filtered_data = filtered_data[filtered_data[col] == float(value)]
                elif condition == "<=":
                    filtered_data = filtered_data[filtered_data[col] <= float(value)]
                elif condition == ">=":
                    filtered_data = filtered_data[filtered_data[col] >= float(value)]
            except ValueError:
                st.error(f"Invalid value for column {col}: {value}")
                return data
        
        # Exclude bad signals (below x10)
        filtered_data = filtered_data[filtered_data["X's"].astype(float) >= 10]
        return filtered_data

    return data

def get_bad_signals(data):
    bad_signals = data[data["X's"].astype(float) < 10]
    st.subheader("Bad Signals Analysis:")
    st.write(f"Identified {len(bad_signals)} bad signals.")
    st.write(bad_signals)
    return bad_signals

def save_filter_config(filters):
    st.sidebar.write("Save/Load Filter Configurations:")
    config_name = st.sidebar.text_input("Configuration Name:")
    if st.sidebar.button("Save Configuration"):
        with open("filter_configs.txt", "a") as f:
            f.write(f"{config_name}:{filters}\n")
        st.sidebar.success("Configuration saved.")

def load_filter_configs():
    try:
        with open("filter_configs.txt", "r") as f:
            configs = f.readlines()
        configs = {line.split(":")[0]: eval(line.split(":")[1]) for line in configs}
        st.sidebar.selectbox("Load Saved Configuration", options=configs.keys())
        return configs
    except FileNotFoundError:
        st.sidebar.warning("No configurations found.")
        return {}

def show_data_summary(data):
    st.subheader("Data Summary:")
    st.write(data.describe())

def filter_ui():
    st.title('Crypto Signal Combination Filters')

    data = load_google_sheet() if SHEET_URL else get_static_data()
    st.write(f"Data loaded successfully with {len(data)} records.")
    
    st.subheader('Raw Data:')
    st.write(data)

    # Data summary insights
    show_data_summary(data)

    # Generate dynamic filters
    filtered_data = generate_filters(data)

    # Show bad signals
    bad_signals = get_bad_signals(data)

    # Save/Load filter configurations
    filter_configs = load_filter_configs()

    st.subheader("Filtered Data (Good Signals Only):")
    st.write(filtered_data)

    # Dynamic column selection
    st.subheader("Select Columns to Include in Output:")
    columns_to_include = st.multiselect("Select Columns:", data.columns, default=data.columns)
    output_data = filtered_data[columns_to_include]

    st.download_button(
        label="Download Filtered Data (CSV)",
        data=output_data.to_csv(index=False),
        file_name=f"filtered_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

    if bad_signals is not None:
        st.download_button(
            label="Download Bad Signals (CSV)",
            data=bad_signals.to_csv(index=False),
            file_name=f"bad_signals_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    filter_ui()
