import datetime
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="DNA: The Doctor Blueprint", page_icon="🧬", layout="wide"
)

# Custom Styling (Dark Gaming / Medical Theme)
st.markdown(
    """
    <style>
    .main { background-color: #030712; color: #f3f4f6; }
    .stTextInput>div>div>input { background-color: #111827; color: white; border: 1px solid #374151; }
    </style>
""",
    unsafe_allow_html=True,
)


# --- GOOGLE SHEETS CONNECTION SETUP ---
@st.cache_resource
def init_connection():
  scope = [
      "https://www.googleapis.com/auth/spreadsheets",
      "https://www.googleapis.com/auth/drive",
  ]
  creds_dict = dict(st.secrets["gcp_service_account"])
  if "private_key" in creds_dict:
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

  creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
  client = gspread.authorize(creds)
  return client


client = init_connection()
sheet_name = st.secrets["google_sheets"]["sheet_name"]
sh = client.open(sheet_name)

# --- LOAD STUDENTS DATA ---
try:
  students_worksheet = sh.worksheet("Students")
  students_data = students_worksheet.get_all_records()
except Exception:
  students_worksheet = sh.worksheet("Students")
  students_worksheet.update([
      [
          "Roll No",
          "Name",
          "Overall Points",
          "Test Score",
          "Tier",
          "Physics",
          "Chemistry",
          "Biology",
          "Weak Area",
          "Focus Action",
          "Mentor Remarks",
      ],
      [
          "666016",
          "Aryan Bangar",
          4850,
          505,
          "Tier A",
          "Strength",
          "Strength",
          "Strength",
          "None",
          "Maintain peak performance with advanced mock tests.",
          "Keep up consistent performance.",
      ],
  ])
  students_data = students_worksheet.get_all_records()

# --- LOAD & SANITIZE TASKS DATA ---
try:
  tasks_worksheet = sh.worksheet("Tasks")
  tasks_data = tasks_worksheet.get_all_records()
  if not tasks_data:
    tasks_worksheet.update([
        ["Date", "Task Description", "Points Weight", "Assigned To (Or ALL)"],
        [
            str(datetime.date.today()),
            "Complete 90 Biology NCERT Flashcards",
            50,
            "ALL",
        ],
    ])
    tasks_data = tasks_worksheet.get_all_records()
except Exception:
  tasks_worksheet = sh.add_worksheet(title="Tasks", rows=100, cols=5)
  tasks_worksheet.update([
      ["Date", "Task Description", "Points Weight", "Assigned To (Or ALL)"],
      [
          str(datetime.date.today()),
          "Complete 90 Biology NCERT Flashcards",
          50,
          "ALL",
      ],
  ])
  tasks_data = tasks_worksheet.get_all_records()

# App Header
st.title("🧬 DNA: THE DOCTOR BLUEPRINT")
st.caption("Doctor's NEET Academy — Secure Academic Management Portal")

# Convert DataFrames safely
df_students = pd.DataFrame(students_data)
if not df_students.empty:
  df_students = df_students.sort_values(
      by="Overall Points", ascending=False
  ).reset_index(drop=True)
  df_students.insert(0, "Rank", df_students.index + 1)

df_tasks = pd.DataFrame(tasks_data)

# Ensure columns and normalize values to prevent matching errors
expected_task_columns = [
    "Date",
    "Task Description",
    "Points Weight",
    "Assigned To (Or ALL)",
]
for col in expected_task_columns:
  if col not in df_tasks.columns:
    df_tasks[col] = ""

if not df_tasks.empty:
  df_tasks["Date"] = df_tasks["Date"].astype(str).str.split(" ").str[0].str.strip()
  df_tasks["Assigned To (Or ALL)"] = (
      df_tasks["Assigned To (Or ALL)"].astype(str).str.strip()
  )

# --- SIDEBAR NAVIGATION & AUTH ---
st.sidebar.header("🔒 Portal Access")
portal_mode = st.sidebar.radio(
    "Select View",
    ["Student Dashboard & Daily Tasks", "Master Monitor (Admin)"],
)

is_admin = False
if portal_mode == "Master Monitor (Admin)":
  passcode = st.sidebar.text_input("Enter Admin Passcode", type="password")
  if passcode == "yash2026":
    is_admin = True
    st.sidebar.success("🔓 Master Access Granted")
  elif passcode != "":
    st.sidebar.error("Incorrect Passcode")

