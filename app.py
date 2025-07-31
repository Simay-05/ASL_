import streamlit as st
from PIL import Image
import os
import sys
import time
import cv2
import numpy as np
import torch
from hand_recognition_3 import HandTrackingDynamic

# Import feedback module with error handling
try:
    import feedback_new as feedback
    FEEDBACK_AVAILABLE = True
except Exception as e:
    st.error(f"Feedback module error: {e}")
    FEEDBACK_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="ASL Learning Assistant",
    page_icon="🤟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .letter-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 10px;
        margin: 20px 0;
    }
    .letter-btn {
        background: white;
        border: 2px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        font-size: 24px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .letter-btn:hover {
        border-color: #667eea;
        background: #f0f4ff;
        transform: scale(1.05);
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "start"
if "avatar" not in st.session_state:
    st.session_state.avatar = "🧑"
if "selected_letter" not in st.session_state:
    st.session_state.selected_letter = "A"
if "camera_working" not in st.session_state:
    st.session_state.camera_working = False
if "camera_cap" not in st.session_state:
    st.session_state.camera_cap = None
if "hand_detector" not in st.session_state:
    st.session_state.hand_detector = None

# Simple camera functions
def initialize_camera():
    """Initialize camera with proper error handling"""
    try:
        # Set environment variables for macOS
        os.environ['OPENCV_AVFOUNDATION_SKIP_AUTH'] = '1'
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return False, "Camera not accessible"
            
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Initialize hand detector with more sensitive parameters
        detector = HandTrackingDynamic(
            mode=False,
            maxHands=1,
            detectionCon=0.7,  # Higher detection confidence
            trackCon=0.7       # Higher tracking confidence
        )
        
        return True, "Camera initialized successfully", cap, detector
        
    except Exception as e:
        return False, f"Camera initialization failed: {str(e)}", None, None

def capture_frame():
    """Capture a single frame from camera with improved frame reading"""
    if st.session_state.camera_cap and st.session_state.camera_cap.isOpened():
        # Read multiple frames to get the most recent one
        for _ in range(3):
            ret, frame = st.session_state.camera_cap.read()
            if ret and frame is not None:
                # Ensure frame has valid dimensions
                if frame.shape[0] > 0 and frame.shape[1] > 0:
                    return frame
    return None

def process_frame_with_hands(frame):
    """Process frame with hand detection"""
    if st.session_state.hand_detector:
        frame = st.session_state.hand_detector.findFingers(frame, draw=False)
        lmsList, bbox = st.session_state.hand_detector.findPosition(frame, draw=True)
        return frame, lmsList, bbox
    return frame, [], None

def capture_hand_image():
    """Capture and crop hand image with improved detection"""
    frame = capture_frame()
    if frame is not None:
        # Save the full frame first
        temp_frame_path = "temp_full_frame.jpg"
        cv2.imwrite(temp_frame_path, frame)
        
        # Use improved hand detection
        try:
            from improved_hand_detection import improved_hand_crop
            success = improved_hand_crop(temp_frame_path, "correct_images/user_image.jpg")
            
            if success:
                # Load the improved crop
                improved_crop = cv2.imread("correct_images/user_image.jpg")
                if improved_crop is not None:
                    st.success("✅ Improved hand detection successful!")
                    return improved_crop
                else:
                    st.error("❌ Could not load improved hand crop")
                    return None
            else:
                st.error("❌ Improved hand detection failed")
                return None
                
        except ImportError:
            st.warning("⚠️ Improved hand detection not available, using fallback")
            return fallback_hand_crop(frame)
        except Exception as e:
            st.error(f"❌ Hand detection error: {e}")
            return fallback_hand_crop(frame)
    return None

def fallback_hand_crop(frame):
    """Fallback hand cropping method"""
    if st.session_state.hand_detector:
        # Process frame to get hand landmarks
        processed_frame = st.session_state.hand_detector.findFingers(frame, draw=False)
        lmsList, bbox = st.session_state.hand_detector.findPosition(processed_frame, draw=True)
        
        if lmsList and hasattr(st.session_state.hand_detector, '_crop_region'):
            y1, y2, x1, x2 = st.session_state.hand_detector._crop_region
            
            # Ensure crop region is valid
            if y1 < y2 and x1 < x2 and y1 >= 0 and x1 >= 0:
                hand_crop = frame[y1:y2, x1:x2]
                
                # Check if crop is too small (likely no hand)
                if hand_crop.shape[0] > 50 and hand_crop.shape[1] > 50:
                    return hand_crop
                else:
                    st.warning("⚠️ Hand crop too small - please position your hand better")
                    return None
            else:
                st.warning("⚠️ Invalid crop region - please show your hand clearly")
                return None
        else:
            st.warning("⚠️ No hand detected - please show your hand in the camera view")
            return None
    return None

def stop_camera():
    """Stop camera and cleanup"""
    if st.session_state.camera_cap:
        st.session_state.camera_cap.release()
        st.session_state.camera_cap = None
    st.session_state.hand_detector = None
    st.session_state.camera_working = False
    cv2.destroyAllWindows()

# Main app logic
def main():
    # Start page
    if st.session_state.page == "start":
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.image("American Sign Language Learning Assistant.png", use_container_width=True)
            st.title("🤟 ASL Learning Assistant")
            st.markdown("""
            **Welcome to your personal ASL tutor!** 
            
            Practice American Sign Language letters with real-time AI feedback. 
            Our system uses advanced computer vision to help you perfect your signs.
            """)
            
            # Avatar selection
            st.subheader("Choose your avatar:")
            avatar_options = ["🧑", "👩‍🦰", "🧔", "👩‍🎓", "🧑‍🎤", "🧑‍🚀", "👨‍💻", "👩‍🔬"]
            selected_avatar = st.selectbox("Select your avatar:", avatar_options, index=0, key="avatar_select")
            
            if st.button("🚀 Start Learning", key="start_learning"):
                st.session_state.avatar = selected_avatar
                st.session_state.page = "pick_letter"
                st.rerun()
    
    # Letter selection page
    elif st.session_state.page == "pick_letter":
        st.header(f"Hello {st.session_state.avatar}! Pick a letter to practice:")
        
        # Create letter grid
        letters = [chr(ord('A') + i) for i in range(26)]
        
        # Display letters in a grid
        cols = st.columns(7)
        for idx, letter in enumerate(letters):
            with cols[idx % 7]:
                if st.button(letter, key=f"letter_{letter}", help=f"Practice {letter}"):
                    st.session_state.selected_letter = letter
                    st.session_state.page = "practice"
                    st.rerun()
        
        # Back button
        if st.button("← Back to Start", key="back_to_start"):
            st.session_state.page = "start"
            st.rerun()
    
    # Practice page
    elif st.session_state.page == "practice":
        st.header(f"Practice Letter: {st.session_state.selected_letter}")
        
        # Show correct reference image
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📖 Correct Sign")
            try:
                ref_image = Image.open(f"correct_images/correct_image_{st.session_state.selected_letter}.png")
                st.image(ref_image, caption=f"Correct sign for letter {st.session_state.selected_letter}", use_container_width=True)
            except Exception as e:
                st.error(f"Could not load reference image: {e}")
        
        with col2:
            st.subheader("📸 Your Sign")
            
            # Input method selection
            input_method = st.radio(
                "Choose input method:",
                ["📷 Camera Capture", "📁 Upload Image"],
                key="input_method"
            )
            
            if input_method == "📷 Camera Capture":
                camera_section()
            else:
                upload_section()
        
        # Navigation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Letters", key="back_to_letters"):
                st.session_state.page = "pick_letter"
                st.rerun()
        with col2:
            if st.button("🏠 Back to Start", key="back_to_start_from_practice"):
                st.session_state.page = "start"
                st.rerun()

def camera_section():
    """Camera capture section with robust error handling"""
    
    # Camera status
    if not st.session_state.camera_working:
        if st.button("🔧 Initialize Camera", key="init_camera"):
            with st.spinner("Initializing camera..."):
                success, message, cap, detector = initialize_camera()
                if success:
                    st.session_state.camera_working = True
                    st.session_state.camera_cap = cap
                    st.session_state.hand_detector = detector
                    st.success("✅ Camera initialized!")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
                    st.info("💡 Try the image upload option instead!")
    
    # Camera interface
    if st.session_state.camera_working:
        # Camera preview section
        st.subheader("📹 Live Camera Feed")
        
        # Initialize camera refresh counter
        if 'camera_refresh_counter' not in st.session_state:
            st.session_state.camera_refresh_counter = 0
        
        # Create a container for the live camera feed
        camera_container = st.container()
        
        with camera_container:
            # Create a placeholder for the camera feed
            camera_placeholder = st.empty()
            
            # Capture and display current frame
            frame = capture_frame()
            if frame is not None:
                # Process frame with hand detection
                processed_frame, lmsList, bbox = process_frame_with_hands(frame)
                
                # Convert BGR to RGB for display
                frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                
                # Display the frame in the placeholder
                camera_placeholder.image(frame_rgb, caption="📹 Live Camera Feed - Position your hand", use_container_width=True)
                
                # Hand detection status
                if lmsList:
                    st.success("✅ Hand detected! Ready to capture.")
                else:
                    st.info("👋 Show your hand in the camera view")
            else:
                st.error("❌ Could not capture frame from camera")
        
        # Continuous camera updates without breaking other features
        st.session_state.camera_refresh_counter += 1
        
        # Smart continuous camera updates
        # Use a more intelligent refresh system
        if st.session_state.camera_refresh_counter % 15 == 0:  # Update every 15 iterations
            # Only refresh if no recent user interactions
            if 'last_interaction' not in st.session_state:
                st.session_state.last_interaction = time.time()
            
            # Check if enough time has passed since last interaction
            time_since_interaction = time.time() - st.session_state.last_interaction
            
            # Only auto-refresh if no recent user interaction and camera is idle
            if time_since_interaction > 3.0:  # 3 second buffer for better UX
                # Use a very gentle refresh to maintain camera feed
                time.sleep(0.3)  # Slightly longer delay
                st.rerun()
        
        # Capture button section
        st.markdown("---")
        st.markdown("### 📸 Capture Photo")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📸 Capture Sign", key="capture_sign", use_container_width=True):
                # Track user interaction
                st.session_state.last_interaction = time.time()
                
                with st.spinner("Capturing photo..."):
                    captured_image = capture_hand_image()
                    if captured_image is not None:
                        # Save and process image
                        cv2.imwrite("correct_images/user_image.jpg", captured_image)
                        st.success("✅ Photo captured successfully!")
                        
                        # Show captured image
                        st.image(cv2.cvtColor(captured_image, cv2.COLOR_BGR2RGB), 
                                caption="Captured Hand Image", use_container_width=True)
                        
                        # Process with AI
                        if FEEDBACK_AVAILABLE:
                            process_image_with_ai()
                        else:
                            st.error("AI feedback system unavailable")
                    else:
                        st.error("❌ No hand detected. Please position your hand in the camera view.")
        
        # Camera controls
        st.markdown("---")
        st.markdown("### 🎛️ Camera Controls")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh View", key="refresh_camera", use_container_width=True):
                st.session_state.last_interaction = time.time()
                st.rerun()
        with col2:
            if st.button("📸 Capture Full Frame", key="capture_full", use_container_width=True):
                st.session_state.last_interaction = time.time()
                frame = capture_frame()
                if frame is not None:
                    cv2.imwrite("correct_images/user_image.jpg", frame)
                    st.success("✅ Full frame captured!")
                    st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), 
                            caption="Full Frame Capture", use_container_width=True)
                    if FEEDBACK_AVAILABLE:
                        process_image_with_ai()
        with col3:
            if st.button("⏹️ Stop Camera", key="stop_camera", use_container_width=True):
                st.session_state.last_interaction = time.time()
                stop_camera()
                st.rerun()
        
        # Alternative capture options
        st.markdown("---")
        st.markdown("### 🔧 Alternative Capture Options")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📸 Capture Center Region", key="capture_center", use_container_width=True):
                st.session_state.last_interaction = time.time()
                frame = capture_frame()
                if frame is not None:
                    # Capture center region of the frame
                    h, w = frame.shape[:2]
                    center_size = min(h, w) // 2
                    y1 = (h - center_size) // 2
                    y2 = y1 + center_size
                    x1 = (w - center_size) // 2
                    x2 = x1 + center_size
                    
                    center_crop = frame[y1:y2, x1:x2]
                    cv2.imwrite("correct_images/user_image.jpg", center_crop)
                    st.success("✅ Center region captured!")
                    st.image(cv2.cvtColor(center_crop, cv2.COLOR_BGR2RGB), 
                            caption="Center Region Capture", use_container_width=True)
                    if FEEDBACK_AVAILABLE:
                        process_image_with_ai()
        
        with col2:
            st.info("💡 **Tip**: The main 'Capture Sign' button uses hand detection for best results. These alternative options can be used when hand detection fails.")

