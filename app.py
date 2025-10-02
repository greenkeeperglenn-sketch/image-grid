import streamlit as st
import cv2
import numpy as np
import pandas as pd
import os
from datetime import datetime
from PIL import Image

st.set_page_config(layout="wide")

st.title("Trial Plot Overlay Tool")

# --- Inputs ---
trial_id = st.text_input("Trial ID", "TrialA")
date_str = st.date_input("Date of Image", datetime.today())

marker_color = st.selectbox("Marker color", ["Red", "White"])

image_file = st.file_uploader("Upload drone image (JPEG/PNG)", type=["jpg","jpeg","png"])
excel_file = st.file_uploader("Upload treatment layout (Excel)", type=["xls","xlsx"])

if image_file and excel_file:
    # --- Load image ---
    image = Image.open(image_file).convert("RGB")
    image_np = np.array(image)

    # --- Load Excel sheet ---
    df = pd.read_excel(excel_file, header=None)
    n_rows, n_cols = df.shape

    st.write("Detected treatment grid:", f"{n_rows} rows × {n_cols} cols")

    st.image(image, caption="Drone image (click corners to align)")

    st.markdown("""
    ⚠️ Prototype note: For now, please click the **four outer corners of your grid manually**.
    Future versions will auto-detect red/white markers.
    """)

    # Placeholder for clicked points
    if "points" not in st.session_state:
        st.session_state["points"] = []

    # Reset button
    if st.button("Reset points"):
        st.session_state["points"] = []

    # Corner clicking (semi-automatic)
    clicked = st.image(image, caption="Click 4 corners (top-left, top-right, bottom-right, bottom-left)")
    # In Streamlit this would use st_canvas or streamlit-drawable-canvas in real use

    if len(st.session_state["points"]) == 4:
        st.success("4 corners selected! Applying perspective correction...")

        pts_src = np.array(st.session_state["points"], dtype="float32")
        pts_dst = np.array([
            [0,0],
            [n_cols*100, 0],
            [n_cols*100, n_rows*100],
            [0, n_rows*100]
        ], dtype="float32")

        # Warp image to rectangle
        M = cv2.getPerspectiveTransform(pts_src, pts_dst)
        warped = cv2.warpPerspective(image_np, M, (n_cols*100, n_rows*100))

        # Overlay treatment numbers
        for i in range(n_rows):
            for j in range(n_cols):
                text = str(df.iloc[i,j])
                x = int((j+0.5)*100)
                y = int((i+0.5)*100)
                cv2.putText(warped, text, (x,y),
                            cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0,0,255), 2, cv2.LINE_AA)

        st.image(warped, caption="Warped image with treatment overlay")

        # --- Save to file system ---
        save_dir = f"Trials/{trial_id}/{date_str}"
        os.makedirs(save_dir, exist_ok=True)
        out_path = os.path.join(save_dir, "overlay.png")
        cv2.imwrite(out_path, cv2.cvtColor(warped, cv2.COLOR_RGB2BGR))

        st.success(f"Saved overlay to {out_path}")
