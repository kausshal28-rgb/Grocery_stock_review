import streamlit as st
import pandas as pd
import os

# Configuration and File Setup
DB_FILE = "grocery_inventory.csv"

# Initialize CSV file if it doesn't exist
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=["Item Name", "Category", "Quantity", "Unit", "Min Threshold"])
    df.to_csv(DB_FILE, index=False)

def load_data():
    return pd.read_csv(DB_FILE)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# Streamlit Page UI Styling
st.set_page_config(page_title="Home Grocery Manager", layout="wide")
st.title("🍏 Home Grocery Inventory Manager")

# Load existing inventory
df = load_data()

# Ensure older CSV files don't crash if they miss the 'Unit' column
if "Unit" not in df.columns and not df.empty:
    df.insert(3, "Unit", "EA")

# --- SIDEBAR: Add New Items ---
st.sidebar.header("➕ Add New Item")
with st.sidebar.form(key="add_form", clear_on_submit=True):
    new_name = st.text_input("Item Name (e.g., Milk, Rice)")
    new_cat = st.selectbox("Category", ["Staples", "Dairy", "Produce", "Snacks", "Frozen", "Other"])
    
    # Unit Selection layout for Current Stock
    col_qty, col_unit = st.sidebar.columns([2, 1])
    new_qty = col_qty.number_input("Current Quantity", min_value=0, value=1, step=1)
    new_unit = col_unit.selectbox("Unit", ["EA", "gram", "Kg", "Litre"])
    
    # Alert Threshold layout (dynamically displays the chosen unit label)
    new_min = st.sidebar.number_input(f"Alert Threshold ({new_unit})", min_value=0, value=2, step=1, 
                                      help="Triggers a 'Low Stock' alert when inventory drops to or below this number.")
    
    submit_button = st.form_submit_button(label="Add Item")

if submit_button and new_name:
    if new_name.strip().lower() in df["Item Name"].str.lower().values:
        st.sidebar.error(f"'{new_name}' already exists!")
    else:
        new_row = pd.DataFrame([[new_name.strip(), new_cat, new_qty, new_unit, new_min]], columns=df.columns)
        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)
        st.sidebar.success(f"Added {new_name} successfully!")
        st.rerun()

# --- MAIN DASHBOARD ---
st.subheader("📋 Current Inventory")

if df.empty:
    st.info("Your pantry is completely empty! Add items using the sidebar.")
else:
    # Status calculation
    df["Status"] = df.apply(lambda row: "🔴 Out of Stock" if row["Quantity"] == 0 else ("🟡 Low Stock" if row["Quantity"] <= row["Min Threshold"] else "🟢 In Stock"), axis=1)
    
    # Metrics
    low_stock_count = df[df["Quantity"] <= df["Min Threshold"]].shape[0]
    total_items = df.shape[0]
    
    c1, c2 = st.columns(2)
    c1.metric("Total Unique Items", total_items)
    c2.metric("Items to Restock", low_stock_count, delta_color="inverse")
    
    st.write("### Manage quantities below:")
    
    # Interactive Table Configuration
    edited_df = st.data_editor(
        df, 
        disabled=["Item Name", "Category", "Status"], 
        column_config={
            "Unit": st.column_config.SelectboxColumn(
                "Unit",
                options=["EA", "gram", "Kg", "Litre"],
                required=True,
            ),
            "Min Threshold": st.column_config.NumberColumn(
                "Min Threshold",
                help="Low stock alert limit"
            )
        },
        use_container_width=True,
        num_rows="dynamic"
    )
    
    if not edited_df.equals(df):
        save_df = edited_df.drop(columns=["Status"])
        save_data(save_df)
        st.success("Inventory updated!")
        st.rerun()