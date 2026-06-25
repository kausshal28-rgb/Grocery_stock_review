import streamlit as st
import pandas as pd
import os
import json
import difflib

# Configuration and File Setup
DB_FILE = "grocery_inventory.csv"
CAT_FILE = "grocery_categories.json"

# Default Initial Dictionary
DEFAULT_GROCERY_DATA = {
    "Staples & Flours": [
        "Wheat Atta", "Basmati Rice", "Regular Rice", "Idli Rice", 
        "Dalia (Broken Wheat)", "Oats", "Sooji (Rava)", "Poha", 
        "Besan (Gram Flour)", "Maida", "Ragi Flour"
    ],
    "Dals & Pulses": [
        "Toor Dal", "Moong Dal", "Masoor Dal", "Urad Dal", "Chana Dal", 
        "Rajma (Kidney Beans)", "Kabuli Chana", "Kala Chana", 
        "Sabut Moong", "Lobia (Black Eyed Peas)"
    ],
    "Spices & Masalas": [
        "Jeera (Cumin Seeds)", "Rai (Mustard Seeds)", "Dhaniya (Coriander Seeds)", 
        "Saunf (Fennel Seeds)", "Methi (Fenugreek Seeds)", "Haldi (Turmeric Powder)", 
        "Red Chilli Powder", "Garam Masala", "Hing (Asafoetida)", "Dalchini (Cinnamon)", 
        "Lavang (Cloves)", "Elaichi (Cardamom)", "Tej Patta (Bay Leaves)", "Salt", "Amchur Powder"
    ],
    "Oils & Sweeteners": [
        "Cooking Oil", "Ghee", "Sugar", "Jaggery (Gud)", "Tamarind (Imli)"
    ],
    "Dry Fruits & Seeds": [
        "Almonds (Badam)", "Cashews (Kaju)", "Raisins (Kishmish)", 
        "Peanuts (Moongfali)", "Sesame Seeds (Til)"
    ],
    "Breakfast & Packaged": [
        "Tea", "Coffee", "Tomato Ketchup", "Soy Sauce", 
        "Vermicelli (Semiya)", "Instant Noodles", "Papad", "Soya Chunks"
    ],
    "Dairy & Frozen": [
        "Milk", "Curd", "Butter", "Paneer", "Frozen Peas", "Frozen Corn"
    ],
    "Household & Cleaning": [
        "Detergent Powder", "Fabric Conditioner", "Dishwash Liquid", 
        "Scrubber Pads", "Floor Cleaner", "Toilet Cleaner", "Garbage Bags", "Mosquito Repellent"
    ],
    "Personal Care": [
        "Bathing Soap", "Shampoo", "Toothpaste", "Toothbrushes"
    ],
    "Other": []
}

# Load or Initialize Categories JSON
if not os.path.exists(CAT_FILE):
    with open(CAT_FILE, "w") as f:
        json.dump(DEFAULT_GROCERY_DATA, f, indent=4)

def load_categories():
    with open(CAT_FILE, "r") as f:
        return json.load(f)

def save_categories(data):
    with open(CAT_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Load current state of categories and items
INDIAN_GROCERY_DATA = load_categories()
CATEGORIES = list(INDIAN_GROCERY_DATA.keys())
UNITS = ["EA", "gram", "g", "Kg", "kg", "Litre", "litres", "ml", "bottle", "multipack", "packet", "pieces", "pack", "refills"]

# Flatten out all standard items dynamically
ALL_STANDARD_ITEMS = ["-- Add Custom Item --"] + sorted(list({item for items in INDIAN_GROCERY_DATA.values() for item in items}))

# Initialize CSV file if it doesn't exist
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=["Item Name", "Category", "Quantity", "Unit", "Min Threshold"])
    df.to_csv(DB_FILE, index=False)

def load_data():
    return pd.read_csv(DB_FILE)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# Streamlit Page UI Styling
st.set_page_config(page_title="Indian Grocery Inventory Manager", layout="wide")
st.title("🇮🇳 Home Grocery Inventory Manager")

# Load existing inventory
df = load_data()

