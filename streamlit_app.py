import streamlit as st
import datetime
import time
from config import TelegramPickupBot
import os


# Configure page settings
st.set_page_config(
    page_title="Food Sharing Pickup",
    page_icon="🍲",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Add custom CSS for better styling
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
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
    .progress-container {
        margin-bottom: 30px;
    }
    .header-container {
        margin-bottom: 40px;
    }
    .message-box {
        background-color: #f1f8e9;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'page' not in st.session_state:
    st.session_state.page = 1
if 'location' not in st.session_state:
    st.session_state.location = ""
if 'remarks' not in st.session_state:
    st.session_state.remarks = ""
if 'date' not in st.session_state:
    st.session_state.date = "Today"
if 'pickup_time' not in st.session_state:
    st.session_state.pickup_time = ""
if 'contact_number' not in st.session_state:
    st.session_state.contact_number = ""
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# Functions to navigate between pages
def next_page():
    st.session_state.page += 1

def previous_page():
    st.session_state.page -= 1

def go_to_page(page_number):
    st.session_state.page = page_number

def reset_form():
    # Reset only the form fields, not the page state
    st.session_state.location = ""
    st.session_state.remarks = ""
    st.session_state.date = "Today"
    st.session_state.pickup_time = ""
    st.session_state.contact_number = ""
    st.session_state.submitted = False
    # Reset to first page
    st.session_state.page = 1

def process_submission():
    st.session_state.submitted = True
    # Here you would call your TelegramPickupBot
    try:
        # Initialize the bot with your credentials
        
        TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
        GROUP_CHAT_ID = st.secrets["GROUP_CHAT_ID"]
        
        pickup_bot = TelegramPickupBot(token=TOKEN, chat_id=GROUP_CHAT_ID)
        
        # Format date string properly
        date_str = st.session_state.date
        if date_str == "Today":
            date_str = datetime.datetime.now().strftime("%A, %d %B")
        
        # Set wait minutes (time until no Saver is found)
        wait_minutes = 15  # Adjust this as needed
        
        # Run the complete workflow
        result = pickup_bot.run_pickup_workflow(
            location=st.session_state.location or "Not specified",
            remarks=st.session_state.remarks,
            date=date_str, 
            pick_up_time=st.session_state.pickup_time,
            contact_number=st.session_state.contact_number,
            wait_minutes=wait_minutes
            
        )
        st.session_state.submission_success = result
        st.session_state.wait_minutes = wait_minutes
    except Exception as e:
        st.session_state.submission_error = str(e)
        st.session_state.submission_success = False

# Display progress bar
total_pages = 4
progress_value = st.session_state.page / total_pages
st.markdown('<div class="progress-container">', unsafe_allow_html=True)
st.progress(progress_value)
st.markdown(f'<p style="text-align:right; font-size:0.8em;">Step {st.session_state.page} of {total_pages}</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Get current hour for time options
current_hour = datetime.datetime.now().hour

# Display content based on current page
if st.session_state.page == 1:
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.title("Thank you for sharing leftover food! When do you have left overs?")
    st.markdown('</div>', unsafe_allow_html=True)
    
    #st.markdown('<div class="message-box">', unsafe_allow_html=True)
    st.markdown("""
    By providing your details, multiple Foodsavers will be informed and someone will reach out to you within 60 minutes!
    """)
    st.markdown('</div>', unsafe_allow_html=True)    
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Today", use_container_width=True):
            st.session_state.date = "Today"
            next_page()
    
    with col2:
        if st.button("Another Day", use_container_width=True):
            go_to_page(1.5)  # Go to date picker sub-page

    

elif st.session_state.page == 1.5:
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.title("Select Date")
    st.markdown('</div>', unsafe_allow_html=True)
    
    min_date = datetime.date.today() + datetime.timedelta(days=1)
    max_date = datetime.date.today() + datetime.timedelta(days=14)
    
    date = st.date_input("Select a date:", min_value=min_date, max_value=max_date)
    st.session_state.date = date.strftime("%A, %d %B")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.button("Back", on_click=lambda: go_to_page(1), use_container_width=True)

    with col2:
        # Fix: Make sure clicking "Continue" actually advances to the next page
        if st.button("Continue", on_click=lambda: go_to_page(2), use_container_width=True):
            pass
    
elif st.session_state.page == 2:
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.title("Pick-up Time")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("""
    This can be an estimation. You can confirm the details once an available Foodsaver is reaching out to you!
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Create time options based on current time if today is selected
    time_options = []
    if st.session_state.date == "Today":
        if current_hour < 14:
            time_options.append(("Before 14:00", "Before 14:00"))
        if current_hour < 16:
            time_options.append(("14:00 - 16:00", "14:00 - 16:00"))
        if current_hour < 18:
            time_options.append(("16:00 - 18:00", "16:00 - 18:00"))
        if current_hour < 20:
            time_options.append(("18:00 - 20:00", "18:00 - 20:00"))
        if current_hour < 22:
            time_options.append(("20:00 - 22:00", "20:00 - 22:00"))
        time_options.append(("After 22:00", "After 22:00"))
    else:
        # If not today, show all options
        time_options = [
            ("Before 14:00", "Before 14:00"),
            ("14:00 - 16:00", "14:00 - 16:00"),
            ("16:00 - 18:00", "16:00 - 18:00"),
            ("18:00 - 20:00", "18:00 - 20:00"),
            ("20:00 - 22:00", "20:00 - 22:00"),
            ("After 22:00", "After 22:00")
        ]
    
    # Display time options as buttons
    cols = st.columns(2)
    for i, (label, value) in enumerate(time_options):
        with cols[i % 2]:
            if st.button(label, key=f"time_{value}", use_container_width=True):
                st.session_state.pickup_time = value
                next_page()
    
    # Add back button at the bottom
    st.markdown('<div class="back-button">', unsafe_allow_html=True)
    st.button("Back", on_click=lambda: go_to_page(1))
    st.markdown('</div>', unsafe_allow_html=True)
            
elif st.session_state.page == 3:
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.title("Location (Optional)")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Debug existing value
    st.write(f"Current location value: {st.session_state.location}")
    
    location_input = st.text_input("Where is the food located?", value=st.session_state.location, 
                 placeholder="e.g., Otaniemi Campus, A-Block")
    
    # Force-update the session state
    st.session_state.location = location_input

    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.title("Additional Information (Optional)")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Debug existing value
    st.write(f"Current remarks value: {st.session_state.remarks}")
    
    remarks_input = st.text_input("Do you want to provide any additional information?", value=st.session_state.remarks, 
                 placeholder="e.g., amount or kind of food")
    
    # Force-update the session state
    st.session_state.remarks = remarks_input
    
    # Fix: Place buttons on the same line with proper spacing
    col1, col2 = st.columns(2)
    
    with col1:
        st.button("Back", on_click=lambda: go_to_page(2), use_container_width=True)
            
    with col2:
        st.button("Continue", on_click=lambda: go_to_page(4), use_container_width=True)
    
elif st.session_state.page == 4:
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.title("Contact Information")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("""
    **How your number is processed:**
    
    We will notify potential Foodsavers. Only one person receives your phone number after confirming the pick-up. By submitting your phone number, you consent to the processing by Telegram Messenger Inc. and Streamlit (Snowflake Inc.). Your number will be shared with a Foodsaver and automatically deleted after 15 minutes.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Initialize the thank you state if it doesn't exist
    if 'showing_thank_you' not in st.session_state:
        st.session_state.showing_thank_you = False
    
    st.text_input("Phone Number", key="contact_number", 
                 placeholder="e.g., +358 40 1234567")
    
    # Fix: Place buttons on the same line consistently
    col1, col2 = st.columns(2)
    
    if not st.session_state.submitted and not st.session_state.showing_thank_you:
        with col1:
            st.button("Back", on_click=previous_page, use_container_width=True)
        
        with col2:
            if st.session_state.contact_number.strip():  # Only enable if contact number provided
                if st.button("Submit", key="submit_button", use_container_width=True):
                    st.session_state.showing_thank_you = True
                    # This will trigger a rerun of the app
            else:
                st.button("Submit", disabled=True, use_container_width=True)
    
        st.markdown("""
        **We are not reaching out to you within 60 minutes?:**
        
        You can also share the left-over food in a Telegram Group and interest people come with their containers. [CLICK HERE to go to TELEGRAM](https://t.me/+2NxhCayA8bg4ODlk) 
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Show thank you message and then process submission
    elif st.session_state.showing_thank_you and not st.session_state.submitted:
        st.success("Thank you! Submission completed.")
        # Use a placeholder for the processing message
        processing_placeholder = st.empty()
        processing_placeholder.info("We are reaching out to potential Foodsaver. If someone is available, they will contact you.")
        
        # Add a small delay to show the thank you message
        time.sleep(2)
        
        # Process the submission
        process_submission()
        
        # Clear the processing message
        processing_placeholder.empty()

    if st.session_state.submitted:
        if hasattr(st.session_state, 'submission_error'):
            st.error(f"There was an error: {st.session_state.submission_error}")
            if st.button("Try Again"):
                st.session_state.submitted = False
                st.session_state.showing_thank_you = False
                del st.session_state.submission_error
        elif st.session_state.submission_success:
            st.success("Thank you! Someone is found. A Foodsaver will contact you soon.")
            
            st.markdown("""
            **Summary:**
            - **Date:** {}
            - **Time:** {}
            - **Location:** {}
            """.format(st.session_state.date, st.session_state.pickup_time, 
                      st.session_state.location if st.session_state.location else "Not specified"))
            
        else:
            st.warning(f"No Foodsavers were available within {st.session_state.wait_minutes} minutes. Please try again later. You can also share the left-over food in a Telegram Group and interest people come with their containers. [CLICK HERE to go to TELEGRAM](https://t.me/+2NxhCayA8bg4ODlk)")
            if st.button("Try Again"):
                st.session_state.submitted = False
                st.session_state.showing_thank_you = False

