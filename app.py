import streamlit as st
import cv2
import numpy as np
import pandas as pd
import os
from datetime import datetime
from PIL import Image
import plotly.express as px
from streamlit_plotly_events import plotly_events

st.set_page_config(layout="wide")
st.title("📸 Trial Plot Overlay Tool (Plotly Version)")

# --- Inputs ---
trial_id = st.text_input("Trial ID", "TrialA")
date_str = st.date_input("Date of Image", datetime.today())

image_file = st.file_uploader("Upload drone image (JPEG/PNG)", type=["jpg","jpeg","png"])
excel_file = st.file_uploader("Upload treatment layout (Excel)", type=["xls","xlsx"])

if st.button("Reset points"):
    st.session_state["points"] = []

if image_file and excel_file:
    # --- Load full image ---
    image_full = Image.open(image_file).convert("RGB")
    image_np_full = np.array(image_full, dtype=np.uint8)

    # --- Resize for display (for clicks only) ---
    max_width = 1200
    scale = min(1.0, max_width / image_full.width)
    if scale < 1.0:
        image_disp = image_full.resize(
            (int(image_full.width * scale), int(image_full.height * scale))
        )
    else:
        image_disp = image_full
    image_np_disp = np.array(image_disp)

    # --- Load Excel ---
    df = pd.read_excel(excel_file, header=None)
    n_rows, n_cols = df.shape
    st.write(f"📑 Detected treatment grid: **{n_rows} rows × {n_cols} cols**")

    # --- Plotly figure for clicking ---
    fig = px.imshow(image_np_disp)
    fig.update_layout(
        dragmode="drawopenpath",
        margin=dict(l=0, r=0, t=0, b=0),
    )
    fig.update_xaxes(showticklabels=False).update_yaxes(showticklabels=False)

    st.markdown("### Step 1: Click 4 outer corners of the grid (Top-Left, Top-Right, Bottom-Right, Bottom-Left)")

    click_result = plotly_events(fig, click_event=True, select_event=False, override_height=image_disp.height)

    if "points" not in st.session_state:
        st.session_state["points"] = []

    if click_result:
        # Plotly gives x,y coords (x=col, y=row)
        x, y = click_result[0]["x"], click_result[0]["y"]
        st.session_state["points"].append((x, y))

    st.write("📍 Selected points (on resized image):", st.session_state["points"])

    # --- Once 4 points selected ---
    if len(st.session_state["points"]) == 4:
        st.success("✅ 4 corners selected! Applying perspective correction...")

        # Rescale back to full resolution
        rescaled_points = [(x / scale, y / scale) for (x, y) in st.session_state["points"]]
        pts_src = np.array(rescaled_points, dtype="float32")

        pts_dst = np.array([
            [0, 0],
            [n_cols * 100, 0],
            [n_cols * 100, n_rows * 100],
            [0, n_rows * 100]
        ], dtype="float32")

        # Perspective transform
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
