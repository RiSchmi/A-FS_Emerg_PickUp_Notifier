import streamlit as st
import datetime
import time
from config import TelegramPickupBot

# --- Page Config ---
st.set_page_config(
    page_title="Food Sharing Pickup",
    page_icon="🍲",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS ---
st.markdown("""
<style>
    .main { padding: 2rem; }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: bold;
    }
    .back-button>button {
        background-color: #f5f5f5;
        color: #333;
        border: 1px solid #ddd;
    }
    .progress-container { margin-bottom: 30px; }
    .header-container { margin-bottom: 40px; }
    .message-box {
        background-color: #f1f8e9;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Defaults ---
st.session_state.setdefault('page', 1)
st.session_state.setdefault('location', "")
st.session_state.setdefault('remarks', "")
st.session_state.setdefault('date', "Today")
st.session_state.setdefault('pickup_time', "")
st.session_state.setdefault('contact_number', "")
st.session_state.setdefault('submitted', False)
st.session_state.setdefault('showing_thank_you', False)
st.session_state.setdefault('submission_success', False)
st.session_state.setdefault('submission_error', None)
st.session_state.setdefault('wait_minutes', 15)

# --- Navigation Functions ---
def next_page(): st.session_state.page += 1
def previous_page(): st.session_state.page -= 1
def go_to_page(n): st.session_state.page = n
def reset_form():
    st.session_state.update({
        'location': "", 'remarks': "", 'date': "Today",
        'pickup_time': "", 'contact_number': "",
        'submitted': False, 'page': 1, 'showing_thank_you': False,
        'submission_success': False, 'submission_error': None
    })

def process_submission():
    st.session_state.submitted = True
    try:
        TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
        GROUP_CHAT_ID = st.secrets["GROUP_CHAT_ID"]
        pickup_bot = TelegramPickupBot(token=TOKEN, chat_id=GROUP_CHAT_ID)

        date_str = st.session_state.date
        if date_str == "Today":
            date_str = datetime.datetime.now().strftime("%A, %d %B")

        result = pickup_bot.run_pickup_workflow(
            location=st.session_state.location or "Not specified",
            remarks=st.session_state.remarks,
            date=date_str,
            pick_up_time=st.session_state.pickup_time,
            contact_number=st.session_state.contact_number,
            wait_minutes=st.session_state.wait_minutes
        )
        st.session_state.submission_success = result
    except Exception as e:
        st.session_state.submission_error = str(e)
        st.session_state.submission_success = False

# --- Progress Bar ---
total_pages = 4
progress = st.session_state.page / total_pages
st.markdown('<div class="progress-container">', unsafe_allow_html=True)
st.progress(progress)
st.markdown(f'<p style="text-align:right; font-size:0.8em;">Step {st.session_state.page} of {total_pages}</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- Current Hour for Filtering ---
current_hour = datetime.datetime.now().hour

# === PAGE 1: DATE SELECTION ===
if st.session_state.page == 1:
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.title("Thank you for sharing leftover food! When do you have leftovers?")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("By providing your details, multiple Foodsavers will be informed and someone will reach out to you within 60 minutes!")

    def choose_today():
        st.session_state.date = "Today"
        next_page()

    def choose_another_day():
        go_to_page(1.5)

    col1, col2 = st.columns(2)
    with col1:
        st.button("Today", on_click=choose_today, use_container_width=True)
    with col2:
        st.button("Another Day", on_click=choose_another_day, use_container_width=True)

# === PAGE 1.5: DATE PICKER ===
elif st.session_state.page == 1.5:
    st.title("Select Date")

    min_date = datetime.date.today() + datetime.timedelta(days=1)
    max_date = datetime.date.today() + datetime.timedelta(days=14)
    date = st.date_input("Select a date:", min_value=min_date, max_value=max_date)
    st.session_state.date = date.strftime("%A, %d %B")

    col1, col2 = st.columns(2)
    with col1:
        st.button("Back", on_click=lambda: go_to_page(1), use_container_width=True)
    with col2:
        st.button("Continue", on_click=lambda: go_to_page(2), use_container_width=True)

# === PAGE 2: PICK-UP TIME ===
elif st.session_state.page == 2:
    st.title("Pick-up Time")
    st.markdown("This can be an estimation. You can confirm the details once an available Foodsaver is reaching out to you!")

    # Time Options
    time_options = []
    if st.session_state.date == "Today":
        if current_hour < 14: time_options.append("Before 14:00")
        if current_hour < 16: time_options.append("14:00 - 16:00")
        if current_hour < 18: time_options.append("16:00 - 18:00")
        if current_hour < 20: time_options.append("18:00 - 20:00")
        if current_hour < 22: time_options.append("20:00 - 22:00")
        time_options.append("After 22:00")
    else:
        time_options = [
            "Before 14:00", "14:00 - 16:00", "16:00 - 18:00",
            "18:00 - 20:00", "20:00 - 22:00", "After 22:00"
        ]

    cols = st.columns(2)
    for i, label in enumerate(time_options):
        def set_time(val=label):
            st.session_state.pickup_time = val
            next_page()
        with cols[i % 2]:
            st.button(label, on_click=set_time, key=f"time_{label}", use_container_width=True)

    st.button("Back", on_click=lambda: go_to_page(1), use_container_width=True)

# === PAGE 3: LOCATION + REMARKS ===
elif st.session_state.page == 3:
    st.title("Location (Optional)")
    location_input = st.text_input("Where is the food located?", value=st.session_state.location,
                                   placeholder="e.g., Otaniemi Campus, A-Block")
    st.session_state.location = location_input

    st.title("Additional Information (Optional)")
    remarks_input = st.text_input("Do you want to provide any additional information?", value=st.session_state.remarks,
                                  placeholder="e.g., amount or kind of food")
    st.session_state.remarks = remarks_input

    col1, col2 = st.columns(2)
    with col1:
        st.button("Back", on_click=lambda: go_to_page(2), use_container_width=True)
    with col2:
        st.button("Continue", on_click=lambda: go_to_page(4), use_container_width=True)

# === PAGE 4: CONTACT INFO + SUBMIT ===
elif st.session_state.page == 4:
    st.title("Contact Information")
    st.markdown("""
    **How your number is processed:**

    We will notify potential Foodsavers. Only one person receives your phone number after confirming the pick-up. 
    Your number will be shared and automatically deleted after 15 minutes.
    """)

    st.text_input("Phone Number", key="contact_number", placeholder="e.g., +358 40 1234567")

    col1, col2 = st.columns(2)
    if not st.session_state.submitted and not st.session_state.showing_thank_you:
        with col1:
            st.button("Back", on_click=previous_page, use_container_width=True)

        def on_submit():
            if st.session_state.contact_number.strip():
                st.session_state.showing_thank_you = True

        with col2:
            st.button("Submit", on_click=on_submit, use_container_width=True, disabled=not st.session_state.contact_number.strip())

        st.markdown("""
        **Not contacted within 60 minutes?**
        [Share leftovers in this Telegram Group](https://t.me/+2NxhCayA8bg4ODlk)
        """)

    elif st.session_state.showing_thank_you and not st.session_state.submitted:
        st.success("Thank you! Submission completed.")
        placeholder = st.empty()
        placeholder.info("We are reaching out to potential Foodsaver...")
        time.sleep(2)
        process_submission()
        placeholder.empty()

    if st.session_state.submitted:
        if st.session_state.submission_error:
            st.error(f"There was an error: {st.session_state.submission_error}")
            if st.button("Try Again"):
                reset_form()
        elif st.session_state.submission_success:
            st.success("Someone is found. A Foodsaver will contact you soon.")
            st.markdown(f"""
            **Summary:**
            - **Date:** {st.session_state.date}
            - **Time:** {st.session_state.pickup_time}
            - **Location:** {st.session_state.location or "Not specified"}
            """)
        else:
            st.warning(f"No Foodsavers were available within {st.session_state.wait_minutes} minutes. Try again later or [use Telegram](https://t.me/+2NxhCayA8bg4ODlk).")
            if st.button("Try Again"):
                reset_form()
