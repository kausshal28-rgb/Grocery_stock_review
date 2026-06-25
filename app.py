import streamlit as st
import pandas as pd
import os
import difflib

# Configuration and File Setup
DB_FILE = "grocery_inventory.csv"
CATEGORIES = ["Staples", "Dairy", "Produce", "Snacks", "Frozen", "Other"]
UNITS = ["EA", "gram", "Kg", "Litre"]

# Pre-defined list of common household groceries to standardize selection
STANDARD_ITEMS = [
    "-- Add Custom Item --",
    "Apple", "Banana", "Bread", "Butter", "Cheese", "Chicken", "Coffee", 
    "Eggs", "Flour", "Garlic", "Milk", "Onion", "Potato", "Rice", 
    "Salt", "Sugar", "Tea", "Tomato", "Yogurt"
]

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
    
    # 1. Standardized Dropdown Selection
    selected_item = st.selectbox("Select Item Name", STANDARD_ITEMS)
    
    # 2. Conditional text field if custom item is chosen
    if selected_item == "-- Add Custom Item --":
        new_name = st.text_input("Type Custom Item Name:")
    else:
        new_name = selected_item

    new_cat = st.selectbox("Category", CATEGORIES)
    
    # Unit Selection layout for Current Stock
    col_qty, col_unit = st.sidebar.columns([2, 1])
    new_qty = col_qty.number_input("Current Quantity", min_value=0, value=1, step=1)
    new_unit = col_unit.selectbox("Unit", UNITS)
    
    # Alert Threshold layout
    new_min = st.sidebar.number_input(f"Alert Threshold ({new_unit})", min_value=0, value=2, step=1, 
                                      help="Triggers a 'Low Stock' alert when inventory drops to or below this number.")
    
    submit_button = st.form_submit_button(label="Add Item")

# Handle Duplicate & Fuzzy Name Matching on Submission
if submit_button and new_name:
    cleaned_name = new_name.strip()
    existing_items = df["Item Name"].tolist()
    
    # Strict Duplicate Check (Case-insensitive)
    if cleaned_name.lower() in [item.lower() for item in existing_items]:
        st.sidebar.error(f"🚨 '{cleaned_name}' already exists in your inventory!")
        
    else:
        # Smart Fuzzy Match Check (75% similarity threshold)
        close_matches = difflib.get_close_matches(cleaned_name, existing_items, n=1, cutoff=0.75)
        
        if close_matches and st.session_state.get("override_item") != cleaned_name:
            st.sidebar.warning(f"🤔 Did you mean **{close_matches[0]}**?")
            st.sidebar.info("If this is a completely different item, click 'Add Item' again to force add it.")
            st.session_state["override_item"] = cleaned_name
        else:
            st.session_state["override_item"] = ""
            new_row = pd.DataFrame([[cleaned_name, new_cat, new_qty, new_unit, new_min]], columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)
            st.sidebar.success(f"Added {cleaned_name} successfully!")
            st.rerun()

# --- MAIN DASHBOARD ---
if df.empty:
    st.subheader("📋 Current Inventory")
    st.info("Your pantry is completely empty! Add items using the sidebar.")
else:
    # Pre-calculate Status
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

    # --- THREE WINDOWS / TABS ---
    tab_all, tab_status, tab_category = st.tabs([
        "📋 Full Inventory & Deletion", 
        "🔍 Filter by Status", 
        "🗂️ Filter by Category"
    ])

    # TAB 1: Full Inventory Management Window (Supports editing and deleting)
    with tab_all:
        st.write("### Complete Pantry Registry")
        st.caption("💡 **To Delete an Item:** Click the blank square box on the far left of the item's row to highlight it, then press the **Delete** key on your keyboard.")
        
        edited_df = st.data_editor(
            df, 
            disabled=["Status"],  # Allow changing Item Name/Category directly in table if needed
            column_config={
                "Unit": st.column_config.SelectboxColumn("Unit", options=UNITS, required=True),
                "Category": st.column_config.SelectboxColumn("Category", options=CATEGORIES, required=True)
            },
            use_container_width=True,
            num_rows="dynamic",  # THIS ENABLES ROW DELETION
            key="full_inventory_editor"
        )
        
        # Check if user added, edited, or deleted rows
        if not edited_df.equals(df):
            # Strip out calculated Status column before syncing to CSV
            if "Status" in edited_df.columns:
                save_df = edited_df.drop(columns=["Status"])
            else:
                save_df = edited_df
            save_data(save_df)
            st.success("Inventory changes saved successfully!")
            st.rerun()

    # TAB 2: Status Filter Window
    with tab_status:
        st.write("### Quick Shopping & Health Check Lists")
        status_choice = st.selectbox(
            "Select Status to View:", 
            ["Show All Warnings (Low & Out of Stock)", "🔴 Out of Stock", "🟡 Low Stock", "🟢 In Stock"],
            key="status_filter_dropdown"
        )
        
        if status_choice == "Show All Warnings (Low & Out of Stock)":
            filtered_status_df = df[df["Status"].isin(["🔴 Out of Stock", "🟡 Low Stock"])]
        else:
            filtered_status_df = df[df["Status"] == status_choice]
            
        if filtered_status_df.empty:
            st.success(f"No items match the status: **{status_choice}** 🎉")
        else:
            st.dataframe(
                filtered_status_df[["Status", "Item Name", "Category", "Quantity", "Unit", "Min Threshold"]],
                use_container_width=True,
                hide_index=True
            )

    # TAB 3: Category Filter Window
    with tab_category:
        st.write("### View Inventory by Kitchen Section")
        category_choice = st.selectbox(
            "Select Kitchen Category to View:", 
            CATEGORIES,
            key="category_filter_dropdown"
        )
        
        filtered_cat_df = df[df["Category"] == category_choice]
        
        if filtered_cat_df.empty:
            st.info(f"You don't have any items registered under **{category_choice}** yet.")
        else:
            st.dataframe(
                filtered_cat_df[["Status", "Item Name", "Quantity", "Unit", "Min Threshold"]],
                use_container_width=True,
                hide_index=True
            )