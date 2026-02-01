import streamlit as st
import cv2
import numpy as np
from PIL import Image
from face_system import FaceSystem
from database import AttendanceTracker
import time
from datetime import datetime, timedelta

# page config
st.set_page_config(
    page_title="Face Attendance System",
    layout="wide"
)

# initialize systems
@st.cache_resource
def init_systems():
    face_sys = FaceSystem()
    attendance = AttendanceTracker()
    return face_sys, attendance

face_system, attendance_tracker = init_systems()

# custom CSS
st.markdown("""
<style>
    .success-msg {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-msg {
        padding: 1rem;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    .info-msg {
        padding: 1rem;
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
    .stat-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        border-left: 3px solid #007bff;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# header
st.title("Face Attendance System")

# sidebar
with st.sidebar:
    st.header("Menu")
    page = st.radio("Select Action", 
                    ["Mark Attendance", "Register New User", "View Records", "Statistics", "Settings"])
    
    st.markdown("---")
    
    # show registered users
    users = face_system.get_all_users()
    st.subheader(f"Registered Users ({len(users)})")
    if users:
        for user in users:
            st.text(f"- {user}")
    else:
        st.text("No users registered")

# MARK ATTENDANCE PAGE
if page == "Mark Attendance":
    st.header("Mark Attendance")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Camera")
        
        # camera input
        camera_image = st.camera_input("Capture your photo")
        
        if camera_image:
            # convert to opencv format
            image = Image.open(camera_image)
            frame = np.array(image)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # detect face and draw rectangle
            face, rect = face_system.detect_face(frame)
            
            if rect:
                x, y, w, h = rect
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # show image with detection
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            st.image(frame_rgb, caption="Face Detection", use_container_width=True)
            
            # anti-spoofing check
            is_real, variance = face_system.anti_spoof_check(frame)
            
            if not is_real:
                st.markdown(f'<div class="error-msg">Warning: Liveness check failed (score: {variance:.1f}). Please use a live camera feed, not a photo.</div>', unsafe_allow_html=True)
            else:
                # recognize
                name, confidence = face_system.recognize(frame)
                
                if name and name != "Unknown":
                    st.success(f"Recognized: **{name}** (match score: {100-confidence:.1f}%)")
                    
                    # punch buttons
                    col_in, col_out, col_break = st.columns(3)
                    
                    with col_in:
                        if st.button("Punch IN", use_container_width=True, type="primary"):
                            success, msg = attendance_tracker.punch(name, 'in')
                            if success:
                                st.markdown(f'<div class="success-msg">{msg}</div>', unsafe_allow_html=True)
                                st.balloons()
                            else:
                                st.markdown(f'<div class="error-msg">{msg}</div>', unsafe_allow_html=True)
                    
                    with col_out:
                        if st.button("Punch OUT", use_container_width=True):
                            success, msg = attendance_tracker.punch(name, 'out')
                            if success:
                                st.markdown(f'<div class="success-msg">{msg}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="error-msg">{msg}</div>', unsafe_allow_html=True)
                    
                    with col_break:
                        if st.button("Break", use_container_width=True):
                            success, msg = attendance_tracker.punch(name, 'break')
                            if success:
                                st.markdown(f'<div class="success-msg">{msg}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="error-msg">{msg}</div>', unsafe_allow_html=True)
                    
                    # show current status
                    status = attendance_tracker.get_today_status(name)
                    st.info(f"Today's Status: **{status}**")
                    
                else:
                    st.error("Face not recognized. Please register first.")
    
    with col2:
        st.subheader("Instructions")
        st.markdown("""
        **How to use:**
        
        1. Click the camera button
        2. Allow camera access
        3. Position your face in the frame
        4. Capture photo
        5. Click Punch IN/OUT/Break
        
        **Tips:**
        - Make sure lighting is good
        - Face the camera directly
        - Remove sunglasses if wearing
        - Don't use a printed photo
        - Keep face centered
        """)
        
        st.markdown("---")
        
        # Today's summary
        st.subheader("Today's Summary")
        summary = attendance_tracker.get_attendance_summary()
        
        total_in = 0
        total_out = 0
        
        for user_name, records in summary.items():
            for rec in records:
                if rec['type'] == 'in':
                    total_in += 1
                elif rec['type'] == 'out':
                    total_out += 1
        
        st.metric("Total Check-ins", total_in)
        st.metric("Total Check-outs", total_out)

# REGISTER USER PAGE
elif page == "Register New User":
    st.header("Register New User")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        name = st.text_input("Full Name", placeholder="Enter your name")
        email = st.text_input("Email (optional)", placeholder="user@example.com")
        department = st.text_input("Department (optional)", placeholder="Engineering")
        
        if name:
            st.info(f"Registering: **{name}**")
            
            st.markdown("### Capture Face Samples")
            st.write("Take multiple photos for better accuracy. Slightly move your head between captures.")
            
            num_samples = st.slider("Number of samples to capture", 5, 20, 10)
            
            # Initialize session state
            if 'captured_frames' not in st.session_state:
                st.session_state.captured_frames = []
            if 'current_capture' not in st.session_state:
                st.session_state.current_capture = None
            if 'registration_name' not in st.session_state:
                st.session_state.registration_name = name
            
            # Reset if name changed
            if st.session_state.registration_name != name:
                st.session_state.captured_frames = []
                st.session_state.current_capture = None
                st.session_state.registration_name = name
            
            # Show progress
            captured_count = len(st.session_state.captured_frames)
            progress = min(captured_count / num_samples, 1.0)
            
            st.markdown(f"**Progress: {captured_count}/{num_samples} samples**")
            st.progress(progress)
            
            # Show captured samples
            if captured_count > 0:
                st.write(f"Captured {captured_count} sample(s)")
                
                # Show thumbnails in a row
                cols = st.columns(min(captured_count, 5))
                for idx in range(min(captured_count, 5)):
                    with cols[idx]:
                        frame_rgb = cv2.cvtColor(st.session_state.captured_frames[-(idx+1)], cv2.COLOR_BGR2RGB)
                        st.image(frame_rgb, caption=f"Sample {captured_count - idx}", width=100)
                
                if captured_count > 5:
                    st.caption(f"... and {captured_count - 5} more")
            
            st.markdown("---")
            
            # Check if we have enough samples
            if captured_count >= num_samples:
                st.success(f"All {captured_count} samples captured!")
                
                col_register, col_more = st.columns(2)
                
                with col_register:
                    if st.button("Complete Registration", type="primary", use_container_width=True):
                        with st.spinner("Processing and training model..."):
                            # Register in face system
                            success, msg = face_system.register_user(name, st.session_state.captured_frames)
                            
                            if success:
                                # Add to local database
                                attendance_tracker.add_user(name)
                                
                                # Try to add to Firebase
                                try:
                                    from firebase_manager import FirebaseManager
                                    firebase = FirebaseManager()
                                    if firebase.is_initialized():
                                        firebase.add_user(name, email, department)
                                        firebase_msg = " | Synced to Firebase"
                                    else:
                                        firebase_msg = " | Firebase not configured"
                                except Exception as e:
                                    firebase_msg = f" | Firebase error: {str(e)}"
                                
                                st.markdown(f'<div class="success-msg">{msg}{firebase_msg}</div>', unsafe_allow_html=True)
                                st.balloons()
                                
                                # Clear session state
                                st.session_state.captured_frames = []
                                st.session_state.current_capture = None
                                st.session_state.registration_name = None
                                
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(f"Registration failed: {msg}")
                
                with col_more:
                    if st.button("Capture More", use_container_width=True):
                        st.session_state.current_capture = None
                        st.rerun()
            
            else:
                # Camera input for new capture
                st.subheader(f"Sample {captured_count + 1} of {num_samples}")
                
                camera_image = st.camera_input("Take photo", key=f"camera_{captured_count}")
                
                if camera_image is not None:
                    # Convert to opencv
                    image = Image.open(camera_image)
                    frame = np.array(image)
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    
                    # Check if face detected
                    face, rect = face_system.detect_face(frame)
                    
                    if face is not None:
                        # Show preview with detection box
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        x, y, w, h = rect
                        cv2.rectangle(frame_rgb, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        st.image(frame_rgb, caption="Face detected!", use_container_width=True)
                        
                        # Next button
                        col_next, col_retake = st.columns(2)
                        
                        with col_next:
                            if st.button("Save & Next", type="primary", use_container_width=True):
                                # Save this frame
                                st.session_state.captured_frames.append(frame)
                                st.session_state.current_capture = None
                                st.rerun()
                        
                        with col_retake:
                            if st.button("Retake", use_container_width=True):
                                st.rerun()
                    else:
                        st.error("No face detected. Please ensure your face is clearly visible.")
                        if st.button("Try Again", use_container_width=True):
                            st.rerun()
            
            # Reset button (always available)
            st.markdown("---")
            if st.button("Reset and Start Over", use_container_width=True):
                st.session_state.captured_frames = []
                st.session_state.current_capture = None
                st.rerun()
    
    with col2:
        st.subheader("Registration Guide")
        st.markdown("""
        **Best practices:**
        
        - Use consistent lighting
        - Look directly at camera
        - Keep neutral expression
        - Slightly turn head between shots
        - Remove sunglasses/hats
        - Keep consistent distance
        
        **Why multiple samples?**
        
        Taking several photos from slightly different angles improves recognition accuracy and makes the system more robust.
        
        Recommended: 10-15 samples
        
        **Firebase Integration:**
        
        User data will be synced to Firebase cloud storage for backup and access from multiple devices.
        """)

# VIEW RECORDS PAGE
elif page == "View Records":
    st.header("Attendance Records")
    
    users = attendance_tracker.get_all_users()
    
    if not users:
        st.info("No registered users yet. Please register users first.")
    else:
        selected_user = st.selectbox("Select User", ["All Users"] + users)
        
        # Date filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From Date", datetime.now() - timedelta(days=7))
        with col2:
            end_date = st.date_input("To Date", datetime.now())
        
        if selected_user == "All Users":
            st.subheader("Today's Status - All Users")
            
            summary = attendance_tracker.get_attendance_summary()
            
            for user in users:
                with st.expander(f"{user}"):
                    status = attendance_tracker.get_today_status(user)
                    st.write(f"**Current Status:** {status}")
                    
                    if user in summary and summary[user]:
                        st.write("**Today's Records:**")
                        for record in summary[user]:
                            st.write(f"  - {record['type'].upper()}: {record['time']}")
                    else:
                        st.write("No records today")
        
        else:
            st.subheader(f"Records: {selected_user}")
            
            # today's status
            status = attendance_tracker.get_today_status(selected_user)
            st.info(f"**Today:** {status}")
            
            # history
            days_diff = (end_date - start_date).days + 1
            history = attendance_tracker.get_user_history(selected_user, days=days_diff)
            
            if history:
                st.write(f"### Last {days_diff} Days")
                
                for date, records in sorted(history.items(), reverse=True):
                    with st.expander(f"{date}"):
                        for record in records:
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.write(f"{record['type'].upper()}")
                            with col2:
                                st.write(record['time'])
            else:
                st.warning("No attendance records found for selected period")

# STATISTICS PAGE
elif page == "Statistics":
    st.header("Statistics Dashboard")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("To", datetime.now())
    
    stats = attendance_tracker.get_statistics(
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    
    # Summary cards
    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.metric("Total Users", len(attendance_tracker.get_all_users()))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        total_punches = sum(stats['by_type'].values())
        st.metric("Total Punches", total_punches)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        check_ins = stats['by_type'].get('in', 0)
        st.metric("Check-ins", check_ins)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        check_outs = stats['by_type'].get('out', 0)
        st.metric("Check-outs", check_outs)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Charts
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Punches by Type")
        if stats['by_type']:
            st.bar_chart(stats['by_type'])
        else:
            st.info("No data available")
    
    with col2:
        st.subheader("Punches by User")
        if stats['by_user']:
            st.bar_chart(stats['by_user'])
        else:
            st.info("No data available")
    
    # Daily attendance
    st.markdown("---")
    st.subheader("Daily Attendance")
    if stats['daily']:
        st.line_chart(stats['daily'])
    else:
        st.info("No data available")
    
    # Detailed table
    st.markdown("---")
    st.subheader("Detailed Breakdown")
    
    if stats['by_user']:
        import pandas as pd
        
        df = pd.DataFrame([
            {'User': user, 'Total Punches': count}
            for user, count in stats['by_user'].items()
        ])
        
        st.dataframe(df, use_container_width=True)

# SETTINGS PAGE
elif page == "Settings":
    st.header("Settings")
    
    st.subheader("Firebase Configuration")
    
    # Check Firebase status
    try:
        from firebase_manager import FirebaseManager
        firebase = FirebaseManager()
        if firebase.is_initialized():
            st.success("Firebase is connected and ready")
            
            if st.button("Sync All Users to Firebase"):
                with st.spinner("Syncing to Firebase..."):
                    success, msg = firebase.sync_local_to_firebase(attendance_tracker)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
        else:
            st.warning("Firebase not configured")
            st.info("To enable Firebase, place your 'firebase-credentials.json' file in the project directory")
    except Exception as e:
        st.warning(f"Firebase module not available: {str(e)}")
        st.info("Install firebase-admin: pip install firebase-admin")
    
    st.markdown("---")
    
    st.subheader("User Management")
    
    users = attendance_tracker.get_all_users()
    
    if users:
        user_to_delete = st.selectbox("Select user to delete", users)
        
        st.warning(f"This will delete **{user_to_delete}** and all their attendance records permanently!")
        
        confirm = st.checkbox("I understand this action cannot be undone")
        
        if confirm:
            if st.button("Delete User", type="primary"):
                # Delete from database
                success, msg = attendance_tracker.delete_user(user_to_delete)
                
                # Try to delete from Firebase
                try:
                    from firebase_manager import FirebaseManager
                    firebase = FirebaseManager()
                    if firebase.is_initialized():
                        firebase.delete_user(user_to_delete)
                except:
                    pass
                
                if success:
                    st.success(msg)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.info("No users to delete")
    
    st.markdown("---")
    
    st.subheader("System Settings")
    
    st.write("**Recognition Threshold**")
    st.slider("Confidence threshold (lower = stricter)", 0, 100, 70, disabled=True)
    st.caption("Currently set in face_system.py")
    
    st.write("**Anti-spoofing**")
    st.slider("Liveness threshold", 50, 200, 100, disabled=True)
    st.caption("Currently set in face_system.py")

# footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; padding: 1rem; font-size: 0.9rem;'>
    Face Attendance System | OpenCV + Streamlit + SQLite + Firebase
</div>
""", unsafe_allow_html=True)
