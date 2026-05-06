import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date

# --- Database Connection ---
try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345",
        database="vehicle_service"
    )
    cursor = conn.cursor()
except mysql.connector.Error as err:
    st.error(f"Database connection error: {err}")
    st.stop()

# --- Page Config ---
st.set_page_config(page_title="Vehicle Service Dashboard", layout="wide")

# --- Styling ---
st.markdown("""
<style>
:root {
    --primary-color: #2b6cb0;
    --pending-color: #e53e3e;
    --progress-color: #d69e2e;
    --completed-color: #38a169;
}
[data-testid="stAppViewContainer"] {
    background: linear-gradient(145deg, #0f172a, #1e293b);
    color: white;
}
[data-theme="light"] [data-testid="stAppViewContainer"] {
    background: #f8fafc;
    color: #1a202c;
}
.title {
    text-align: center;
    font-size: 2.8em;
    font-weight: 800;
    color: var(--primary-color);
    margin-bottom: 25px;
}
.card {
    background-color: rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 15px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.25);
    backdrop-filter: blur(10px);
    transition: all 0.25s;
}
[data-theme="light"] .card {
    background-color: black;
    color: black;
}
.card:hover { transform: scale(1.02); }
.status-badge {
    padding: 6px 12px;
    border-radius: 15px;
    font-weight: 600;
    color: white;
}
.status-Pending { background-color: var(--pending-color); }
.status-In\\ Progress { background-color: var(--progress-color); }
.status-Completed { background-color: var(--completed-color); }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🚗 Vehicle Service Management Dashboard</div>', unsafe_allow_html=True)

# --- Ensure Columns Exist ---
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
    st.warning(f"⚠️ Table structure update failed: {e}")

# --- Fixed Costs for Services ---
SERVICE_COSTS = {
    "Oil Change": 1200,
    "Engine Repair": 3000,
    "Tire Replacement": 1800,
    "Full Service": 4000
}

# --- Service Registration Form ---
with st.expander("📝 Register New Service", expanded=False):
    with st.form("service_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("Customer Name")
        with col2:
            vehicle = st.text_input("Vehicle Number (e.g. KA27M2345)")
        with col3:
            service_type = st.selectbox("Service Type", [
                "Select", "Oil Change", "Engine Repair", "Tire Replacement", "Full Service"
            ])
        service_date = st.date_input("Service Date", value=date.today())

        # Auto show fixed cost
        if service_type != "Select":
            fixed_cost = SERVICE_COSTS.get(service_type, 0)
            st.info(f"💰 Fixed Cost for {service_type}: ₹{fixed_cost}")
        else:
            fixed_cost = 0

        submitted = st.form_submit_button("Add Service")

        if submitted:
            if name and vehicle and service_type != "Select":
                try:
                    insert_query = """
                        INSERT INTO services (customer_name, vehicle_number, service_type, service_date, status, total_cost)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (name, vehicle, service_type, service_date, "Pending", fixed_cost))
                    conn.commit()
                    st.success("✅ Service registered successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.warning("Please fill out all fields.")

# --- View and Manage Services ---
st.markdown("### 📋 All Service Records")

try:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, customer_name, vehicle_number, service_type, service_date, status, total_cost, review 
        FROM services ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    cursor.close()

    if rows:
        df = pd.DataFrame(rows, columns=[
            "ID", "Customer Name", "Vehicle Number", "Service Type", "Service Date", "Status", "Total Cost (₹)", "Review"
        ])

        for _, row in df.iterrows():
            id_, name, vehicle, s_type, s_date, status, cost, review = row

            st.markdown(f"""
                <div class="card">
                    <b>Customer:</b> {name}<br>
                    <b>Vehicle:</b> {vehicle}<br>
                    <b>Service:</b> {s_type}<br>
                    <b>Date:</b> {s_date}<br>
                    <b>Cost:</b> ₹{cost if cost else 0}<br>
                    <span class="status-badge status-{status}">{status}</span><br>
                    <b>Review:</b> {review if review else 'No review yet'}
                </div>
            """, unsafe_allow_html=True)

            # --- Action Buttons ---
            cols = st.columns(4)
            with cols[0]:
                if st.button("🔴 Pending", key=f"pending_{id_}"):
                    cursor = conn.cursor()
                    cursor.execute("UPDATE services SET status=%s WHERE id=%s", ("Pending", id_))
                    conn.commit()
                    cursor.close()
                    st.success(f"Set to Pending for {vehicle}")
                    st.rerun()

            with cols[1]:
                if st.button("🟡 In Progress", key=f"progress_{id_}"):
                    cursor = conn.cursor()
                    cursor.execute("UPDATE services SET status=%s WHERE id=%s", ("In Progress", id_))
                    conn.commit()
                    cursor.close()
                    st.success(f"Set to In Progress for {vehicle}")
                    st.rerun()

            with cols[2]:
                if st.button("🟢 Completed", key=f"completed_{id_}"):
                    cursor = conn.cursor()
                    cursor.execute("UPDATE services SET status=%s WHERE id=%s", ("Completed", id_))
                    conn.commit()
                    cursor.close()
                    st.success(f"Marked Completed for {vehicle}")
                    st.rerun()

            # --- Delete Completed Records ---
            with cols[3]:
                if status == "Completed":
                    if f"confirm_delete_{id_}" not in st.session_state:
                        st.session_state[f"confirm_delete_{id_}"] = False

                    if not st.session_state[f"confirm_delete_{id_}"]:
                        if st.button("🗑 Delete", key=f"delete_{id_}"):
                            st.session_state[f"confirm_delete_{id_}"] = True
                            st.rerun()
                    else:
                        st.warning(f"Confirm delete for {vehicle}?")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Yes, Delete", key=f"yes_{id_}"):
                                del_cur = conn.cursor()
                                del_cur.execute("DELETE FROM services WHERE id=%s", (id_,))
                                conn.commit()
                                del_cur.close()
                                del st.session_state[f"confirm_delete_{id_}"]
                                st.success(f"Deleted record for {vehicle}")
                                st.rerun()
                        with c2:
                            if st.button("❌ Cancel", key=f"cancel_{id_}"):
                                st.session_state[f"confirm_delete_{id_}"] = False
                                st.rerun()
            st.markdown("---")

    else:
        st.info("No records found.")
except Exception as e:
    st.error(f"❌ Error loading records: {e}")

conn.close()
