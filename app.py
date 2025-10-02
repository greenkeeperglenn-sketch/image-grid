from PIL import Image
import streamlit as st
from streamlit_drawable_canvas import st_canvas

st.title("Canvas Test")

file = st.file_uploader("Upload image", type=["jpg","jpeg","png"])
if file:
    # Keep as PIL, RGB
    img = Image.open(file).convert("RGB")
    img = img.resize((800, 600))  # shrink for demo

    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=3,
        stroke_color="#FF0000",
        background_image=img,   # ✅ PIL.Image works
        update_streamlit=True,
        height=img.height,
        width=img.width,
        drawing_mode="point",
        point_display_radius=6,
        key="canvas",
    )

    st.write(canvas_result.json_data)