def upload_section():
    """Image upload section"""
    uploaded_file = st.file_uploader(
        "Upload a photo of your hand sign:",
        type=["jpg", "jpeg", "png"],
        key="upload_sign"
    )
    
    if uploaded_file is not None:
        try:
            # Save uploaded image
            img = Image.open(uploaded_file)
            img.save("correct_images/user_image.jpg")
            
            # Display uploaded image
            st.image(img, caption="Your uploaded sign", use_container_width=True)
            
            # Process with AI
            if FEEDBACK_AVAILABLE:
                process_image_with_ai()
            else:
                st.error("AI feedback system unavailable")
                
        except Exception as e:
            st.error(f"Error processing uploaded image: {e}")

def process_image_with_ai():
    """Process captured/uploaded image with AI feedback using improved model"""
    try:
        with st.spinner("🤖 Analyzing your sign with improved AI..."):
            result = feedback.predict_and_feedback(
                "correct_images/user_image.jpg",
                st.session_state.selected_letter
            )
        
        # Display results
        st.markdown("### 📊 Analysis Results")
        
        st.markdown(f"**🤖 Predicted Letter:** {result['predicted_class']}")
        
        # Show images side by side
        col1, col2 = st.columns(2)
        with col1:
            st.image("correct_images/user_image.jpg", caption="Your Sign", use_container_width=True)
        with col2:
            st.image(f"correct_images/correct_image_{st.session_state.selected_letter}.png", 
                    caption="Correct Reference", use_container_width=True)
        
        # AI Feedback
        st.markdown("### 💡 AI Feedback")
        st.markdown(result['feedback'])
        
        # Success/Error indication
        if result['predicted_class'] == st.session_state.selected_letter:
            st.success("🎉 Excellent! Your sign matches the target letter!")
        elif result['predicted_class'] == 'Blank':
            st.warning("🔍 No clear hand sign detected. Please try again with better positioning.")
        else:
            st.warning(f"📝 Close! You signed '{result['predicted_class']}' instead of '{st.session_state.selected_letter}'")
            
        # Debug information
        if result['predicted_class'] == 'Blank':
            st.error("🔍 **Debug Info**: The AI detected 'Blank' which usually means:")
            st.markdown("""
            - **No hand visible** in the captured image
            - **Hand too small** or **too far** from camera
            - **Poor lighting** making hand hard to see
            - **Hand partially cut off** by crop region
            
            **💡 Tips to fix:**
            - Move your hand **closer** to the camera (20-30cm away)
            - Ensure **good lighting** on your hand (avoid shadows)
            - Make sure your **entire hand** is visible in the camera view
            - Try **different angles** if hand isn't detected
            - Use **plain background** for better contrast
            - Hold your hand **steady** for 2-3 seconds
            """)
            
            # Show manual capture options
            st.markdown("### 🔧 **Try Manual Capture Options:**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📸 Try Full Frame", key="try_full_frame"):
                    frame = capture_frame()
                    if frame is not None:
                        cv2.imwrite("correct_images/user_image.jpg", frame)
                        st.success("✅ Full frame captured!")
                        st.rerun()
            with col2:
                if st.button("📸 Try Center Crop", key="try_center_crop"):
                    frame = capture_frame()
                    if frame is not None:
                        h, w = frame.shape[:2]
                        size = min(h, w)
                        y1 = (h - size) // 2
                        y2 = y1 + size
                        x1 = (w - size) // 2
                        x2 = x1 + size
                        center_crop = frame[y1:y2, x1:x2]
                        cv2.imwrite("correct_images/user_image.jpg", center_crop)
                        st.success("✅ Center crop captured!")
                        st.rerun()
            
    except Exception as e:
        st.error(f"Error processing image: {e}")
        st.info("💡 **Tip**: The camera preview and hand detection are working perfectly! The AI feedback system requires Ollama to be running for detailed feedback, but you can still practice and compare your signs visually.")
        
        # Show basic results even if AI feedback fails
        try:
            # Try to get basic prediction using the improved model
            predicted_letter, confidence = feedback.predict_from_cv2_image(cv2.imread("correct_images/user_image.jpg"))
            
            st.markdown("### 📊 Basic Analysis Results")
            st.markdown(f"**🤖 Predicted Letter:** {predicted_letter}")
            
            # Show images side by side
            col1, col2 = st.columns(2)
            with col1:
                st.image("correct_images/user_image.jpg", caption="Your Sign", use_container_width=True)
            with col2:
                st.image(f"correct_images/correct_image_{st.session_state.selected_letter}.png", 
                        caption="Correct Reference", use_container_width=True)
            
            # Basic feedback
            if predicted_letter == st.session_state.selected_letter:
                st.success("🎉 Excellent! Your sign matches the target letter!")
            else:
                st.warning(f"📝 Close! You signed '{predicted_letter}' instead of '{st.session_state.selected_letter}'")
                
            # Debug information for Blank detection
            if predicted_letter == 'Blank':
                st.error("🔍 **Debug Info**: The AI detected 'Blank' which usually means:")
                st.markdown("""
                - **No hand visible** in the captured image
                - **Hand too small** or **too far** from camera
                - **Poor lighting** making hand hard to see
                - **Hand partially cut off** by crop region
                
                **💡 Tips to fix:**
                - Move your hand **closer** to the camera (20-30cm away)
                - Ensure **good lighting** on your hand (avoid shadows)
                - Make sure your **entire hand** is visible in the camera view
                - Try **different angles** if hand isn't detected
                - Use **plain background** for better contrast
                - Hold your hand **steady** for 2-3 seconds
                """)
                
                # Show manual capture options
                st.markdown("### 🔧 **Try Manual Capture Options:**")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📸 Try Full Frame (Fallback)", key="try_full_frame_fallback"):
                        frame = capture_frame()
                        if frame is not None:
                            cv2.imwrite("correct_images/user_image.jpg", frame)
                            st.success("✅ Full frame captured!")
                            st.rerun()
                with col2:
                    if st.button("📸 Try Center Crop (Fallback)", key="try_center_crop_fallback"):
                        frame = capture_frame()
                        if frame is not None:
                            h, w = frame.shape[:2]
                            size = min(h, w)
                            y1 = (h - size) // 2
                            y2 = y1 + size
                            x1 = (w - size) // 2
                            x2 = x1 + size
                            center_crop = frame[y1:y2, x1:x2]
                            cv2.imwrite("correct_images/user_image.jpg", center_crop)
                            st.success("✅ Center crop captured!")
                            st.rerun()
                
        except Exception as basic_error:
            st.error(f"Could not process image: {basic_error}")

# Run the app
if __name__ == "__main__":
    main() 