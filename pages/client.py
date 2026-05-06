import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date

# --- Page Config ---
st.set_page_config(page_title="Client Service Tracker", layout="centered")

st.title("👨‍🔧 Vehicle Service Status Tracker")

# --- Custom Styling ---
st.markdown("""
<style>
.status-card {
    padding: 14px;
    border-radius: 12px;
    margin: 7px 0;
    background: rgba(255,255,255,0.09);
    box-shadow: 0 3px 14px rgba(60,60,60,0.12);
    backdrop-filter: blur(9px);
    color: inherit;
}

[data-theme="light"] .status-card {
    background: rgba(240,245,255,0.88);
    color: #101822;
    border: 1px solid #eaeaea;
    box-shadow: 0 4px 16px rgba(80,80,110,0.07);
}
</style>
""", unsafe_allow_html=True)

# --- Database Connection ---
try:
    conn = mysql.connector.connect(
        host="trolley.proxy.rlwy.net",
        port=12569,
        user="root",
        password="COTAetjZfIfkLoOCtMRgyYwmPPEfBjzt",
        database="vehicle_service"
    )

    cursor = conn.cursor()

except mysql.connector.Error as err:
    st.error(f"Database connection error: {err}")
    st.stop()

# --- Fixed cost chart ---
SERVICE_COSTS = {
    "Oil Change": 1000,
    "Engine Repair": 2500,
    "Tire Replacement": 1500,
    "Full Service": 3500
}

# =========================================================
# SECTION 1: REGISTER SERVICE
# =========================================================

st.markdown("## 📝 Register Your Vehicle for Service")

with st.expander("Click to Register a New Service", expanded=False):

    with st.form("client_service_form"):

        col1, col2, col3 = st.columns(3)

        with col1:
            name = st.text_input("Customer Name")

        with col2:
            vehicle = st.text_input("Vehicle Number (e.g. KA27M2345)")

        with col3:
            service_type = st.selectbox(
                "Service Type",
                [
                    "Select",
                    "Oil Change",
                    "Engine Repair",
                    "Tire Replacement",
                    "Full Service"
                ]
            )

        service_date = st.date_input(
            "Preferred Service Date",
            value=date.today()
        )

        # --- Show estimated cost ---
        if service_type != "Select":
            estimated_cost = SERVICE_COSTS.get(service_type, 0)
            st.info(f"💰 Estimated Cost: ₹{estimated_cost}")
        else:
            estimated_cost = 0

        submitted = st.form_submit_button("Submit Service Request")

        if submitted:

            if name and vehicle and service_type != "Select":

                try:

                    insert_query = """
                    INSERT INTO services
                    (
                        customer_name,
                        vehicle_number,
                        service_type,
                        service_date,
                        status,
                        total_cost
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """

                    values = (
                        name,
                        vehicle,
                        service_type,
                        service_date,
                        "Pending",
                        estimated_cost
                    )

                    cursor.execute(insert_query, values)
                    conn.commit()

                    st.success(
                        "✅ Service registered successfully!"
                    )

                except Exception as e:
                    st.error(f"❌ Database Error: {e}")

            else:
                st.warning("Please fill all fields.")

# =========================================================
# SECTION 2: CHECK STATUS
# =========================================================

st.markdown("---")

st.header("🚗 Check Your Vehicle Service Status")

vehicle_number = st.text_input(
    "Enter your Vehicle Number:"
)

if st.button("Check Status"):

    if vehicle_number:

        try:

            query = """
            SELECT
                customer_name,
                vehicle_number,
                service_type,
                service_date,
                status,
                total_cost,
                review
            FROM services
            WHERE vehicle_number = %s
            """

            cursor.execute(query, (vehicle_number,))
            records = cursor.fetchall()

            if records:

                st.success("✅ Record Found!")

                df = pd.DataFrame(
                    records,
                    columns=[
                        "Customer Name",
                        "Vehicle Number",
                        "Service Type",
                        "Service Date",
                        "Status",
                        "Estimated Cost",
                        "Review"
                    ]
                )

                st.dataframe(df)

                for row in records:

                    customer_name = row[0]
                    vehicle_no = row[1]
                    service_type = row[2]
                    service_date = row[3]
                    status = row[4]
                    total_cost = row[5]

                    st.markdown(f"""
                    <div class="status-card">
                        <b>Customer:</b> {customer_name}<br>
                        <b>Vehicle:</b> {vehicle_no}<br>
                        <b>Service:</b> {service_type}<br>
                        <b>Date:</b> {service_date}<br>
                        <b>Status:</b> {status}<br>
                        <b>Estimated Cost:</b> ₹{total_cost}
                    </div>
                    """, unsafe_allow_html=True)

            else:
                st.warning("No record found for that vehicle number.")

        except Exception as e:
            st.error(f"❌ Error fetching data: {e}")

    else:
        st.warning("Please enter vehicle number.")

# =========================================================
# SECTION 3: VIEW ALL RECORDS BY NAME
# =========================================================

st.markdown("---")

st.subheader("📋 View Your Past Service Records")

client_name = st.text_input(
    "Enter your Name:"
)

if st.button("Show My Records"):

    if client_name:

        try:

            query = """
            SELECT
                vehicle_number,
                service_type,
                service_date,
                status,
                total_cost,
                review
            FROM services
            WHERE customer_name = %s
            """

            cursor.execute(query, (client_name,))
            data = cursor.fetchall()

            if data:

                df_client = pd.DataFrame(
                    data,
                    columns=[
                        "Vehicle Number",
                        "Service Type",
                        "Service Date",
                        "Status",
                        "Estimated Cost",
                        "Review"
                    ]
                )

                st.dataframe(df_client)

            else:
                st.info("No records found.")

        except Exception as e:
            st.error(f"Error loading records: {e}")

    else:
        st.warning("Please enter your name.")

# --- Close Connection ---
conn.close()