# pip install phidata google-generativeai tavily-python
# pip install streamlit

import streamlit as st
import os
from PIL import Image
from io import BytesIO
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
from tempfile import NamedTemporaryFile
from constants import SYSTEM_PROMPT, INSTRUCTIONS

# API Keys (Ensure these are stored securely in production)
os.environ['TAVILY_API_KEY'] = st.secrets['TAVILY_API_KEY']
os.environ['GOOGLE_API_KEY'] = st.secrets['GOOGLE_API_KEY']

MAX_IMAGE_WIDTH = 300

def resize_image_for_display(image_file):
    """Resize image for display only, returns bytes"""
    if isinstance(image_file, str):
        img = Image.open(image_file)
    else:
        img = Image.open(image_file)
        image_file.seek(0)
    
    aspect_ratio = img.height / img.width
    new_height = int(MAX_IMAGE_WIDTH * aspect_ratio)
    img = img.resize((MAX_IMAGE_WIDTH, new_height), Image.Resampling.LANCZOS)
    
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

@st.cache_resource
def get_agent():
    """Initialize the AI agent with updated prompts for medicine and supplement analysis"""
    return Agent(
        model=Gemini(id="gemini-2.0-flash-exp"),
        system_prompt=SYSTEM_PROMPT,  # Defined in constants.py
        instructions=INSTRUCTIONS,  # Defined in constants.py
        tools=[TavilyTools(api_key=os.getenv("TAVILY_API_KEY"))],
        markdown=True,
    )

def analyze_image(image_path):
    """Runs AI analysis on the provided medicine/supplement image"""
    agent = get_agent()
    with st.spinner('Analyzing ingredients...'):
        response = agent.run(
            "Analyze the given image for medicine or supplement ingredients.",
            images=[image_path],
        )
        st.markdown(response.content)

def save_uploaded_file(uploaded_file):
    """Save the uploaded image temporarily for processing"""
    with NamedTemporaryFile(dir='.', suffix='.jpg', delete=False) as f:
        f.write(uploaded_file.getbuffer())
        return f.name

def main():
    """Streamlit UI"""
    st.title("💊 Medicine Analyzer")
    st.markdown("Upload an image of a **medicine or supplement label** to analyze its ingredients, safety, and effectiveness.")

    if 'selected_example' not in st.session_state:
        st.session_state.selected_example = None
    if 'analyze_clicked' not in st.session_state:
        st.session_state.analyze_clicked = False
    
    tab_upload, tab_camera = st.tabs([
        "📤 Upload Image", 
        "📸 Take Photo"
    ])
    
    with tab_upload:
        uploaded_file = st.file_uploader(
            "Upload an image of a medicine or supplement ingredient label",
            type=["jpg", "jpeg", "png"],
            help="Ensure the ingredient list is **clear and readable**."
        )
        if uploaded_file:
            resized_image = resize_image_for_display(uploaded_file)
            st.image(resized_image, caption="Uploaded Image", use_container_width=False, width=MAX_IMAGE_WIDTH)
            if st.button("🔬 Analyze Ingredients", key="analyze_upload"):
                temp_path = save_uploaded_file(uploaded_file)
                analyze_image(temp_path)
                os.unlink(temp_path) 
    
    with tab_camera:
        camera_photo = st.camera_input("Take a picture of the ingredient label")
        if camera_photo:
            resized_image = resize_image_for_display(camera_photo)
            st.image(resized_image, caption="Captured Photo", use_container_width=False, width=MAX_IMAGE_WIDTH)
            if st.button("🔬 Analyze Captured Image", key="analyze_camera"):
                temp_path = save_uploaded_file(camera_photo)
                analyze_image(temp_path)
                os.unlink(temp_path) 
    
    if st.session_state.selected_example:
        st.divider()
        st.subheader("Selected Product Example")
        resized_image = resize_image_for_display(st.session_state.selected_example)
        st.image(resized_image, caption="Selected Example", use_container_width=False, width=MAX_IMAGE_WIDTH)
        
        if st.button("🔬 Analyze Example", key="analyze_example") and not st.session_state.analyze_clicked:
            st.session_state.analyze_clicked = True
            analyze_image(st.session_state.selected_example)

if __name__ == "__main__":
    st.set_page_config(
        page_title="Medicine Analyzer",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    main()
