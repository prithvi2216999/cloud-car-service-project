import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date

# --- Page Config ---
st.set_page_config(page_title="Client Service Tracker", layout="centered")

st.title("👨‍🔧 Vehicle Service Status Tracker")

# --- Glassmorphism fix (add right after st.title) ---
st.markdown("""
<style>
.status-card {
    padding: 14px; 
    border-radius: 12px;
    margin: 7px 0;
    background: rgba(255,255,255,0.09); /* dark mode glass look */
    box-shadow: 0 3px 14px rgba(60,60,60,0.12);
    backdrop-filter: blur(9px);
    color: inherit;
}
[data-theme="light"] .status-card {
    background: rgba(240,245,255,0.88); /* light mode glass look */
    color: #101822;
    border: 1px solid #eaeaea;
    box-shadow: 0 4px 16px rgba(80,80,110,0.07);
}
</style>
""", unsafe_allow_html=True)

# --- Database Connection ---
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345",   # change if needed
        database="vehicle_service"
    )
    cursor = conn.cursor()
except mysql.connector.Error as err:
    st.error(f"Database connection error: {err}")
    st.stop()

# --- Ensure new columns exist (for cost and review) ---
try:
    cursor.execute("SHOW COLUMNS FROM services LIKE 'total_cost'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE services ADD COLUMN total_cost DECIMAL(10,2) DEFAULT 0")
        conn.commit()

    cursor.execute("SHOW COLUMNS FROM services LIKE 'review'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE services ADD COLUMN review TEXT")
        conn.commit()
except Exception as e:
    st.warning(f"Column check failed: {e}")

# --- Fixed cost chart for each service type ---
SERVICE_COSTS = {
    "Oil Change": 1000,
    "Engine Repair": 2500,
    "Tire Replacement": 1500,
    "Full Service": 3500
}

# --- Section 1: Register New Service ---
st.markdown("## 📝 Register Your Vehicle for Service")

with st.expander("Click to Register a New Service", expanded=False):
    with st.form("client_service_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("Customer Name")
        with col2:
            vehicle = st.text_input("Vehicle Number (e.g. KA27M2345)")
        with col3:
            service_type = st.selectbox("Service Type", [
                "Select", "Oil Change", "Engine Repair", "Tire Replacement", "Full Service"
            ])
        service_date = st.date_input("Preferred Service Date", value=date.today())

        # Auto show cost
        if service_type != "Select":
            estimated_cost = SERVICE_COSTS.get(service_type, 0)
            st.info(f"💰 Estimated Cost for {service_type}: ₹{estimated_cost}")
        else:
            estimated_cost = 0

        submitted = st.form_submit_button("Submit Service Request")

        if submitted:
            if name and vehicle and service_type != "Select":
                try:
                    insert_query = """
                        INSERT INTO services (customer_name, vehicle_number, service_type, service_date, status, total_cost)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (name, vehicle, service_type, service_date, "Pending", estimated_cost))
                    conn.commit()
                    st.success("✅ Service registered successfully! Please remember your vehicle number to track status.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.warning("Please fill out all fields before submitting.")

st.markdown("---")

# --- Section 2: Check Vehicle Service Status ---
st.header(" Check Your Vehicle Service Status")

vehicle_number = st.text_input("Enter your Vehicle Number (e.g. KA27M2345):")

if st.button("Check Status"):
    if vehicle_number:
        try:
            query = """
                SELECT id, customer_name, service_type, service_date, status, total_cost, review
                FROM services 
                WHERE vehicle_number = %s
            """
            cursor.execute(query, (vehicle_number,))
            records = cursor.fetchall()

            if records:
                df = pd.DataFrame(records, columns=[
                    "ID", "Customer Name", "Service Type", "Service Date", "Status", "Estimated Cost (₹)", "Review"
                ])
                st.success("✅ Record Found!")
                st.dataframe(df)

                for _, row in df.iterrows():
                    id_, name, s_type, s_date, status, cost, review = row
                    color = (
                        "🔴 Pending" if status == "Pending" else
                        "🟡 In Progress" if status == "In Progress" else
                        "🟢 Completed"
                    )
                    st.markdown(f"""
                        <div class="status-card">
                            <b>Customer:</b> {name}<br>
                            <b>Service:</b> {s_type}<br>
                            <b>Date:</b> {s_date}<br>
                            <b>Status:</b> {color}<br>
                            <b>Estimated Cost:</b> ₹{cost if cost else 0}
                        </div>
                    """, unsafe_allow_html=True)

                    # Review only if completed
                    if status == "Completed":
                        st.subheader(f"🗒 Leave a Review for {vehicle_number}")
                        user_review = st.text_area(f"Your feedback about the {s_type} service:", key=f"review_{id_}")
                        if st.button("Submit Review", key=f"submit_review_{id_}"):
                            if user_review.strip():
                                try:
                                    cursor.execute("UPDATE services SET review=%s WHERE id=%s", (user_review, id_))
                                    conn.commit()
                                    st.success("✅ Thank you! Your review has been recorded.")
                                except Exception as e:
                                    st.error(f"Error saving review: {e}")
                            else:
                                st.warning("Please write something before submitting your review.")

            else:
                st.warning("No record found for that vehicle number.")
        except Exception as e:
            st.error(f"❌ Error fetching data: {e}")
    else:
        st.warning("Please enter your vehicle number.")

st.markdown("---")

# --- Section 3: View Past Records by Name ---
st.subheader("View Your Past Service Records")
client_name = st.text_input("Enter your Name to View All Your Requests:")

if st.button("Show My Records"):
    if client_name:
        try:
            cursor.execute("""
                SELECT vehicle_number, service_type, service_date, status, total_cost, review 
                FROM services WHERE customer_name=%s
            """, (client_name,))
            data = cursor.fetchall()

            if data:
                df_client = pd.DataFrame(data, columns=[
                    "Vehicle Number", "Service Type", "Service Date", "Status", "Estimated Cost (₹)", "Review"
                ])
                st.dataframe(df_client)
            else:
                st.info("No records found for this name.")
        except Exception as e:
            st.error(f"Error loading records: {e}")
    else:
        st.warning("Please enter your name.")

conn.close()