import streamlit as st
import pandas as pd
import plotly.express as px
import os
import uuid
from datetime import datetime
import re

# Set page configuration for a premium, wide dashboard look
st.set_page_config(
    page_title="CitizenVoiz | Community Complaint Tracker",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling: glassmorphism, gradients, clean cards, and polished text
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main-title {
        background: linear-gradient(135deg, #FF4B4B 0%, #FF8F8F 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        color: #8C96A6;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    .card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
        margin-bottom: 1rem;
    }
    
    .metric-title {
        font-size: 0.9rem;
        color: #8C96A6;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-top: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# File names for storing complaints data
CSV_FILE = "complaints.csv"
TXT_LOG_FILE = "complaints_log.txt"

# ----------------------------------------------------
# DATA STORAGE & LOGGING HELPERS (TXT & CSV Handling, try/except)
# ----------------------------------------------------

def initialize_files():
    """
    Ensures that the CSV and TXT files exist with proper structures.
    Uses try/except block to handle file creation errors.
    """
    try:
        # Check and initialize complaints CSV
        if not os.path.exists(CSV_FILE):
            df = pd.DataFrame(columns=[
                "id", "reporter", "contact", "category", 
                "location", "description", "severity", "status", "timestamp"
            ])
            df.to_csv(CSV_FILE, index=False)
            write_to_txt_log("SYSTEM", "Initialized complaints database CSV file.")
            
        # Check and initialize TXT log file
        if not os.path.exists(TXT_LOG_FILE):
            with open(TXT_LOG_FILE, "w") as f:
                f.write(f"[{datetime.now()}] SYSTEM: Initialized system audit TXT log file.\n")
    except Exception as e:
        st.error(f"Initialization Error: {e}")

def write_to_txt_log(action_by, action_description):
    """
    Logs system audit events to a raw text file (TXT Handling, try/except).
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] USER: {action_by} | ACTION: {action_description}\n"
    try:
        with open(TXT_LOG_FILE, "a") as f:
            f.write(log_line)
    except IOError as e:
        # Gracefully handle file write errors
        st.warning(f"Failed to write to TXT log file: {e}")

def load_complaints_data():
    """
    Loads complaints data from CSV into a Pandas DataFrame.
    Uses try/except to handle parsing errors or corrupted files.
    """
    initialize_files()
    try:
        df = pd.read_csv(CSV_FILE)
        # Ensure ID column is string
        if not df.empty:
            df["id"] = df["id"].astype(str)
        return df
    except Exception as e:
        st.error(f"Error loading complaints database: {e}. Re-initializing database.")
        # Re-initialize file to avoid crash
        df = pd.DataFrame(columns=[
            "id", "reporter", "contact", "category", 
            "location", "description", "severity", "status", "timestamp"
        ])
        df.to_csv(CSV_FILE, index=False)
        return df

def save_complaint_record(complaint_dict):
    """
    Appends a new complaint dictionary record to the CSV file (Dictionaries, try/except).
    """
    try:
        df = load_complaints_data()
        new_row = pd.DataFrame([complaint_dict])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(CSV_FILE, index=False)
        
        # Log to the audit log (TXT handling)
        write_to_txt_log(
            complaint_dict["reporter"], 
            f"Created complaint ID {complaint_dict['id']} under Category '{complaint_dict['category']}'."
        )
        return True
    except Exception as e:
        st.error(f"Failed to save complaint to database: {e}")
        return False

def update_complaint_status(complaint_id, new_status, updated_by="Admin"):
    """
    Updates the status of a specific complaint using pandas filtering and selection.
    """
    try:
        df = load_complaints_data()
        # Find index of the matching complaint
        idx = df.index[df['id'] == complaint_id]
        if not idx.empty:
            old_status = df.loc[idx[0], 'status']
            df.loc[idx[0], 'status'] = new_status
            df.to_csv(CSV_FILE, index=False)
            write_to_txt_log(
                updated_by, 
                f"Updated status of complaint {complaint_id} from '{old_status}' to '{new_status}'."
            )
            return True
        else:
            st.error(f"Complaint with ID {complaint_id} not found.")
            return False
    except Exception as e:
        st.error(f"Failed to update complaint status: {e}")
        return False

# ----------------------------------------------------
# VALIDATION LOGIC
# ----------------------------------------------------

def validate_complaint_inputs(name, contact, location, description):
    """
    Validates form input variables, raising value errors for problems (Validation, try/except).
    """
    errors = []
    
    # 1. Validate Reporter Name (at least 2 letters, alphabetic + spaces check)
    name_clean = name.strip()
    if len(name_clean) < 2:
        errors.append("Reporter Name must be at least 2 characters long.")
    elif not re.match(r"^[A-Za-z\s]+$", name_clean):
        errors.append("Reporter Name should only contain letters and spaces.")
        
    # 2. Validate Contact Number (exactly 10 digits)
    contact_clean = contact.strip()
    if not re.match(r"^\d{10}$", contact_clean):
        errors.append("Contact Number must be exactly 10 digits (e.g., 9876543210).")
        
    # 3. Validate Location (non-empty)
    if len(location.strip()) < 3:
        errors.append("Location/Address must be at least 3 characters long.")
        
    # 4. Validate Description (at least 10 characters to ensure meaningful reports)
    if len(description.strip()) < 10:
        errors.append("Description must be at least 10 characters long to explain the issue clearly.")
        
    if errors:
        raise ValueError("\n".join(errors))

# ----------------------------------------------------
# STREAMLIT UI LAYOUT & FLOW
# ----------------------------------------------------

# Header Title Section
st.markdown('<div class="main-title">CitizenVoiz</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Empowering communities to report, track, and resolve local issues.</div>', unsafe_allow_html=True)

# Initialize files
initialize_files()

# Sidebar: Create/Submit a new complaint
st.sidebar.markdown("### 📝 File a New Complaint")
with st.sidebar.form(key="complaint_form", clear_on_submit=True):
    reporter_name = st.text_input("Reporter Name", placeholder="e.g. John Doe")
    contact_number = st.text_input("Contact Number", placeholder="10-digit mobile number")
    
    category = st.selectbox(
        "Issue Category",
        ["Pothole", "Garbage Accumulation", "Streetlight Failure", "Water Supply Pipe Leak", "Stray Animals", "Other"]
    )
    
    severity = st.select_slider(
        "Severity Level",
        options=["Low", "Medium", "High"],
        value="Medium"
    )
    
    location = st.text_input("Incident Location / Address", placeholder="e.g. 5th Main St, Block C")
    description = st.text_area("Detailed Description", placeholder="Please describe the issue in detail...")
    
    submit_button = st.form_submit_button(label="Submit Report")

# Form Submission Processing (try/except, Dictionaries, Validation)
if submit_button:
    try:
        # Perform validation on form fields
        validate_complaint_inputs(reporter_name, contact_number, location, description)
        
        # Build the complaint dictionary (Dictionary concept)
        complaint_id = str(uuid.uuid4())[:8].upper()
        new_complaint = {
            "id": complaint_id,
            "reporter": reporter_name.strip(),
            "contact": contact_number.strip(),
            "category": category,
            "location": location.strip(),
            "description": description.strip(),
            "severity": severity,
            "status": "Pending",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save complaint using helper (TXT + CSV handling)
        if save_complaint_record(new_complaint):
            st.sidebar.success(f"🎉 Complaint submitted successfully! ID: {complaint_id}")
            # Rerun the app to update the dashboard instantly
            st.rerun()
            
    except ValueError as val_error:
        # Show specific validation warnings to the user
        st.sidebar.error(f"⚠️ Validation Error(s):\n{str(val_error)}")
    except Exception as e:
        # Catch-all exception handling for unexpected errors
        st.sidebar.error(f"❌ An error occurred: {e}")

# Load active complaints database
df_complaints = load_complaints_data()

# ----------------------------------------------------
# MAIN DASHBOARD TABS
# ----------------------------------------------------

tab_dashboard, tab_explorer, tab_logs = st.tabs([
    "📊 Analytics Dashboard", 
    "🔍 Search & Track", 
    "📜 System Audit Log"
])

# ---- TAB 1: DASHBOARD SUMMARY (Extended Visual Analytics) ----
with tab_dashboard:
    if df_complaints.empty:
        st.info("No complaints have been reported yet. Use the sidebar to submit the first complaint!")
    else:
        # 1. Metrics Grid
        total_complaints = len(df_complaints)
        resolved_count = len(df_complaints[df_complaints["status"] == "Resolved"])
        in_progress_count = len(df_complaints[df_complaints["status"] == "In Progress"])
        pending_count = len(df_complaints[df_complaints["status"] == "Pending"])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="card">
                <div class="metric-title">📋 Total Filed</div>
                <div class="metric-value">{total_complaints}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="card">
                <div class="metric-title">⏳ Pending</div>
                <div class="metric-value" style="color: #FF5A5A;">{pending_count}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="card">
                <div class="metric-title">⚙️ In Progress</div>
                <div class="metric-value" style="color: #FFAE34;">{in_progress_count}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"""
            <div class="card">
                <div class="metric-title">✅ Resolved</div>
                <div class="metric-value" style="color: #2ED573;">{resolved_count}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        
        # 2. Charts Section (Pandas Grouping & Plotly Visuals)
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("📈 Issues by Category")
            # Intermediate: Count issue types using Pandas
            category_counts = df_complaints["category"].value_counts().reset_index()
            category_counts.columns = ["Category", "Count"]
            
            fig_category = px.bar(
                category_counts,
                x="Count",
                y="Category",
                orientation='h',
                color="Count",
                color_continuous_scale="Reds",
                template="plotly_dark",
                labels={"Count": "Number of Complaints", "Category": "Issue Category"}
            )
            fig_category.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False,
                margin=dict(l=20, r=20, t=10, b=10),
                height=300
            )
            st.plotly_chart(fig_category, use_container_width=True)
            
        with col_chart2:
            st.subheader("🎯 Severity & Resolution Distribution")
            # Pie Chart showing Status distribution
            status_counts = df_complaints["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            
            fig_status = px.pie(
                status_counts,
                names="Status",
                values="Count",
                hole=0.4,
                color="Status",
                color_discrete_map={
                    "Pending": "#FF5A5A",
                    "In Progress": "#FFAE34",
                    "Resolved": "#2ED573"
                },
                template="plotly_dark"
            )
            fig_status.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=10, b=10),
                height=300
            )
            st.plotly_chart(fig_status, use_container_width=True)

        st.markdown("---")
        
        # 3. Severity Breakdown Details
        st.subheader("⚠️ Severity Analysis")
        severity_counts = df_complaints.groupby(["category", "severity"]).size().reset_index(name="count")
        
        fig_severity = px.bar(
            severity_counts,
            x="category",
            y="count",
            color="severity",
            title="Severity Level breakdown across Categories",
            labels={"category": "Category", "count": "Count", "severity": "Severity Level"},
            color_discrete_map={"High": "#FF4B4B", "Medium": "#FFAE34", "Low": "#2ED573"},
            template="plotly_dark",
            barmode="group"
        )
        fig_severity.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=40, b=10),
            height=320
        )
        st.plotly_chart(fig_severity, use_container_width=True)