# --- SIDEBAR: Add New Items ---
st.sidebar.header("➕ Add New Item")
with st.sidebar.form(key="add_form", clear_on_submit=True):
    
    # Standardized Searchable Dropdown
    selected_item = st.selectbox("Select Item Name", ALL_STANDARD_ITEMS)
    
    # Conditional field if user wants a custom item name
    if selected_item == "-- Add Custom Item --":
        new_name = st.text_input("Type Custom Item Name:")
        default_cat_idx = CATEGORIES.index("Other")
    else:
        new_name = selected_item
        detected_cat = "Other"
        for cat, items in INDIAN_GROCERY_DATA.items():
            if selected_item in items:
                detected_cat = cat
                break
        default_cat_idx = CATEGORIES.index(detected_cat)

    new_cat = st.selectbox("Category", CATEGORIES, index=default_cat_idx)
    
    # Unit & Quantity Layout
    col_qty, col_unit = st.sidebar.columns([2, 1])
    new_qty = col_qty.number_input("Current Quantity", min_value=0.0, value=1.0, step=0.5, format="%.1f")
    new_unit = col_unit.selectbox("Unit", UNITS)
    
    # Alert Threshold layout
    new_min = st.sidebar.number_input(f"Alert Threshold ({new_unit})", min_value=0.0, value=0.0, step=0.5, format="%.1f")
    
    submit_button = st.form_submit_button(label="Add Item")

# Handle Submission, Duplicate Prevention, and Dynamic Dictionary Updating
if submit_button and new_name:
    # Formatting input nicely (Capitalizing first letter of words)
    cleaned_name = new_name.strip().title()
    existing_items = df["Item Name"].tolist()
    
    # Strict Duplicate Check
    if cleaned_name.lower() in [item.lower() for item in existing_items]:
        st.sidebar.error(f"🚨 '{cleaned_name}' already exists in your inventory!")
        
    else:
        # Fuzzy Match Check
        close_matches = difflib.get_close_matches(cleaned_name, existing_items, n=1, cutoff=0.75)
        
        if close_matches and st.session_state.get("override_item") != cleaned_name:
            st.sidebar.warning(f"🤔 Did you mean **{close_matches[0]}**?")
            st.sidebar.info("If this is a completely different item, click 'Add Item' again to force add it.")
            st.session_state["override_item"] = cleaned_name
        else:
            st.session_state["override_item"] = ""
            
            # --- DYNAMIC UPDATE LOGIC ---
            # If it was a custom item, automatically add it permanently to the selected category list!
            if selected_item == "-- Add Custom Item --":
                # Double-check it doesn't already live inside the master structural dictionary
                flat_master_list = [item.lower() for items in INDIAN_GROCERY_DATA.values() for item in items]
                if cleaned_name.lower() not in flat_master_list:
                    INDIAN_GROCERY_DATA[new_cat].append(cleaned_name)
                    save_categories(INDIAN_GROCERY_DATA)
                    st.sidebar.info(f"💡 '{cleaned_name}' added to standard dropdown library!")

            # Save item to inventory database
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
    df["Status"] = df.apply(lambda row: "🔴 Out of Stock" if float(row["Quantity"]) == 0 else ("🟡 Low Stock" if float(row["Quantity"]) <= float(row["Min Threshold"]) else "🟢 In Stock"), axis=1)
    
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

    # TAB 1: Full Inventory Management Window
    with tab_all:
        st.write("### Complete Pantry Registry")
        st.caption("💡 **To Delete an Item:** Click the blank square box on the far left of the item's row to highlight it, then press the **Delete** key on your keyboard.")
        
        edited_df = st.data_editor(
            df, 
            disabled=["Status"],
            column_config={
                "Quantity": st.column_config.NumberColumn("Quantity", step=0.1, format="%.1f"),
                "Min Threshold": st.column_config.NumberColumn("Min Threshold", step=0.1, format="%.1f"),
                "Unit": st.column_config.SelectboxColumn("Unit", options=UNITS, required=True),
                "Category": st.column_config.SelectboxColumn("Category", options=CATEGORIES, required=True)
            },
            use_container_width=True,
            num_rows="dynamic",
            key="full_inventory_editor"
        )
        
        if not edited_df.equals(df):
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