# ==========================================
# 1. STUDENT DASHBOARD & ANALYTICS (READ-ONLY FOR STUDENTS)
# ==========================================
if portal_mode == "Student Dashboard & Daily Tasks" or not is_admin:
  st.subheader("🏆 Aspirant Leaderboard & Performance Metrics")

  if df_students.empty:
    st.warning("No aspirant records found.")
  else:
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Aspirants", len(df_students))
    col2.metric("Top Leader", df_students.iloc[0]["Name"])
    col3.metric("System Status", "🟢 Secured & Operational")

    st.markdown("---")

    for idx, row in df_students.iterrows():
      with st.container():
        c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 2])
        with c1:
          st.markdown(f"### `#{row['Rank']}`")
        with c2:
          st.markdown(f"**{row['Name']}**")
          st.caption(f"Roll: {row['Roll No']} | Tier: {row['Tier']}")
        with c3:
          st.markdown(f"🔥 **Points:** `{row['Overall Points']} pts`")
        with c4:
          st.markdown(f"📊 **Test Score:** `{row['Test Score']}`")
        with c5:
          st.markdown(f"⚠️ **Weak Area:** `{row['Weak Area']}`")
        st.divider()

    selected_student_name = st.selectbox(
        "Select Your Name to View Profile & Assigned Tasks:",
        df_students["Name"].tolist(),
    )
    student_info = df_students[
        df_students["Name"] == selected_student_name
    ].iloc[0]

    st.info(
        f"💡 **Mentor Remarks for {selected_student_name}:**"
        f" {student_info['Mentor Remarks']}"
    )

    st.markdown("### 📊 Subject Competency & Tactical Focus")
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Physics", student_info["Physics"])
    sc2.metric("Chemistry", student_info["Chemistry"])
    sc3.metric("Biology", student_info["Biology"])

    st.warning(
        f"🎯 **Manually Assigned Focus Action:** {student_info['Focus Action']}"
    )

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
      st.markdown("#### 🧪 Subject Balance Ratio")
      status_map = {"Strength": 3, "Average": 2, "Weakness": 1}
      sub_scores = [
          status_map.get(str(student_info["Physics"]), 2),
          status_map.get(str(student_info["Chemistry"]), 2),
          status_map.get(str(student_info["Biology"]), 2),
      ]
      fig, ax = plt.subplots(figsize=(4, 4))
      ax.pie(
          sub_scores,
          labels=["Physics", "Chemistry", "Biology"],
          autopct="%1.1f%%",
          colors=["#3b82f6", "#10b981", "#f59e0b"],
          startangle=90,
          textprops={"color": "white"},
      )
      fig.patch.set_facecolor("#030712")
      ax.set_facecolor("#030712")
      st.pyplot(fig)

    with col_chart2:
      st.markdown("#### 📋 Your Assigned Tasks (View Only)")
      selected_date = st.date_input(
          "Select Date to View Tasks", value=datetime.date.today()
      )

      if df_tasks.empty:
        st.info("No tasks scheduled.")
      else:
        filtered_tasks = df_tasks[
            (df_tasks["Date"] == str(selected_date))
            & (
                (df_tasks["Assigned To (Or ALL)"] == "ALL")
                | (df_tasks["Assigned To (Or ALL)"] == selected_student_name)
            )
        ]

        if filtered_tasks.empty:
          st.info(f"No tasks assigned for {selected_date}.")
        else:
          st.caption(
              "Complete these targets. Your mentor will verify and credit"
              " points."
          )
          for i, t_row in filtered_tasks.iterrows():
            st.markdown(
                f"- ✅ **{t_row['Task Description']}** `(+{t_row['Points Weight']}"
                " pts)`"
            )

