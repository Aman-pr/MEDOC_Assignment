import streamlit as st
import cv2
import numpy as np
from PIL import Image
from face_system import FaceSystem
from attendance import AttendanceTracker
import time

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
</style>
""", unsafe_allow_html=True)

# header
st.title("Face Attendance System")

# sidebar
with st.sidebar:
    st.header("Menu")
    page = st.radio("Select Action", 
                    ["Mark Attendance", "Register New User", "View Records"])
    
    st.markdown("---")
    
    # show registered users
    users = face_system.get_all_users()
    st.subheader("Registered Users")
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
                    st.success(f"Recognized: {name} (match score: {100-confidence:.1f}%)")
                    
                    # punch buttons
                    col_in, col_out = st.columns(2)
                    
                    with col_in:
                        if st.button("Punch IN", use_container_width=True, type="primary"):
                            success, msg = attendance_tracker.punch(name, 'in')
                            if success:
                                st.markdown(f'<div class="success-msg">{msg}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="error-msg">{msg}</div>', unsafe_allow_html=True)
                    
                    with col_out:
                        if st.button("Punch OUT", use_container_width=True):
                            success, msg = attendance_tracker.punch(name, 'out')
                            if success:
                                st.markdown(f'<div class="success-msg">{msg}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="error-msg">{msg}</div>', unsafe_allow_html=True)
                    
                    # show current status
                    status = attendance_tracker.get_today_status(name)
                    st.info(f"Today: {status}")
                    
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
        5. Click Punch IN or OUT
        
        **Tips:**
        - Make sure lighting is good
        - Face the camera directly
        - Remove sunglasses if wearing any
        - Don't use a printed photo
        """)

# REGISTER USER PAGE
elif page == "Register New User":
    st.header("Register New User")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        name = st.text_input("Full Name", placeholder="Enter your name")
        
        if name:
            st.info(f"Registering: {name}")
            
            st.markdown("### Capture Face Samples")
            st.write("Take multiple photos for better accuracy. Slightly move your head between captures.")
            
            num_samples = st.slider("Number of samples to capture", 5, 15, 10)
            
            # use session state to store captured frames
            if 'captured_frames' not in st.session_state:
                st.session_state.captured_frames = []
            
            camera_image = st.camera_input(f"Sample {len(st.session_state.captured_frames) + 1} of {num_samples}")
            
            if camera_image:
                # convert to opencv
                image = Image.open(camera_image)
                frame = np.array(image)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # check if face detected
                face, rect = face_system.detect_face(frame)
                
                if face is not None:
                    # add to captured frames
                    st.session_state.captured_frames.append(frame)
                    
                    # show preview
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    x, y, w, h = rect
                    cv2.rectangle(frame_rgb, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    st.image(frame_rgb, caption=f"Sample {len(st.session_state.captured_frames)} captured", width=300)
                    
                    if len(st.session_state.captured_frames) >= num_samples:
                        st.success(f"Captured all {len(st.session_state.captured_frames)} samples")
                        
                        if st.button("Complete Registration", type="primary"):
                            with st.spinner("Processing and training model..."):
                                success, msg = face_system.register_user(name, st.session_state.captured_frames)
                                
                                if success:
                                    st.markdown(f'<div class="success-msg">{msg}</div>', unsafe_allow_html=True)
                                    st.session_state.captured_frames = []
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"Registration failed: {msg}")
                    else:
                        remaining = num_samples - len(st.session_state.captured_frames)
                        st.warning(f"Continue capturing. {remaining} more sample(s) needed.")
                else:
                    st.error("No face detected. Please ensure your face is clearly visible and try again.")
            
            if len(st.session_state.captured_frames) > 0:
                if st.button("Reset and Start Over"):
                    st.session_state.captured_frames = []
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
        
        **Why multiple samples?**
        
        Taking several photos from slightly different angles improves recognition accuracy.
        
        Recommended: 10-15 samples
        """)

# VIEW RECORDS PAGE
elif page == "View Records":
    st.header("Attendance Records")
    
    users = face_system.get_all_users()
    
    if not users:
        st.info("No registered users yet. Please register users first.")
    else:
        selected_user = st.selectbox("Select User", ["All Users"] + users)
        
        if selected_user == "All Users":
            st.subheader("Today's Status - All Users")
            
            for user in users:
                with st.expander(f"{user}"):
                    status = attendance_tracker.get_today_status(user)
                    st.write(f"**Current Status:** {status}")
                    
                    history = attendance_tracker.get_user_history(user, days=7)
                    
                    if history:
                        st.write("**Last 7 Days:**")
                        for date, records in history.items():
                            st.write(f"{date}:")
                            for record in records:
                                st.write(f"  {record['type'].upper()}: {record['time']}")
                    else:
                        st.write("No attendance records")
        
        else:
            st.subheader(f"Records: {selected_user}")
            
            # today's status
            status = attendance_tracker.get_today_status(selected_user)
            st.info(f"**Today:** {status}")
            
            # history
            history = attendance_tracker.get_user_history(selected_user, days=30)
            
            if history:
                st.write("### Last 30 Days")
                
                for date, records in history.items():
                    with st.expander(f"{date}"):
                        for record in records:
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.write(f"{record['type'].upper()}")
                            with col2:
                                st.write(record['time'])
            else:
                st.warning("No attendance records found")

# footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; padding: 1rem; font-size: 0.9rem;'>
    Face Attendance System | OpenCV + Streamlit
</div>
""", unsafe_allow_html=True)