import streamlit as st
import mysql.connector
from datetime import date

# MySQL connection
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='12345',
    database='vehicle_service'
)
cursor = conn.cursor()

# Streamlit app setup
st.set_page_config(page_title="Vehicle Service Entry", page_icon="🚘", layout="centered")

st.markdown(
    """
    <style>
    .title {
        font-size: 2.5em;
        text-align: center;
        color: #2b6cb0;
        margin-bottom: 20px;
        animation: fadeInDown 1s ease-out;
    }

    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .stButton>button {
        background-color: #2b6cb0;
        color: white;
        padding: 0.75em 1.5em;
        border-radius: 0.5em;
        font-size: 1em;
        transition: background-color 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #2c5282;
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="title">🚘 Vehicle Service Entry</div>', unsafe_allow_html=True)

# Form
with st.form("service_form"):
    name = st.text_input("Customer Name")
    vehicle = st.text_input("Vehicle Number")
    service_type = st.selectbox("Service Type", [
        "Select", "Oil Change", "Engine Repair", "Tire Replacement", "Full Service"
    ])
    service_date = st.date_input("Service Date", value=date.today())

    submitted = st.form_submit_button("Submit")

    if submitted:
        if name and vehicle and service_type != "Select":
            query = """
            INSERT INTO services (customer_name, vehicle_number, service_type, service_date)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute("SELECT customer_name, vehicle_number, service_type, service_date FROM service123")

            conn.commit()
            st.success("✅ Service entry saved successfully!")
        else:
            st.error("Please fill all fields correctly.")

# Optional: Show table of previous entries
with st.expander("📋 View All Service Records"):
    cursor.execute("SELECT customer_name, vehicle_number, service_type, service_date FROM services ORDER BY id DESC")
    data = cursor.fetchall()
    if data:
        st.table(data)
    else:
        st.info("No entries found.")
