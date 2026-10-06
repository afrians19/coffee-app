"""
Grind Size Analyzer (Particle Size Distribution - PSD)
Integrated Module for Airkopi Barista App
Based on optical particle detection algorithms by Jonathan Gagné.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import cv2
import io
import gc

# Preset reference coins & objects (diameters in mm)
REFERENCE_OBJECTS = {
    "US Quarter (24.26 mm)": 24.26,
    "US Dime (17.91 mm)": 17.91,
    "US Penny (19.05 mm)": 19.05,
    "US Dollar (26.92 mm)": 26.92,
    "1 Euro (23.25 mm)": 23.25,
    "2 Euros (25.75 mm)": 25.75,
    "50 Euro Cents (24.25 mm)": 24.25,
    "20 Euro Cents (22.25 mm)": 22.25,
    "Canadian Quarter (23.81 mm)": 23.81,
    "Canadian Dollar (26.50 mm)": 26.50,
    "Canadian Dime (18.03 mm)": 18.03,
    "Custom / Manual (Coin/Washer)": None
}

def detect_coin_scale(image_rgb, ref_diameter_mm):
    """Detect reference coin/washer using contour compactness & edge gradient."""
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 2)
    h, w = gray.shape
    min_dim = min(h, w)

    edges = cv2.Canny(blurred, 40, 120)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilated_edges = cv2.dilate(edges, kernel)
    contours, _ = cv2.findContours(dilated_edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    best_circle = None
    best_score = -1.0
    min_r = int(min_dim * 0.03)
    max_r = int(min_dim * 0.45)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < np.pi * (min_r ** 2) or area > np.pi * (max_r ** 2):
            continue

        (cx, cy), radius = cv2.minEnclosingCircle(cnt)
        if radius < min_r or radius > max_r:
            continue

        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue
        circularity = (4.0 * np.pi * area) / (perimeter ** 2)
        circle_area = np.pi * (radius ** 2)
        fill_ratio = area / circle_area

        if circularity > 0.60 and fill_ratio > 0.65:
            score = circularity * fill_ratio * area
            if score > best_score:
                best_score = score
                best_circle = (int(cx), int(cy), int(radius))

    if best_circle is None:
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=min_dim // 3,
            param1=80,
            param2=55,
            minRadius=min_r,
            maxRadius=max_r
        )
        if circles is not None and len(circles) > 0:
            c = np.round(circles[0, :]).astype("int")
            candidates = []
            for item in c:
                cx, cy, r = int(item[0]), int(item[1]), int(item[2])
                if r < min_r or r > max_r:
                    continue
                if cx - r < 0 or cx + r >= w or cy - r < 0 or cy + r >= h:
                    continue
                candidates.append((cx, cy, r))
            if candidates:
                best_circle = candidates[0]

    if best_circle is not None:
        x, y, r = best_circle
        diameter_px = r * 2.0
        calculated_scale = diameter_px / ref_diameter_mm
        return calculated_scale, (x, y, r)

    return None, None

def analyze_particles(image_np, threshold_pct, min_surface, max_cluster_axis, min_roundness, pixel_scale, crop_box=None, coin_circle=None):
    """Connected component particle detection with mobile memory optimization."""
    h_orig, w_orig = image_np.shape[:2]
    if crop_box:
        y0 = int(crop_box[0] * h_orig)
        y1 = int(crop_box[1] * h_orig)
        x0 = int(crop_box[2] * w_orig)
        x1 = int(crop_box[3] * w_orig)
        sub_img = image_np[y0:y1, x0:x1]
    else:
        sub_img = image_np
        y0, x0 = 0, 0

    blue_ch = sub_img[:, :, 2].astype(np.float32)
    bg_median = float(np.median(blue_ch))
    thresh_val = bg_median * (threshold_pct / 100.0)

    binary_mask = (blue_ch < thresh_val).astype(np.uint8)

    # Exclude coin area so it isn't counted as a giant coffee boulder
    if coin_circle is not None:
        ccx, ccy, ccr = coin_circle
        ccx_sub = ccx - x0
        ccy_sub = ccy - y0
        cv2.circle(binary_mask, (int(ccx_sub), int(ccy_sub)), int(ccr * 1.08), 0, -1)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)

    particles = []
    vis_overlay = np.copy(sub_img)

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < min_surface:
            continue

        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        diag = np.sqrt(w**2 + h**2)
        if diag > max_cluster_axis * 2:
            continue

        comp_mask = (labels == i).astype(np.uint8)
        contours, _ = cv2.findContours(comp_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if not contours:
            continue
        cnt = contours[0]
        if len(cnt) < 5:
            continue

        try:
            ellipse = cv2.fitEllipse(cnt)
            (cx, cy), (d1, d2), _ = ellipse
            major_axis = max(d1, d2) / 2.0
            minor_axis = min(d1, d2) / 2.0
        except Exception:
            (cx, cy), radius = cv2.minEnclosingCircle(cnt)
            major_axis = float(radius)
            minor_axis = float(radius)

        if major_axis > max_cluster_axis:
            continue

        roundness = float(area) / (np.pi * (major_axis ** 2) + 1e-5)
        if roundness < min_roundness:
            continue

        surface_px2 = float(area)
        short_axis = max(surface_px2 / (np.pi * major_axis + 1e-5), 0.5)
        volume_px3 = np.pi * (short_axis ** 2) * major_axis

        diameter_mm = 2.0 * np.sqrt(major_axis * short_axis) / pixel_scale
        surface_mm2 = surface_px2 / (pixel_scale ** 2)
        volume_mm3 = volume_px3 / (pixel_scale ** 3)

        particles.append({
            "id": i,
            "x": cx + x0,
            "y": cy + y0,
            "diameter_um": diameter_mm * 1000.0,
            "diameter_mm": diameter_mm,
            "surface_mm2": surface_mm2,
            "volume_mm3": volume_mm3,
            "roundness": roundness
        })

        cv2.drawContours(vis_overlay, [cnt], -1, (217, 119, 6), 1)

    df_particles = pd.DataFrame(particles)
    del labels, binary_mask
    gc.collect()

    return df_particles, vis_overlay, bg_median


def app():
    # Airkopi Card Banner
    st.markdown("""
    <div class="coffee-card" style="padding: 24px; margin-bottom: 24px;">
        <h2 style="margin: 0 0 8px 0; font-family: 'Playfair Display', serif; color: #2D2219;">🔬 Optical Grind Size Analyzer</h2>
        <p style="margin: 0; color: #6B5B4D; font-size: 0.95rem; line-height: 1.6;">
            Analyze your coffee grind size distribution (PSD) from smartphone camera photos. Calibrated using standard coins to measure dominant particle size and fines percentage.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 1. Image Input Section with Mobile Camera Support
    st.markdown('<div class="coffee-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top:0;'>1. Capture / Upload Coffee Sample</h3>", unsafe_allow_html=True)

    input_mode = st.radio(
        "Source Method:",
        ["📁 Upload from Gallery / Files", "📸 Take Photo with Camera", "🧪 Use Demo Sample"],
        horizontal=True
    )

    image_rgb = None

    if input_mode == "📁 Upload from Gallery / Files":
        uploaded_file = st.file_uploader("Upload photo of ground coffee with reference coin", type=["jpg", "jpeg", "png", "webp"])
        if uploaded_file is not None:
            pil_img = Image.open(uploaded_file).convert("RGB")
            # Downsample ultra high-res mobile photos to prevent mobile browser memory limits
            max_dim = 1800
            if max(pil_img.size) > max_dim:
                pil_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            image_rgb = np.array(pil_img)
    elif input_mode == "📸 Take Photo with Camera":
        cam_file = st.camera_input("Snap picture of coffee grounds on white paper with coin")
        if cam_file is not None:
            pil_img = Image.open(cam_file).convert("RGB")
            max_dim = 1800
            if max(pil_img.size) > max_dim:
                pil_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            image_rgb = np.array(pil_img)
    else:
        # Synthetic sample
        w, h = 900, 700
        syn = np.full((h, w, 3), 245, dtype=np.uint8)
        # Reference coin in bottom right
        coin_c = (720, 540)
        coin_r = 75
        cv2.circle(syn, coin_c, coin_r, (160, 165, 170), -1)
        cv2.circle(syn, coin_c, coin_r, (110, 115, 120), 4)
        cv2.putText(syn, "COIN", (690, 545), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (80, 80, 80), 2)
        # Synthetic particles (coarse grind ~2500 um)
        np.random.seed(42)
        for d in np.clip(np.random.lognormal(2.6, 0.38, 280), 4, 45):
            px = np.random.randint(50, 600)
            py = np.random.randint(60, h - 60)
            col = (np.random.randint(40, 70), np.random.randint(25, 45), np.random.randint(15, 30))
            cv2.ellipse(syn, (px, py), (max(int(d / 2), 2), max(int(d / 3), 1)), np.random.randint(0, 180), 0, 360, col, -1)
        image_rgb = syn

    st.markdown('</div>', unsafe_allow_html=True)

    if image_rgb is None:
        st.info("👆 Snap a photo or upload an image to begin optical grind analysis.")
        return

    # 2. Calibration & Detection Settings
    st.markdown('<div class="coffee-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top:0;'>2. Calibration & Detection Parameters</h3>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        ref_obj = st.selectbox("Reference Coin / Object", list(REFERENCE_OBJECTS.keys()), index=0)
        preset_dia = REFERENCE_OBJECTS[ref_obj]
        ref_dia_mm = st.number_input("Coin Diameter (mm)", value=preset_dia if preset_dia else 24.26, step=0.1)
        coin_quadrant = st.selectbox(
            "Coin Location Hint",
            ["Bottom-Right Corner", "Bottom-Left Corner", "Top-Right Corner", "Top-Left Corner", "Anywhere in image", "Manual Coordinates"],
            index=0,
            help="Limits search area so particles aren't mistaken for coins"
        )
    with col2:
        auto_coin = st.checkbox("Auto-detect Coin Circle", value=True)
        manual_scale = st.number_input("Manual Pixel Scale (px/mm)", value=35.0, min_value=1.0, max_value=2000.0, step=1.0)
        threshold_pct = st.slider("Grind Darkness Threshold (%)", 10.0, 90.0, 58.8, 0.5)

    with st.expander("🛠️ Advanced Particle Filters (Clustering & Morphology)"):
        adv_col1, adv_col2 = st.columns(2)
        with adv_col1:
            min_surface_px = st.number_input("Min Particle Area (px²)", value=5, min_value=1, max_value=50)
            max_cluster_axis = st.number_input("Max Semi-Axis (px)", value=140, min_value=30, max_value=500)
        with adv_col2:
            min_roundness = st.slider("Min Roundness (0 to 1)", 0.0, 0.8, 0.0, 0.05)
            crop_roi = st.checkbox("Crop Region (Exclude Edges)", value=False)
        
        crop_box = None
        if crop_roi:
            r_top = st.slider("Top Crop (%)", 0, 50, 0)
            r_bot = st.slider("Bottom Crop (%)", 50, 100, 100)
            r_l = st.slider("Left Crop (%)", 0, 50, 0)
            r_r = st.slider("Right Crop (%)", 50, 100, 100)
            crop_box = (r_top / 100.0, r_bot / 100.0, r_l / 100.0, r_r / 100.0)

    st.markdown('</div>', unsafe_allow_html=True)

    # Scale calculation
    active_scale = manual_scale
    coin_circle_found = None

    if auto_coin and ref_dia_mm > 0:
        h_img, w_img = image_rgb.shape[:2]
        search_img = image_rgb
        off_x, off_y = 0, 0
        if coin_quadrant == "Bottom-Right Corner":
            search_img = image_rgb[int(h_img * 0.45):, int(w_img * 0.45):]
            off_y, off_x = int(h_img * 0.45), int(w_img * 0.45)
        elif coin_quadrant == "Bottom-Left Corner":
            search_img = image_rgb[int(h_img * 0.45):, :int(w_img * 0.55)]
            off_y, off_x = int(h_img * 0.45), 0
        elif coin_quadrant == "Top-Right Corner":
            search_img = image_rgb[:int(h_img * 0.55), int(w_img * 0.45):]
            off_y, off_x = 0, int(w_img * 0.45)
        elif coin_quadrant == "Top-Left Corner":
            search_img = image_rgb[:int(h_img * 0.55), :int(w_img * 0.55)]
            off_y, off_x = 0, 0

        det_scale, circle_p = detect_coin_scale(search_img, ref_dia_mm)
        if det_scale:
            active_scale = det_scale
            sx, sy, sr = circle_p
            coin_circle_found = (sx + off_x, sy + off_y, sr)
            st.success(f"🎯 **Reference Coin Detected:** Scale = **{active_scale:.2f} px/mm** (1 mm = {active_scale:.1f} px)")
        else:
            st.warning("⚠️ Coin circle could not be locked automatically. Using manual scale.")

    # Run particle detection
    with st.spinner("Analyzing coffee particles..."):
        df_particles, vis_overlay, bg_median = analyze_particles(
            image_rgb,
            threshold_pct=threshold_pct,
            min_surface=min_surface_px,
            max_cluster_axis=max_cluster_axis,
            min_roundness=min_roundness,
            pixel_scale=active_scale,
            crop_box=crop_box,
            coin_circle=coin_circle_found
        )

    num_detected = len(df_particles)

    if num_detected == 0:
        st.warning("No coffee particles detected with current settings. Try lowering the Threshold (%) in step 2.")
        return

    # 3. KPI Statistics Cards (Airkopi Palette)
    diameters_um = df_particles["diameter_um"].values
    volumes_mm3 = df_particles["volume_mm3"].values
    total_vol = np.sum(volumes_mm3)

    # Mass-weighted percentiles
    sort_idx = np.argsort(diameters_um)
    sorted_d = diameters_um[sort_idx]
    cum_weights = np.cumsum(volumes_mm3[sort_idx]) / total_vol
    d10 = float(np.interp(0.10, cum_weights, sorted_d))
    d50 = float(np.interp(0.50, cum_weights, sorted_d))
    d90 = float(np.interp(0.90, cum_weights, sorted_d))
    vol_mean = np.sum(diameters_um * volumes_mm3) / total_vol
    fines_pct = (np.sum(volumes_mm3[diameters_um < 400]) / total_vol) * 100.0

    st.markdown("""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px;">
        <div class="coffee-card" style="margin-bottom:0; text-align:center; padding:18px;">
            <p style="margin:0; font-size:0.85rem; color:#6B5B4D;">Particles Count</p>
            <h2 style="margin:4px 0 0 0; color:#B45309;">{:,}</h2>
        </div>
        <div class="coffee-card" style="margin-bottom:0; text-align:center; padding:18px;">
            <p style="margin:0; font-size:0.85rem; color:#6B5B4D;">Mass Median (D50)</p>
            <h2 style="margin:4px 0 0 0; color:#B45309;">{:.0f} µm</h2>
        </div>
        <div class="coffee-card" style="margin-bottom:0; text-align:center; padding:18px;">
            <p style="margin:0; font-size:0.85rem; color:#6B5B4D;">Vol-Weighted Mean</p>
            <h2 style="margin:4px 0 0 0; color:#B45309;">{:.0f} µm</h2>
        </div>
        <div class="coffee-card" style="margin-bottom:0; text-align:center; padding:18px;">
            <p style="margin:0; font-size:0.85rem; color:#6B5B4D;">Fines (<400 µm)</p>
            <h2 style="margin:4px 0 0 0; color:#B45309;">{:.1f}%</h2>
        </div>
    </div>
    """.format(num_detected, d50, vol_mean, fines_pct), unsafe_allow_html=True)

    # 4. Interactive PSD Plotly Chart (Warm Airkopi Theme)
    st.markdown('<div class="coffee-card">', unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top:0;'>Particle Size Distribution (PSD)</h3>", unsafe_allow_html=True)

    # Compute bins on log-space
    min_val = max(np.percentile(diameters_um, 0.5), 10.0)
    max_val = np.percentile(diameters_um, 99.5)
    bins = np.logspace(np.log10(min_val), np.log10(max_val), 35)

    hist, bin_edges = np.histogram(diameters_um, bins=bins, weights=volumes_mm3 / total_vol)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
    cdf = np.cumsum(hist) / np.sum(hist)

    peak_idx = int(np.argmax(hist))
    peak_um = float(bin_centers[peak_idx])

    fig = go.Figure()
    # Amber/Warm Coffee Distribution Bars
    fig.add_trace(go.Bar(
        x=[float(v) for v in bin_centers],
        y=[float(v) for v in hist],
        name="Mass Fraction",
        marker=dict(color='#D97706', line=dict(color='#B45309', width=1)),
        opacity=0.88,
        hovertemplate='Diameter: %{x:.0f} µm<br>Mass Fraction: %{y:.3f}<extra></extra>'
    ))
    # Elegant Navy CDF Line
    fig.add_trace(go.Scatter(
        x=[float(v) for v in bin_edges[1:]],
        y=[float(v) for v in cdf],
        mode="lines+markers",
        name="Cumulative (CDF)",
        yaxis="y2",
        line=dict(color='#2563EB', width=3, dash='dot'),
        marker=dict(size=4, color='#1D4ED8'),
        hovertemplate='Diameter: %{x:.0f} µm<br>Cumulative: %{y:.1%}<extra></extra>'
    ))

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#FFF9F0",
        plot_bgcolor="#FFF9F0",
        margin=dict(t=50, l=40, r=40, b=40),
        height=480,
        xaxis=dict(
            title=dict(text="Particle Diameter (µm)", font=dict(family="Plus Jakarta Sans", size=14, color="#2B2118")),
            type="log",
            showgrid=True,
            gridcolor="#E8D9C8",
            linecolor="#D8C3A5",
            tickfont=dict(color="#6B5B4D")
        ),
        yaxis=dict(
            title=dict(text="Fraction of Total Mass", font=dict(family="Plus Jakarta Sans", size=14, color="#2B2118")),
            showgrid=True,
            gridcolor="#E8D9C8",
            linecolor="#D8C3A5",
            tickfont=dict(color="#6B5B4D")
        ),
        yaxis2=dict(
            title=dict(text="Cumulative Fraction (0-1)", font=dict(family="Plus Jakarta Sans", size=14, color="#2563EB")),
            overlaying="y",
            side="right",
            range=[0, 1.05],
            showgrid=False,
            tickfont=dict(color="#2563EB")
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#2B2118")
        ),
        hoverlabel=dict(bgcolor="#FFFDF8", font=dict(color="#2B2118", size=13))
    )

    st.plotly_chart(fig, theme=None, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 5. Intelligent Brew Classification & Graph Guide
    span_uniformity = (d90 - d10) / (d50 + 1e-5)
    if d50 < 350:
        grind_category = "Extra Fine (Turkish / Espresso)"
        rec_brew = "Ideal for Turkish ibrik or commercial espresso machines. Very high resistance to water flow."
        recipe_hint = "For V60 / Pour-over, adjust your grinder coarser toward ~700 - 1000 µm."
        badge = "🔴"
    elif d50 < 600:
        grind_category = "Fine (Moka Pot / Aeropress / Single Espresso)"
        rec_brew = "Best suited for Moka Pots, standard Aeropress recipes, or single-basket espresso."
        recipe_hint = "For V60 / Pour-over, adjust your grinder coarser toward ~700 - 1000 µm."
        badge = "🟠"
    elif d50 < 1100:
        grind_category = "Medium (V60 / Kalita Wave / Drip Coffee)"
        rec_brew = "Standard filter / pour-over grind. Balances extraction rate with clean, steady percolation."
        recipe_hint = "Already dialed in for standard pour-over brewing."
        badge = "🟢"
    elif d50 < 1700:
        grind_category = "Medium-Coarse (Chemex / Clever Dripper / Cupping)"
        rec_brew = "Great for Chemex thick filters, immersion drippers, or standard SCA cupping sessions."
        recipe_hint = "For French Press / Cold Brew, you can grind slightly coarser (> 2000 µm)."
        badge = "🔵"
    else:
        grind_category = "Coarse (French Press / Cold Brew)"
        rec_brew = "Ideal for full immersion like French Press, Cold Brew, or siphon brewing to prevent over-extraction and muddy cups."
        recipe_hint = "If targeting Pour-over (V60/Chemex), adjust your grinder significantly finer toward ~700 - 1000 µm."
        badge = "🟤"

    st.markdown('<div class="coffee-card">', unsafe_allow_html=True)
    st.markdown(f"<h3 style='margin-top:0; color:#2D2219;'>{badge} Grind Analysis & Brewing Insights</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:1.15rem; margin-bottom:16px;'><strong>Detected Profile:</strong> <span style='color:#B45309; font-weight:700;'>{grind_category}</span></p>", unsafe_allow_html=True)
    
    uniformity_label = "Narrow / High Uniformity" if span_uniformity < 1.3 else "Standard Burr Spread"
    st.markdown(f"""
---
#### 1. Key Metrics Decoded
* **Dominant Peak (Mode):** **{peak_um:.0f} µm ({peak_um / 1000.0:.2f} mm)** — size bucket with the highest concentration of coffee grounds.
* **Mass Median ($D_{{50}}$):** **{d50:.0f} µm ({d50 / 1000.0:.2f} mm)** — exactly 50% of coffee weight is finer, and 50% is coarser.
* **Fines Fraction (< 400 µm):** **{fines_pct:.1f}%** of total mass.
* **Uniformity Index:** **{span_uniformity:.2f}** ({uniformity_label}).

#### 2. Brewing Recommendations
* **Recommended Methods:** {rec_brew}
* **Dialing In Advice:** {recipe_hint}

#### 3. How to Read this Graph
* 🟧 **Amber Bars:** Mass-weighted percentage in each size bucket. A tall, single peak represents clean burr alignment.
* 🔷 **Blue Dotted Line:** Cumulative curve (CDF). Crosses 50% (0.5) at the median size ($D_{{50}}$). A steeper curve indicates higher grind consistency.
""")
    st.markdown('</div>', unsafe_allow_html=True)

    # 6. Particle Detection Map & Visual Inspection
    with st.expander("🔍 View Optical Inspection & Detected Outlines"):
        c_i1, c_i2 = st.columns(2)
        with c_i1:
            st.markdown("**Original Image & Coin Scale**")
            disp_orig = np.copy(image_rgb)
            if coin_circle_found:
                cx, cy, cr = coin_circle_found
                cv2.circle(disp_orig, (cx, cy), cr, (37, 99, 235), 3)
                cv2.circle(disp_orig, (cx, cy), 4, (220, 38, 38), -1)
                cv2.putText(disp_orig, f"Coin ({ref_dia_mm:.1f}mm)", (cx - cr, cy - cr - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (37, 99, 235), 2)
            st.image(disp_orig, use_container_width=True)
        with c_i2:
            st.markdown(f"**Detected Outlines ({num_detected:,} particles)**")
            st.image(vis_overlay, use_container_width=True)

        csv_buf = io.StringIO()
        df_particles[["id", "diameter_um", "diameter_mm", "surface_mm2", "volume_mm3", "roundness"]].round(2).to_csv(csv_buf, index=False)
        st.download_button(
            label="📥 Download Particles CSV",
            data=csv_buf.getvalue(),
            file_name="coffee_particle_psd.csv",
            mime="text/csv"
        )
