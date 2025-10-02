import streamlit as st
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas

st.title("Canvas Test - NumPy Background")

file = st.file_uploader("Upload image", type=["jpg","jpeg","png"])
if file:
    img = Image.open(file).convert("RGB")
    img = img.resize((800, 600))

    # ✅ Force NumPy array uint8 copy
    img_np = np.array(img).astype("uint8").copy()

    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=3,
        stroke_color="#FF0000",
        background_image=img_np,   # ✅ NumPy uint8 array
        update_streamlit=True,
        height=img_np.shape[0],
        width=img_np.shape[1],
        drawing_mode="point",
        point_display_radius=6,
        key="canvas",
    )

    st.write(canvas_result.json_data)
