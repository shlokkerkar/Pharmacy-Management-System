import streamlit as st
import pandas as pd
import os
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
from database import (
    calculate_total_profit, calculate_total_sales,
    fetch_medicines, fetch_customers, fetch_sales,
    add_medicine, add_customer, medicines_expiring_this_week,
    record_sale, generate_report,
    delete_medicine, delete_customer,
    update_medicine, update_customer
)

# Ensure static folder exists
os.makedirs("static", exist_ok=True)

st.markdown("""
    <style>
        .login-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .login-column {
            padding: 40px;
            background: #ffffff;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            height: 100vh;
            overflow-y: auto;
        }
        .login-title {
            color: #1976D2;
            font-size: 32px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 20px;
        }
        .login-description {
            color: #333;
            font-size: 16px;
            margin-bottom: 20px;
            line-height: 1.6;
        }
        .stTextInput input {
            border: 1px solid #BBDEFB;
            border-radius: 8px;
            padding: 10px;
            font-size: 16px;
        }
        .stButton > button {
            background-color: #2196F3;
            color: white;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
            border: none;
            width: 100%;
            transition: 0.3s;
        }
        .stButton > button:hover {
            background-color: #1E88E5;
        }
            
        }
    </style>
""", unsafe_allow_html=True)


def update_prescription_paths():
    sales = fetch_sales()
    for sale in sales:
        _, _, _, _, _, pres_path = sale
        if pres_path and "prescriptions" in pres_path:
            new_path = pres_path.replace("prescriptions", "static")
            if os.path.exists(pres_path) and not os.path.exists(new_path):
                os.rename(pres_path, new_path)
            # Update database (you’ll need to implement this in database.py)
            # Example: update_sale_prescription_path(sale_id, new_path)


# ─── LOGIN LOGIC ───────────────────────────────────────────────────────────────
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login(username, password):
    return username == "admin" and password == "root"


# Login section
if not st.session_state.logged_in:
    # Create a container for the login section
    st.markdown('<h2 class="login-title">🔐 Admin Login</h2>', unsafe_allow_html=True)
    # st.markdown("""
    #     <div class="login-description" style="text-align: center;">
    #         Welcome to the Pharmacy Management System. Please log in with your admin credentials.
    #     </div>
    # """, unsafe_allow_html=True)

    user = st.text_input("Username", placeholder="Enter your username")
    pwd = st.text_input("Password", type="password", placeholder="Enter your password")

    if st.button("Login"):
        if login(user, pwd):
            st.session_state.logged_in = True
            st.success("✅ Logged in!")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

        # Terms and Conditions link
    # st.markdown('<a href="/terms" target="_self" class="terms-link" >Terms and Conditions</a>', unsafe_allow_html=True)

    st.stop()
# ─── OPTIONAL LOGOUT ───────────────────────────────────────────────────────────
with st.sidebar:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()



