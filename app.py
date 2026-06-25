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
if df.empty:
    st.subheader("📋 Current Inventory")
    st.info("Your pantry is completely empty! Add items using the sidebar.")
else:
    # Always pre-calculate the Status before displaying any window/tab
    df["Status"] = df.apply(lambda row: "🔴 Out of Stock" if row["Quantity"] == 0 else ("🟡 Low Stock" if row["Quantity"] <= row["Min Threshold"] else "🟢 In Stock"), axis=1)
    
    # Top Metrics Bar
    out_stock_count = df[df["Quantity"] == 0].shape[0]
    low_stock_count = df[(df["Quantity"] <= df["Min Threshold"]) & (df["Quantity"] > 0)].shape[0]
    total_items = df.shape[0]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Unique Items", total_items)
    c2.metric("🟡 Low Stock Items", low_stock_count)
    c3.metric("🔴 Out of Stock", out_stock_count, delta_color="inverse")
    
    st.write("---")

    # --- CREATING THE WINDOWS / TABS ---
    tab_all, tab_filter = st.tabs(["📋 View & Edit Full Inventory", "🔍 Filter Items by Status"])

    # WINDOW 1: Full Inventory Management
    with tab_all:
        st.write("### Complete Pantry Registry")
        edited_df = st.data_editor(
            df, 
            disabled=["Item Name", "Category", "Status"], 
            column_config={
                "Unit": st.column_config.SelectboxColumn(
                    "Unit", options=["EA", "gram", "Kg", "Litre"], required=True
                )
            },
            use_container_width=True,
            key="full_inventory_editor"
        )
        
        if not edited_df.equals(df):
            save_df = edited_df.drop(columns=["Status"])
            save_data(save_df)
            st.success("Inventory updated!")
            st.rerun()

    # WINDOW 2: Status Filter Window
    with tab_filter:
        st.write("### Quick Shopping & Health Check Lists")
        
        # User dropdown to filter down items
        status_choice = st.selectbox(
            "Select Status to View:", 
            ["Show All Warnings (Low & Out of Stock)", "🔴 Out of Stock", "🟡 Low Stock", "🟢 In Stock"]
        )
        
        # Apply the selected filter to data
        if status_choice == "Show All Warnings (Low & Out of Stock)":
            filtered_df = df[df["Status"].isin(["🔴 Out of Stock", "🟡 Low Stock"])]
        else:
            filtered_df = df[df["Status"] == status_choice]
            
        # Display the filtered items
        if filtered_df.empty:
            st.success(f"No items match the status: **{status_choice}** 🎉")
        else:
            st.dataframe(
                filtered_df[["Status", "Item Name", "Category", "Quantity", "Unit", "Min Threshold"]],
                use_container_width=True,
                hide_index=True
            )