# ---- TAB 2: DATA EXPLORER & MANAGEMENT ----
with tab_explorer:
    st.subheader("🔍 Search, Filter, and Manage Complaints")
    
    if df_complaints.empty:
        st.info("No complaint reports available to browse.")
    else:
        # Search & Filter controls
        col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
        with col_f1:
            search_query = st.text_input("🔍 Search by Reporter, Description, or ID", placeholder="Type to search...")
        with col_f2:
            status_filter = st.selectbox("Filter Status", ["All", "Pending", "In Progress", "Resolved"])
        with col_f3:
            severity_filter = st.selectbox("Filter Severity", ["All", "Low", "Medium", "High"])
            
        # Apply Pandas filtering logic based on input filters
        filtered_df = df_complaints.copy()
        
        if search_query:
            filtered_df = filtered_df[
                filtered_df["id"].str.contains(search_query, case=False, na=False) |
                filtered_df["reporter"].str.contains(search_query, case=False, na=False) |
                filtered_df["description"].str.contains(search_query, case=False, na=False) |
                filtered_df["location"].str.contains(search_query, case=False, na=False)
            ]
            
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df["status"] == status_filter]
            
        if severity_filter != "All":
            filtered_df = filtered_df[filtered_df["severity"] == severity_filter]
            
        # Display the interactive dataframe
        st.markdown(f"**Showing {len(filtered_df)} filtered results out of {len(df_complaints)} total complaints**")
        
        # Display styled dataframe
        st.dataframe(
            filtered_df[[
                "id", "timestamp", "reporter", "contact", 
                "category", "location", "severity", "status", "description"
            ]],
            use_container_width=True,
            hide_index=True
        )
        
        # Manage and update status section
        st.markdown("### ⚙️ Admin Actions: Resolve & Update Status")
        col_act1, col_act2, col_act3 = st.columns([1, 1, 1])
        
        with col_act1:
            selected_id = st.selectbox("Select Complaint ID to Update", filtered_df["id"].tolist() if not filtered_df.empty else ["None"])
            
        with col_act2:
            action_status = st.selectbox("Set New Status", ["Pending", "In Progress", "Resolved"])
            
        with col_act3:
            update_button = st.button("Apply Status Change", use_container_width=True)
            
        if update_button:
            if selected_id == "None":
                st.error("No valid complaint selected.")
            else:
                if update_complaint_status(selected_id, action_status, updated_by="Admin Console"):
                    st.success(f"Status of complaint {selected_id} updated to {action_status}!")
                    st.rerun()

        # CSV Export function
        st.markdown("---")
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Filtered Data to CSV",
            data=csv_data,
            file_name=f"filtered_complaints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# ---- TAB 3: SYSTEM AUDIT LOG (TXT Handling) ----
with tab_logs:
    st.subheader("📜 System Audit Trail (TXT Log Viewer)")
    st.markdown("This section reads the raw audit log from `complaints_log.txt` on the disk, highlighting system events and user actions.")
    
    # Check if TXT file exists and display it
    if os.path.exists(TXT_LOG_FILE):
        try:
            with open(TXT_LOG_FILE, "r") as f:
                logs = f.readlines()
                
            # Show logs in reverse chronological order (latest events first)
            logs.reverse()
            
            # Format text log nicely in a code block or markdown area
            log_text = "".join(logs)
            st.text_area("Audit Logs:", value=log_text, height=400, disabled=True)
            
            # Button to clear log if needed
            if st.button("Clear Log History"):
                with open(TXT_LOG_FILE, "w") as f:
                    f.write(f"[{datetime.now()}] SYSTEM: Cleared log history.\n")
                st.success("Audit log history has been cleared.")
                st.rerun()
                
        except Exception as e:
            st.error(f"Failed to read TXT audit log file: {e}")
    else:
        st.info("No audit log file found. Create a complaint to start logging.")