# ─── CSS & TITLE ────────────────────────────────────────────────────────────────
st.markdown("""
    <style>
        .stApp { background-color: #FFFFFF; }
        .stSidebar { background-color: #E3F2FD; padding: 20px; }
        .stSidebar .sidebar .sidebar-content { color: #1976D2 !important; }
        .stSidebar .stRadio > div > label > div:first-child { display: none; }
        .stSidebar .stRadio > div > label {
            color: #1976D2; font-size: 18px; padding: 10px 18px; margin: 5px 0;
            border-radius: 8px; cursor: pointer; transition: .3s;
        }
        .stSidebar .stRadio > div > label:hover { background-color: #90CAF9; color: #FFF; }
        .stSidebar .stRadio > div > label[aria-checked="true"] {
            background-color: #2196F3; color: #FFF;
        }
        .stTitle { color: #1976D2; font-size: 36px; font-weight: bold; text-align: center; margin-bottom: 20px; }
        .stHeader { color: #1976D2; font-size: 28px; font-weight: bold; margin-bottom: 15px; }
        .stButton > button {
            background-color: #2196F3; color: white; border-radius: 8px;
            padding: 10px 20px; font-size: 16px; font-weight: bold; border: none; transition: .3s;
        }
        .stButton > button:hover { background-color: #1E88E5; }
        .stMetric {
            background-color: #F5F5F5; padding: 20px; border-radius: 10px;
            text-align: center; font-size: 20px; font-weight: bold;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;
        }
        .stDataFrame {
            border: 1px solid #E0E0E0; border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stTextInput input, .stNumberInput input, .stTextArea textarea {
            border: 1px solid #BBDEFB; border-radius: 8px; padding: 10px; font-size: 16px;
        }
        .stSelectbox div[role="listbox"] {
            border: 1px solid #BBDEFB; border-radius: 8px; padding: 10px; font-size: 16px;
        }
        .stLineChart, .stBarChart { border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h2 class="stTitle">Pharmacy Management System 🏥</h2>', unsafe_allow_html=True)

# Update old paths on app start (run once)
if 'paths_updated' not in st.session_state:
    update_prescription_paths()
    st.session_state.paths_updated = True

# ─── SIDEBAR NAVIGATION ────────────────────────────────────────────────────────
st.sidebar.markdown('<div class="stSidebar">', unsafe_allow_html=True)
st.sidebar.title("Navigation")
menu = ["Dashboard", "Manage Medicines", "Manage Customers", "Record Sale", "Generate Report", "Advanced Analytics", "Medicine Recommender", "Alerts"]



choice = st.sidebar.radio("Select an option", menu)
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# ─── PAGES ─────────────────────────────────────────────────────────────────────

# Dashboard
if choice == "Dashboard":
    st.markdown('<h3 class="stHeader">Dashboard Overview 📊</h3>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Medicines", len(fetch_medicines()))
    col2.metric("Total Customers", len(fetch_customers()))
    col3.metric("Total Transactions", len(fetch_sales()))
    total_presc = sum(1 for *_, pres in fetch_sales() if pres)
    col4.metric("Prescriptions Uploaded", total_presc)

    s1, s2, s3 = st.columns(3)
    s1.metric("Total Sales Amount", f"₹{calculate_total_sales():.2f}")
    s2.metric("Total Profit", f"₹{calculate_total_profit():.2f}")
    s3.metric("Expires This Week", medicines_expiring_this_week())

    st.subheader("Recent Sales Transactions")
    sales_data = fetch_sales()
    if sales_data:
        df = pd.DataFrame(
            sales_data,
            columns=["Customer", "Medicine", "Qty", "Total", "Date", "Prescription"]
        )
        df["Prescription Link"] = df["Prescription"].apply(
            lambda x: f'<a href="app/static/{os.path.basename(x)}" target="_blank">View</a>' if pd.notna(x) else "N/A"
        )
        display_df = df.drop(columns=["Prescription"])
        html = display_df.tail(5).to_html(escape=False, index=False)
        st.markdown(html, unsafe_allow_html=True)        
    else:
        st.write("No sales yet.")

# Manage Medicines
elif choice == "Manage Medicines":
    st.markdown('<h3 class="stHeader">Manage Medicines 💊</h3>', unsafe_allow_html=True)
    action = st.selectbox("Select Action", ["Add Medicine", "Update Medicine", "Delete Medicine"])
    if action == "Add Medicine":
        name = st.text_input("Medicine Name")
        category = st.text_input("Category")
        buy_price = st.number_input("Buy Price", min_value=0.0, step=0.1)
        sell_price = st.number_input("Sell Price", min_value=0.0, step=0.1)
        stock = st.number_input("Stock", min_value=0, step=1)
        expiry_date = st.date_input("Expiry Date")
        if st.button("Add Medicine"):
            if not name.strip():
                st.error("Medicine Name cannot be empty.")
            elif not category.strip():
                st.error("Category cannot be empty.")
            elif buy_price <= 0:
                st.error("Buy Price must be greater than 0.")
            elif sell_price <= 0:
                st.error("Sell Price must be greater than 0.")
            elif stock < 0:
                st.error("Stock cannot be negative.")
            else:
                add_medicine(name, category, buy_price, sell_price, stock, expiry_date.strftime("%Y-%m-%d"))
                st.success(f"Medicine '{name}' added successfully!")
    elif action == "Update Medicine":
        medicines = fetch_medicines()
        med_map = {med[1]: med[0] for med in medicines}
        sel = st.selectbox("Select Medicine to Update", list(med_map.keys()))
        med_id = med_map[sel]
        new_name = st.text_input("New Name", value=sel)
        new_category = st.text_input("New Category")
        new_buy = st.number_input("New Buy Price", min_value=0.0, step=0.1)
        new_sell = st.number_input("New Sell Price", min_value=0.0, step=0.1)
        new_stock = st.number_input("New Stock", min_value=0, step=1)
        new_expiry = st.date_input("New Expiry Date")
        if st.button("Update Medicine"):
            if not new_name.strip():
                st.error("New Name cannot be empty.")
            elif not new_category.strip():
                st.error("New Category cannot be empty.")
            elif new_buy <= 0:
                st.error("New Buy Price must be > 0.")
            elif new_sell <= 0:
                st.error("New Sell Price must be > 0.")
            elif new_stock < 0:
                st.error("New Stock cannot be negative.")
            else:
                update_medicine(
                    med_id, new_name, new_category,
                    new_buy, new_sell, new_stock,
                    new_expiry.strftime("%Y-%m-%d")
                )
                st.success(f"Medicine '{sel}' updated!")
    else:  # Delete Medicine
        medicines = fetch_medicines()
        med_map = {med[1]: med[0] for med in medicines}
        sel = st.selectbox("Select Medicine to Delete", list(med_map.keys()))
        if st.button("Delete Medicine"):
            delete_medicine(med_map[sel])
            st.success(f"Medicine '{sel}' deleted!")
    st.subheader("Current Inventory")
    inv = pd.DataFrame(
        fetch_medicines(),
        columns=["ID", "Name", "Category", "Buy_price", "Sell_price", "Stock", "Expiry_date"]
    )
    st.dataframe(inv, height=200)

# Manage Customers
elif choice == "Manage Customers":
    st.markdown('<h3 class="stHeader">Manage Customers 👤</h3>', unsafe_allow_html=True)
    action = st.selectbox("Select Action", ["Add Customer", "Update Customer", "Delete Customer"])
    if action == "Add Customer":
        name = st.text_input("Customer Name")
        contact = st.text_input("Customer Contact")
        address = st.text_area("Customer Address")
        if st.button("Add Customer"):
            if not name.strip():
                st.error("Customer Name cannot be empty.")
            elif not contact.strip() or not contact.isdigit() or len(contact) < 10:
                st.error("Contact must be a valid phone number (at least 10 digits).")
            elif not address.strip():
                st.error("Address cannot be empty.")
            else:
                add_customer(name, contact, address)
                st.success(f"Customer '{name}' added!")
    elif action == "Update Customer":
        customers = fetch_customers()
        cust_map = {c[1]: c[0] for c in customers}
        sel = st.selectbox("Select Customer to Update", list(cust_map.keys()))
        cust_id = cust_map[sel]
        new_name = st.text_input("New Name", value=sel)
        new_contact = st.text_input("New Contact")
        new_address = st.text_area("New Address")
        if st.button("Update Customer"):
            if not new_name.strip():
                st.error("New Name cannot be empty.")
            elif not new_contact.strip() or not new_contact.isdigit() or len(new_contact) < 10:
                st.error("New Contact must be a valid phone number.")
            elif not new_address.strip():
                st.error("New Address cannot be empty.")
            else:
                update_customer(cust_id, new_name, new_contact, new_address)
                st.success(f"Customer '{sel}' updated!")
    else:  # Delete Customer
        customers = fetch_customers()
        cust_map = {c[1]: c[0] for c in customers}
        sel = st.selectbox("Select Customer to Delete", list(cust_map.keys()))
        if st.button("Delete Customer"):
            delete_customer(cust_map[sel])
            st.success(f"Customer '{sel}' deleted!")
    st.subheader("Customer List")
    cust_df = pd.DataFrame(fetch_customers(), columns=["ID", "Name", "Contact", "Address"])
    st.dataframe(cust_df, height=200)

elif choice == "Record Sale":
    st.markdown('<h3 class="stHeader">Record a New Sale 🛒</h3>', unsafe_allow_html=True)

    customers = fetch_customers()
    medicines = fetch_medicines()

    if not customers or not medicines:
        st.error("No customers or medicines available.")
    else:
        # Create a mapping from customer name to ID
        customer_name_to_id = {c[1]: c[0] for c in customers}
        customer_names = list(customer_name_to_id.keys())

        # ✅ ONE autocomplete text box using selectbox
        selected_customer_name = st.selectbox("Select Customer", customer_names)
        customer_id = customer_name_to_id[selected_customer_name]



        # Initialize cart if not present
        if "cart" not in st.session_state:
            st.session_state.cart = []

        st.subheader("Add Medicines to Cart")
        med_names = [m[1] for m in medicines]
        med_id_map = {m[1]: m[0] for m in medicines}
        med_stock_map = {m[0]: m[5] for m in medicines}
        med_price_map = {m[0]: m[4] for m in medicines}

        with st.form("med_form", clear_on_submit=True):
            med_name = st.selectbox("Select Medicine", med_names, key="med_select")
            quantity = st.number_input("Quantity", min_value=1, step=1, key="qty_select")
            add_med = st.form_submit_button("Add to Cart")

            if add_med:
                med_id = med_id_map[med_name]
                if quantity > med_stock_map[med_id]:
                    st.error("Not enough stock available.")
                else:
                    st.session_state.cart.append((med_id, med_name, quantity, med_price_map[med_id]))
                    st.success(f"Added {quantity} x {med_name} to cart")

        # Prescription uploader
        prescription = st.file_uploader("Upload Prescription (jpg/jpeg/png)", type=["jpg", "jpeg", "png"])
        if prescription:
            st.image(prescription, caption="Preview Prescription", width=200)

        # Display Cart Summary
        if st.session_state.cart:
            st.subheader("Cart Summary")
            total = sum(q * p for _, _, q, p in st.session_state.cart)
            for med_id, med_name, qty, price in st.session_state.cart:
                st.write(f"{med_name} - Qty: {qty}, Price: ₹{price} | Subtotal: ₹{qty * price}")

            st.write(f"### Total Amount: ₹{total}")

        # Final Sale Submission
        if st.button("Record Sale") and st.session_state.cart:
            path = None
            if prescription:
                path = os.path.join("static", prescription.name)
                with open(path, "wb") as f:
                    f.write(prescription.read())

            for med_id, _, qty, _ in st.session_state.cart:
                msg = record_sale(customer_id, med_id, qty, path)
                st.success(msg)

            st.session_state.cart = []  # Clear cart after submission





# Generate Report
elif choice == "Generate Report":
    st.markdown('<h3 class="stHeader">Generate Sales Report 📊</h3>', unsafe_allow_html=True)
    sd = st.date_input("Start Date")
    ed = st.date_input("End Date")
    if st.button("Generate Report"):
        if sd > ed:
            st.error("Start Date must be before End Date.")
        else:
            rpt = generate_report(sd.strftime('%Y-%m-%d'), ed.strftime('%Y-%m-%d'))

            if rpt is not None and not rpt.empty:
                rpt["Prescription Link"] = rpt["prescription"].apply(
                    lambda x: f'<a href="app/static/{os.path.basename(x)}" target="_blank">View</a>' if pd.notna(x) else "N/A"
                )
                display_rpt = rpt.drop(columns=["prescription"])
                html = display_rpt.to_html(escape=False, index=False)
                st.markdown(html, unsafe_allow_html=True)

                # Allow download as CSV
                csv = rpt.to_csv(index=False)
                st.download_button("Download CSV", csv, file_name="sales_report.csv", mime="text/csv")

            else:
                st.write("No records in this range.")


elif choice == "Advanced Analytics":
    st.markdown('<h3 class="stHeader">Advanced Analytics 📈</h3>', unsafe_allow_html=True)
    sales = fetch_sales()

    if sales:
        try:
            df = pd.DataFrame(
                sales,
                columns=["Customer", "Medicine", "Qty", "Total", "Date", "prescription"]
            )

            # Convert Date to datetime
            df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
            if df["Date"].isna().any():
                st.warning("Some dates could not be parsed and will be excluded.")
            df = df.dropna(subset=["Date"])

            # Sort and set Date index, ensuring uniqueness
            df = df.sort_values("Date")
            df.set_index("Date", inplace=True)
            df = df.loc[~df.index.duplicated(keep='first')]  # Remove duplicate dates

            # Ensure numeric columns
            df["Qty"] = pd.to_numeric(df["Qty"], errors='coerce').fillna(0)
            df["Total"] = pd.to_numeric(df["Total"], errors='coerce').fillna(0)

            # Date range filter
            st.subheader("Filter by Date Range")
            min_date = df.index.min().date()
            max_date = df.index.max().date()
            start_date, end_date = st.date_input(
                "Select Date Range",
                [min_date, max_date],
                min_value=min_date,
                max_value=max_date
            )
            filtered_df = df.loc[start_date:end_date]

            # Time period filter
            st.subheader("Select Time Period for Analysis")
            time_period = st.selectbox("Time Period", ["Daily", "Monthly", "Yearly"])
            resample_freq = {"Daily": "D", "Monthly": "M", "Yearly": "Y"}
            freq = resample_freq[time_period]

            # Sales Over Time
            st.subheader(f"Sales Over Time ({time_period})")
            sales_data = filtered_df["Total"].resample(freq).sum()
            if sales_data.empty:
                st.warning("No sales data for the selected period.")
            else:
                st.line_chart(sales_data)

            # Top Selling Medicines
            st.subheader("Top Selling Medicines")
            top_meds = filtered_df.groupby("Medicine")["Qty"].sum().nlargest(5)
            if top_meds.empty:
                st.warning("No medicine sales data.")
            else:
                st.bar_chart(top_meds)

            # Customer Purchase Analysis
            st.subheader("Customer Purchase Analysis")
            top_customers = filtered_df.groupby("Customer")["Total"].sum().nlargest(5)
            if top_customers.empty:
                st.warning("No customer purchase data.")
            else:
                st.bar_chart(top_customers)

        except Exception as e:
            st.error(f"Error processing sales data: {e}")
    else:
        st.write("No sales data available.")

elif choice == "Medicine Recommender":
    st.markdown('<h3 class="stHeader">AI Medicine Recommender 🤖</h3>', unsafe_allow_html=True)

    # Load the built-in dataset (already available internally)
    @st.cache_data
    def load_data():
        return pd.read_csv("C:\\Users\\Shlokam\\Desktop\\Static\\medicine_data.csv")  # Adjust if path is different

    data = load_data()

    # Handle multiple symptoms properly
    X = data['symptoms']
    y = data['medicine']

    # Create pipeline: text vectorizer + SVM
    from sklearn.svm import SVC
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.pipeline import make_pipeline

    model = make_pipeline(CountVectorizer(), SVC(kernel='linear', probability=True))
    model.fit(X, y)

    
    user_symptoms = st.text_area("Enter symptoms (comma separated)", placeholder="e.g. cough, fever, headache")

    
    known_symptoms = set()
    for symptom_list in data['symptoms']:
        known_symptoms.update(symptom.strip().lower() for symptom in symptom_list.split(','))

    if st.button("Recommend Medicine"):
        if not user_symptoms.strip():
            st.error("Please enter at least one symptom.")
        else:
            
            input_symptoms = [sym.strip().lower() for sym in user_symptoms.split(',')]
            invalid_symptoms = [sym for sym in input_symptoms if sym not in known_symptoms]

            if invalid_symptoms:
                st.error(f"❌ Sorry, can't predict. Try valid symptoms like: " + ', '.join(list(known_symptoms)[:5]) + "...")
            else:
                try:
                    
                    prediction = model.predict([user_symptoms])
                    probas = model.predict_proba([user_symptoms])[0]
                    top_meds = sorted(zip(model.classes_, probas), key=lambda x: x[1], reverse=True)[:3]

                    st.success(f"Recommended Medicine: {prediction[0]}")
                    st.markdown("#### Top Suggestions:")
                    for med, prob in top_meds:
                        st.write(f"- {med} ({prob*100:.1f}%)")
                except Exception as e:
                    st.error(f"Prediction failed: {e}")





elif choice == "Alerts":
    st.markdown('<h3 class="stHeader">Medicine Alerts ⚠️</h3>', unsafe_allow_html=True)

  
    medicines = fetch_medicines()

    
    low_stock_threshold = 10
    expiry_warning_threshold = pd.to_datetime("today") + pd.DateOffset(weeks=1)  

    
    low_stock_meds = [med for med in medicines if med[5] <= low_stock_threshold]

    
    expiring_meds = [med for med in medicines if pd.to_datetime(med[6]) <= expiry_warning_threshold]

   
    if low_stock_meds:
        st.subheader("Medicines with Low Stock")
        low_stock_df = pd.DataFrame(low_stock_meds, columns=["ID", "Name", "Category", "Buy_price", "Sell_price", "Stock", "Expiry_date"])
        st.dataframe(low_stock_df, height=200)
    else:
        st.write("No medicines are low in stock.")

   
    if expiring_meds:
        st.subheader("Medicines Expiring Soon")
        expiring_df = pd.DataFrame(expiring_meds, columns=["ID", "Name", "Category", "Buy_price", "Sell_price", "Stock", "Expiry_date"])
        st.dataframe(expiring_df, height=200)
    else:
        st.write("No medicines are expiring soon.")