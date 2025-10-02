import streamlit as st
import numpy as np
from PIL import Image
import io
from streamlit_drawable_canvas import st_canvas

st.title("Canvas Test - Bytes Background")

file = st.file_uploader("Upload image", type=["jpg","jpeg","png"])
if file:
    img = Image.open(file).convert("RGB")
    img = img.resize((800, 600))

    # ✅ Convert to bytes (PNG)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()

    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=3,
        stroke_color="#FF0000",
        background_image=byte_im,   # ✅ bytes instead of NumPy/PIL
        update_streamlit=True,
        height=img.height,
        width=img.width,
        drawing_mode="point",
        point_display_radius=6,
        key="canvas",
    )

    st.write(canvas_result.json_data)