# ==========================================
# 2. MASTER MONITOR ADMIN PORTAL (Admin Only)
# ==========================================
elif portal_mode == "Master Monitor (Admin)" and is_admin:
  st.subheader("🛠️ Master Administrative Control Panel")

  admin_tab1, admin_tab2, admin_tab3, admin_tab4, admin_tab5, admin_tab6 = (
      st.tabs([
          "✏️ Edit Profiles & Focus Actions",
          "👥 Register New Aspirant",
          "🗑️ Remove Student",
          "📅 Assign Date-Wise Tasks",
          "🗑️ Delete Tasks",
          "✅ Track & Credit Tasks",
      ])
  )

  with admin_tab1:
    st.subheader("✏️ Edit Individual Aspirant Metrics & Manual Focus Actions")
    if df_students.empty:
      st.info("No aspirant data available.")
    else:
      edit_student_name = st.selectbox(
          "Select Aspirant to Edit:", df_students["Name"].tolist()
      )
      student_obj = df_students[
          df_students["Name"] == edit_student_name
      ].iloc[0]

      with st.form("individual_student_edit_form"):
        ind_points = st.number_input(
            "Overall Points", value=int(student_obj["Overall Points"])
        )
        ind_score = st.number_input(
            "Recent Test Score", value=int(student_obj["Test Score"])
        )
        ind_tier = st.selectbox(
            "Tier",
            ["Tier A", "Tier B", "Tier C"],
            index=(
                ["Tier A", "Tier B", "Tier C"].index(student_obj["Tier"])
                if student_obj["Tier"] in ["Tier A", "Tier B", "Tier C"]
                else 0
            ),
        )
        ind_physics = st.selectbox(
            "Physics Status",
            ["Strength", "Average", "Weakness"],
            index=["Strength", "Average", "Weakness"].index(
                student_obj["Physics"]
            ),
        )
        ind_chem = st.selectbox(
            "Chemistry Status",
            ["Strength", "Average", "Weakness"],
            index=["Strength", "Average", "Weakness"].index(
                student_obj["Chemistry"]
            ),
        )
        ind_bio = st.selectbox(
            "Biology Status",
            ["Strength", "Average", "Weakness"],
            index=["Strength", "Average", "Weakness"].index(
                student_obj["Biology"]
            ),
        )
        ind_weak = st.text_input("Weak Area", value=student_obj["Weak Area"])
        ind_focus = st.text_input(
            "Manually Type Focus Action for Student",
            value=student_obj["Focus Action"],
        )
        ind_remarks = st.text_area(
            "Mentor Remarks / Feedback", value=student_obj["Mentor Remarks"]
        )

        save_ind_btn = st.form_submit_button("💾 Save & Update Records")
        if save_ind_btn:
          cell = students_worksheet.find(edit_student_name)
          row_idx = cell.row
          students_worksheet.update_cell(row_idx, 3, int(ind_points))
          students_worksheet.update_cell(row_idx, 4, int(ind_score))
          students_worksheet.update_cell(row_idx, 5, ind_tier)
          students_worksheet.update_cell(row_idx, 6, ind_physics)
          students_worksheet.update_cell(row_idx, 7, ind_chem)
          students_worksheet.update_cell(row_idx, 8, ind_bio)
          students_worksheet.update_cell(row_idx, 9, ind_weak)
          students_worksheet.update_cell(row_idx, 10, ind_focus)
          students_worksheet.update_cell(row_idx, 11, ind_remarks)

          st.success(
              f"Successfully updated records & focus action for"
              f" {edit_student_name}!"
          )
          st.rerun()

  with admin_tab2:
    st.subheader("👥 Register New Aspirant")
    with st.form("add_student_form"):
      new_name = st.text_input("Full Name")
      new_roll = st.text_input("Roll Number")
      new_tier = st.selectbox("Tier", ["Tier A", "Tier B", "Tier C"])
      new_points = st.number_input("Initial Overall Points", value=3000)
      new_score = st.number_input("Initial Test Score", value=400)
      new_physics = st.selectbox(
          "Physics Status", ["Strength", "Average", "Weakness"]
      )
      new_chem = st.selectbox(
          "Chemistry Status", ["Strength", "Average", "Weakness"]
      )
      new_bio = st.selectbox(
          "Biology Status", ["Strength", "Average", "Weakness"]
      )
      new_weak = st.text_input("Primary Weak Area", value="General Revision")
      new_focus = st.text_input(
          "Manual Focus Action", value="Complete daily targets"
      )
      new_rem = st.text_area(
          "Initial Remarks", value="Welcome to DNA: The Doctor Blueprint!"
      )

      submit_new_student = st.form_submit_button("➕ Register Aspirant")
      if submit_new_student and new_name and new_roll:
        students_worksheet.append_row([
            str(new_roll),
            str(new_name),
            int(new_points),
            int(new_score),
            str(new_tier),
            str(new_physics),
            str(new_chem),
            str(new_bio),
            str(new_weak),
            str(new_focus),
            str(new_rem),
        ])
        st.success(f"Successfully registered {new_name} into the portal!")
        st.rerun()

  with admin_tab3:
    st.subheader("🗑️ Remove Student from Database")
    if df_students.empty:
      st.info("No students available to remove.")
    else:
      remove_student_name = st.selectbox(
          "Select Aspirant to Remove:",
          df_students["Name"].tolist(),
          key="remove_student_box",
      )
      st.warning(
          f"⚠️ Are you sure you want to delete **{remove_student_name}** from"
          " the Google Sheet? This action cannot be undone."
      )

      if st.button("🗑️ Confirm & Delete Student"):
        try:
          cell = students_worksheet.find(remove_student_name)
          students_worksheet.delete_rows(cell.row)
          st.success(
              f"Successfully removed {remove_student_name} from the database!"
          )
          st.rerun()
        except Exception as e:
          st.error(f"Error removing student: {e}")

  with admin_tab4:
    st.subheader("📅 Assign Multiple Date-Wise Tasks")
    with st.form("add_date_task_form"):
      task_date = st.date_input("Assign For Date", value=datetime.date.today())
      task_desc = st.text_input("Task Description")
      task_pts = st.number_input("Points Weight", value=50)

      student_list_options = (
          ["ALL"] + df_students["Name"].tolist()
          if not df_students.empty
          else ["ALL"]
      )
      target_student = st.selectbox("Assign To", student_list_options)

      submit_date_task = st.form_submit_button("➕ Push Task to Cloud Worksheet")
      if submit_date_task and task_desc:
        if tasks_worksheet.row_count == 0 or not tasks_worksheet.get_all_values():
          tasks_worksheet.update([
              [
                  "Date",
                  "Task Description",
                  "Points Weight",
                  "Assigned To (Or ALL)",
              ]
          ])
        tasks_worksheet.append_row([
            str(task_date),
            str(task_desc),
            int(task_pts),
            str(target_student),
        ])
        st.success("Successfully assigned date-wise task to Google Sheets!")
        st.rerun()

  with admin_tab5:
    st.subheader("🗑️ Delete Incorrectly Assigned Tasks")
    if df_tasks.empty:
      st.info("No tasks available to delete.")
    else:
      task_options = []
      for idx, t_row in df_tasks.iterrows():
        task_options.append(
            f"Row {idx+2} | Date: {t_row['Date']} | Desc:"
            f" {t_row['Task Description']} | Assigned To:"
            f" {t_row['Assigned To (Or ALL)']}"
        )

      selected_task_to_delete = st.selectbox(
          "Select Task to Delete:", task_options
      )
      if st.button("🗑️ Delete Selected Task"):
        selected_idx = task_options.index(selected_task_to_delete)
        # Row index in Google Sheets is dataframe index + 2 (since header is row 1)
        row_to_delete = selected_idx + 2
        tasks_worksheet.delete_rows(row_to_delete)
        st.success("Successfully deleted task from Google Sheets!")
        st.rerun()

  with admin_tab6:
    st.subheader(
        "✅ Verify Task Completion & Automatically Credit Points (Admin Only)"
    )
    if df_students.empty:
      st.info("No students available.")
    else:
      verify_student_name = st.selectbox(
          "Select Aspirant to Evaluate:",
          df_students["Name"].tolist(),
          key="verify_student",
      )
      verify_date = st.date_input(
          "Select Date for Tasks Verification",
          value=datetime.date.today(),
          key="verify_date",
      )

      student_verify_obj = df_students[
          df_students["Name"] == verify_student_name
      ].iloc[0]

      if df_tasks.empty:
        st.info("No tasks found in the database.")
      else:
        verify_filtered_tasks = df_tasks[
            (df_tasks["Date"] == str(verify_date))
            & (
                (df_tasks["Assigned To (Or ALL)"] == "ALL")
                | (df_tasks["Assigned To (Or ALL)"] == verify_student_name)
            )
        ]

        if verify_filtered_tasks.empty:
          st.info(
              f"No tasks found for {verify_student_name} on {verify_date}."
          )
        else:
          st.markdown(
              f"**Tick tasks completed by {verify_student_name} (Points will be"
              " credited automatically):**"
          )

          if "task_status_log" not in st.session_state:
            st.session_state.task_status_log = set()

          for j, t_row in verify_filtered_tasks.iterrows():
            t_label = (
                f"{t_row['Task Description']} (+{t_row['Points Weight']} pts)"
            )
            task_unique_key = f"admin_task_{verify_student_name}_{verify_date}_{j}_{t_row['Task Description']}"

            is_checked = st.checkbox(t_label, key=task_unique_key)

            if (
                is_checked
                and task_unique_key not in st.session_state.task_status_log
            ):
              st.session_state.task_status_log.add(task_unique_key)
              current_pts = int(student_verify_obj["Overall Points"])
              pts_to_add = int(t_row["Points Weight"])
              updated_pts = current_pts + pts_to_add

              cell = students_worksheet.find(verify_student_name)
              students_worksheet.update_cell(cell.row, 3, updated_pts)
              st.success(
                  f"⚡ Automatically credited +{pts_to_add} points to"
                  f" {verify_student_name}!"
              )
              st.rerun()