import streamlit as st
import cv2
import numpy as np
import pandas as pd
import os
from datetime import datetime
from PIL import Image
from streamlit_drawable_canvas import st_canvas

st.set_page_config(layout="wide")
st.title("📸 Trial Plot Overlay Tool (Prototype)")

# --- Inputs ---
trial_id = st.text_input("Trial ID", "TrialA")
date_str = st.date_input("Date of Image", datetime.today())

image_file = st.file_uploader("Upload drone image (JPEG/PNG)", type=["jpg","jpeg","png"])
excel_file = st.file_uploader("Upload treatment layout (Excel)", type=["xls","xlsx"])

if image_file and excel_file:
    # --- Load image ---
    image = Image.open(image_file).convert("RGB")
    image_np = np.array(image)

    # --- Load Excel sheet ---
    df = pd.read_excel(excel_file, header=None)
    n_rows, n_cols = df.shape
    st.write(f"📑 Detected treatment grid: **{n_rows} rows × {n_cols} cols**")

    # --- Canvas for corner selection ---
    st.markdown("### Step 1: Click 4 outer corners of the grid (Top-Left, Top-Right, Bottom-Right, Bottom-Left)")

    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=3,
        stroke_color="#FF0000",
        background_image=image_np,  # ✅ FIXED: must be numpy, not PIL
        update_streamlit=True,
        height=image.size[1],
        width=image.size[0],
        drawing_mode="point",
        point_display_radius=6,
        key="canvas",
    )

    # --- Collect points ---
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        st.session_state["points"] = [(obj["left"], obj["top"]) for obj in objects]

    if "points" in st.session_state:
        st.write("📍 Selected points:", st.session_state["points"])

        if len(st.session_state["points"]) == 4:
            st.success("✅ 4 corners selected! Applying perspective correction...")

            # Source and destination points
            pts_src = np.array(st.session_state["points"], dtype="float32")
            pts_dst = np.array([
                [0, 0],
                [n_cols * 100, 0],
                [n_cols * 100, n_rows * 100],
                [0, n_rows * 100]
            ], dtype="float32")

            # Perspective transform
            M = cv2.getPerspectiveTransform(pts_src, pts_dst)
            warped = cv2.warpPerspective(image_np, M, (n_cols * 100, n_rows * 100))

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

            # --- Save to file system ---
            save_dir = f"Trials/{trial_id}/{date_str}"
            os.makedirs(save_dir, exist_ok=True)
            out_path = os.path.join(save_dir, "overlay.png")
            cv2.imwrite(out_path, cv2.cvtColor(warped, cv2.COLOR_RGB2BGR))

            st.success(f"💾 Saved overlay to `{out_path}`")
