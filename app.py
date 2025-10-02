import streamlit as st
import cv2
import numpy as np
import pandas as pd
import os
from datetime import datetime
from PIL import Image
from streamlit_drawable_canvas import st_canvas

st.set_page_config(layout="wide")
st.title("📸 Trial Plot Overlay Tool (Prototype with Resize, Fixed)")

# --- Inputs ---
trial_id = st.text_input("Trial ID", "TrialA")
date_str = st.date_input("Date of Image", datetime.today())

image_file = st.file_uploader("Upload drone image (JPEG/PNG)", type=["jpg","jpeg","png"])
excel_file = st.file_uploader("Upload treatment layout (Excel)", type=["xls","xlsx"])

# Reset button
if st.button("Reset points"):
    st.session_state["points"] = []

if image_file and excel_file:
    # --- Load full image ---
    image_full = Image.open(image_file).convert("RGB")
    image_np_full = np.array(image_full, dtype=np.uint8)   # ✅ NumPy (H,W,3)

    # --- Resize for canvas ---
    max_width = 1200
    scale = min(1.0, max_width / image_full.width)
    if scale < 1.0:
        image_canvas = image_full.resize(
            (int(image_full.width * scale), int(image_full.height * scale))
        )
    else:
        image_canvas = image_full

    image_np_canvas = np.array(image_canvas, dtype=np.uint8)  # ✅ NumPy RGB

    # --- Load Excel ---
    df = pd.read_excel(excel_file, header=None)
    n_rows, n_cols = df.shape
    st.write(f"📑 Detected treatment grid: **{n_rows} rows × {n_cols} cols**")

    # --- Canvas for corner selection ---
    st.markdown("### Step 1: Click 4 outer corners of the grid (TL, TR, BR, BL)")

    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=3,
        stroke_color="#FF0000",
        background_image=image_np_canvas,  # ✅ must be NumPy RGB
        update_streamlit=True,
        height=image_np_canvas.shape[0],
        width=image_np_canvas.shape[1],
        drawing_mode="point",
        point_display_radius=6,
        key="canvas",
    )

    # --- Collect points ---
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data.get("objects", [])
        st.session_state["points"] = [(obj["left"], obj["top"]) for obj in objects]

    if "points" in st.session_state:
        st.write("📍 Selected points (resized image):", st.session_state["points"])

        if len(st.session_state["points"]) == 4:
            st.success("✅ 4 corners selected! Applying perspective correction...")

            # Rescale points back to full resolution
            rescaled_points = [(x / scale, y / scale) for (x, y) in st.session_state["points"]]
            pts_src = np.array(rescaled_points, dtype="float32")

            pts_dst = np.array([
                [0, 0],
                [n_cols * 100, 0],
                [n_cols * 100, n_rows * 100],
                [0, n_rows * 100]
            ], dtype="float32")

            # Perspective transform on full-size image
            M = cv2.getPerspectiveTransform(pts_src, pts_dst)
            warped = cv2.warpPerspective(image_np_full, M, (n_cols * 100, n_rows * 100))

            # --- Overlay treatment numbers ---
            for i in range(n_rows):
                for j in range(n_cols):
                    text = str(df.iloc[i, j])
                    x = int((j + 0.5) * 100)
                    y = int((i + 0.5) * 100)
                    cv2.putText(
                        warped, text, (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 0, 255), 2, cv2.LINE_AA
                    )

            st.image(warped, caption="🖼 Warped image with treatment overlay")

            # --- Save ---
            save_dir = f"Trials/{trial_id}/{date_str}"
            os.makedirs(save_dir, exist_ok=True)
            out_path = os.path.join(save_dir, "overlay.png")
            cv2.imwrite(out_path, cv2.cvtColor(warped, cv2.COLOR_RGB2BGR))
            st.success(f"💾 Saved overlay to `{out_path}`")
