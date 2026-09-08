


import os
import base64
import hashlib
from datetime import datetime

import streamlit as st

from utils.plate_detection import detect_plate
from utils.violation_detection import detect_violation
from utils.ocr import read_plate
from utils.whatsapp import send_whatsapp_message
from database.user_db import get_user
from database.chalan_db import get_violation_fine, save_challan


# Optional: only used if you add a get_all_challans() function to
# database/chalan_db.py (SELECT * FROM challans ORDER BY id DESC).
# The app works fine without it — it just falls back to an in-session log.
try:
    from database.chalan_db import get_all_challans

    HISTORY_AVAILABLE = True
except ImportError:
    HISTORY_AVAILABLE = False


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="TrafficSense AI | Challan Automation",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CAMERA LOCATIONS
# ============================================================

CAMERAS = {
    "CAM-101": "MG Road Junction",
    "CAM-204": "Ring Road Signal",
    "CAM-309": "Highway Toll Plaza",
    "CAM-412": "City Center Circle",
}


# ============================================================
# VIOLATION LABELS
# ============================================================

VIOLATION_LABELS = {
    "WITHOUT_HELMET": ("no helmet", "🪖", "High"),
    "USING_MOBILE": ("using mobile", "📱", "High"),
}

DEFAULT_VIOLATION = ("no parking", "🅿️", "Medium")


# ============================================================
# TRAFFIC RULES
# ============================================================

TRAFFIC_RULES = [
    {
        "icon": "🪖",
        "title": "Helmet Mandatory",
        "note": "ISI-marked helmets required for rider and pillion on two-wheelers.",
        "fine": "₹1,000+",
        "color": "#e63946",
    },
    {
        "icon": "📱",
        "title": "No Mobile While Driving",
        "note": "Using a handheld phone while driving or riding is prohibited.",
        "fine": "₹1,000–₹5,000",
        "color": "#f4a261",
    },
    {
        "icon": "🚦",
        "title": "Obey Traffic Signals",
        "note": "Jumping a red light risks fines and license penalty points.",
        "fine": "₹1,000–₹5,000",
        "color": "#2a9d8f",
    },
    {
        "icon": "🅿️",
        "title": "No-Parking Zones",
        "note": "Avoid parking in marked no-parking areas or blocking traffic flow.",
        "fine": "₹500+",
        "color": "#457b9d",
    },
    {
        "icon": "🛑",
        "title": "Speed Limits",
        "note": "Stay within posted limits, especially near schools and hospitals.",
        "fine": "₹1,000–₹2,000",
        "color": "#e76f51",
    },
    {
        "icon": "🍺",
        "title": "No Drink & Drive",
        "note": "Driving under the influence carries heavy fines and possible arrest.",
        "fine": "₹10,000+",
        "color": "#9d0208",
    },
    {
        "icon": "🪪",
        "title": "Carry Your Documents",
        "note": "Keep license, RC, insurance, and PUC certificate on hand.",
        "fine": "₹500+",
        "color": "#6a4c93",
    },
    {
        "icon": "🔒",
        "title": "Seatbelt Compliance",
        "note": "All occupants, including rear-seat passengers, must wear seatbelts.",
        "fine": "₹1,000",
        "color": "#1d3557",
    },
]


# ============================================================
# IMAGE HELPER
# ============================================================

def get_base64(path):
    """
    Read a local image file and return its base64 string.
    Returns None if the file does not exist.
    """
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None


# ============================================================
# APPLICATION DIRECTORY
# ============================================================

_APP_DIR = os.path.dirname(os.path.abspath(__file__))

_bg_image = get_base64(
    os.path.join(_APP_DIR, "assets", "background.jpg")
)


# ============================================================
# BACKGROUND
# ============================================================

_bg_css = (
    f'background-image: linear-gradient(rgba(6,10,18,0.72), rgba(6,10,18,0.85)), '
    f'url("data:image/jpeg;base64,{_bg_image}");'
    if _bg_image
    else "background: linear-gradient(180deg, #f4f6f9 0%, #e9edf2 100%);"
)


st.markdown(
    f"""
    <style>

    .stApp {{
        {_bg_css}
        background-size: cover;
        background-position: center center;
        background-attachment: fixed;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# APPLICATION STYLES
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       MAIN CONTENT
       ======================================================== */

    .main {
        padding-top: 0.5rem;
    }


    /* ========================================================
       APPLICATION HEADER
       ======================================================== */

    .app-header {
        padding: 28px 32px;
        border-radius: 16px;
        background: linear-gradient(
            135deg,
            rgba(15,76,129,0.95),
            rgba(24,124,150,0.9)
        );
        color: #ffffff;
        margin-bottom: 24px;
    }

    .app-header h1 {
        margin: 0;
        font-size: 32px;
        font-weight: 700;
        color: #ffffff !important;
    }

    .app-header p {
        margin: 6px 0 0 0;
        font-size: 15px;
        opacity: 0.9;
        color: #ffffff !important;
    }

    .status-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        background: rgba(255,255,255,0.18);
        font-size: 13px;
        margin-top: 12px;
        color: #ffffff !important;
    }

    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #3ddc84;
        margin-right: 6px;
    }


    /* ========================================================
       SECTION TITLES
       ======================================================== */

    .section-title {
        font-size: 20px;
        font-weight: 700;
        margin-top: 22px;
        margin-bottom: 10px;
        color: #000000 !important;
    }


    /* ========================================================
       FILE UPLOADER
       ======================================================== */

    [data-testid="stFileUploader"] label {
        color: #000000 !important;
        font-weight: 600;
    }

    [data-testid="stFileUploader"] section {
        color: #000000 !important;
    }

    [data-testid="stFileUploader"] section * {
        color: #000000 !important;
    }


    /* ========================================================
       CAPTIONS
       ======================================================== */

    [data-testid="stCaptionContainer"] {
        color: #000000 !important;
    }

    [data-testid="stImage"] figcaption {
        color: #000000 !important;
        font-weight: 600;
    }


    /* ========================================================
       METRICS
       ======================================================== */

    [data-testid="stMetric"] {
        color: #000000 !important;
    }

    [data-testid="stMetricLabel"] {
        color: #000000 !important;
    }

    [data-testid="stMetricValue"] {
        color: #000000 !important;
    }


    /* ========================================================
       TABS
       ======================================================== */

    .stTabs [data-baseweb="tab"] p {
        color: #000000 !important;
        font-weight: 600;
    }


    /* ========================================================
       INFORMATION CARDS
       ======================================================== */

    .info-card,
    .challan-card {
        padding: 20px 22px;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
        margin-bottom: 15px;
        color: #1a1a1a;
    }


    /* ========================================================
       FINAL CHALLAN CARD
       ======================================================== */

    .challan-card {
        border: 2px solid #ffb703;
        background: linear-gradient(
            180deg,
            rgba(255,255,255,0.97),
            rgba(255,247,225,0.97)
        );
    }

    .challan-title {
        text-align: center;
        font-size: 26px;
        font-weight: 700;
        margin-bottom: 4px;
        color: #14213d;
    }

    .challan-id {
        text-align: center;
        font-size: 13px;
        opacity: 0.65;
        margin-bottom: 18px;
        color: #000000;
    }

    .fine-amount {
        text-align: center;
        font-size: 28px;
        font-weight: 700;
        margin-top: 12px;
        color: #d62828;
    }


    /* ========================================================
       VIOLATION BADGES
       ======================================================== */

    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        margin: 2px 4px 2px 0;
    }

    .badge-high {
        background: rgba(220,53,69,0.18);
        color: #ff6b6b;
    }

    .badge-medium {
        background: rgba(255,193,7,0.2);
        color: #ffca3a;
    }


    /* ========================================================
       TECHNOLOGY BADGES
       ======================================================== */

    .tech-badge {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 8px;
        background: rgba(76, 201, 240, 0.18);
        color: #000000 !important;
        font-size: 13px;
        margin: 3px 4px;
        font-weight: 600;
    }


    /* ========================================================
       TRAFFIC RULE CARDS
       ======================================================== */

    .rule-card {
        padding: 16px 18px;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.95);
        border-left: 6px solid var(--rule-color, #457b9d);
        box-shadow: 0 3px 10px rgba(0,0,0,0.22);
        margin-bottom: 14px;
        color: #000000;
        height: 100%;
    }

    .rule-card .rule-title {
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 4px;
        color: #000000;
    }

    .rule-card .rule-note {
        font-size: 13px;
        opacity: 0.8;
        margin-bottom: 8px;
        color: #000000;
    }

    .rule-card .rule-fine {
        display: inline-block;
        font-size: 12px;
        font-weight: 700;
        padding: 2px 9px;
        border-radius: 999px;
        background: var(--rule-color, #457b9d);
        color: #ffffff;
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    div.stButton > button,
    div.stDownloadButton > button {
        border-radius: 10px;
        font-weight: 600;
        border: none;
        background: linear-gradient(
            135deg,
            #0f4c81,
            #187c96
        );
        color: #ffffff;
    }

    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        background: linear-gradient(
            135deg,
            #187c96,
            #0f4c81
        );
        color: #ffffff;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.95);
    }

    section[data-testid="stSidebar"] * {
        color: #000000 !important;
    }

    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] small {
        color: #000000 !important;
    }


    /* ========================================================
       DATAFRAME
       ======================================================== */

    [data-testid="stDataFrame"] {
        color: #000000 !important;
    }


    /* ========================================================
       FOOTER
       ======================================================== */

    .footer {
        text-align: center;
        margin-top: 40px;
        padding: 18px;
        font-size: 13px;
        color: #000000 !important;
        font-weight: 500;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SETUP
# ============================================================

os.makedirs("outputs", exist_ok=True)

st.session_state.setdefault(
    "vehicles_scanned",
    0
)

st.session_state.setdefault(
    "total_fine_collected",
    0
)

st.session_state.setdefault(
    "session_log",
    []
)

st.session_state.setdefault(
    "processed_hashes",
    set()
)


# ============================================================
# VIOLATION SELECTION
# ============================================================

def pick_violation(detections):
    """
    Return (label, icon, severity) for the
    highest-priority violation found.
    """

    for detection in detections:

        detected_class = detection.get(
            "class_name",
            ""
        ).upper()

        if detected_class in VIOLATION_LABELS:
            return VIOLATION_LABELS[detected_class]

    return DEFAULT_VIOLATION


# ============================================================
# CHALLAN ID GENERATION
# ============================================================

def make_challan_id(file_bytes: bytes) -> str:

    digest = hashlib.md5(
        file_bytes
    ).hexdigest()[:6].upper()

    return (
        f"CH-{datetime.now().strftime('%Y%m%d')}-{digest}"
    )


# ============================================================
# TRAFFIC RULES DISPLAY
# ============================================================

def render_traffic_rules():

    st.markdown(
        '<div class="section-title">📚 Know Your Traffic Rules</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "A quick refresher so this doesn't happen again — "
        "fine amounts shown are illustrative; check your local "
        "traffic authority for the exact current figures."
    )

    cols = st.columns(2)

    for i, rule in enumerate(TRAFFIC_RULES):

        with cols[i % 2]:

            st.markdown(
                f"""
                <div class="rule-card" style="--rule-color: {rule['color']};">
                    <div class="rule-title">
                        {rule['icon']} {rule['title']}
                    </div>
                    <div class="rule-note">
                        {rule['note']}
                    </div>
                    <span class="rule-fine">
                        Fine: {rule['fine']}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# RECEIPT GENERATION
# ============================================================

def build_receipt_text(
    challan_id,
    timestamp,
    camera_id,
    location,
    user,
    violation_label,
    fine,
):

    return (
        "==============================================\n"
        "        TRAFFIC CHALLAN - OFFICIAL RECEIPT\n"
        "==============================================\n"
        f"Challan ID     : {challan_id}\n"
        f"Date / Time    : {timestamp}\n"
        f"Camera         : {camera_id} ({location})\n"
        "----------------------------------------------\n"
        f"Vehicle Number : {user['vehicle_reg']}\n"
        f"Owner Name     : {user['user_name']}\n"
        f"Vehicle Type   : {user['vehicle_type']}\n"
        f"Contact Number : {user['mobile_number']}\n"
        "----------------------------------------------\n"
        f"Violation      : {violation_label}\n"
        f"Fine Amount    : Rs. {fine}\n"
        "==============================================\n"
        "Pay within 15 days to avoid additional penalty.\n"
        "==============================================\n"
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="app-header">
        <h1>🚦 TrafficSense AI</h1>
        <p>
            Automated number-plate recognition,
            violation detection, and e-challan generation
        </p>
        <div class="status-pill">
            <span class="status-dot"></span>
            System Online
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("### 📊 Live Statistics")

    stat_col1, stat_col2 = st.columns(2)

    scanned_placeholder = stat_col1.empty()
    fine_placeholder = stat_col2.empty()

    scanned_placeholder.metric(
        "Vehicles Scanned",
        st.session_state["vehicles_scanned"],
    )

    fine_placeholder.metric(
        "Fine Collected",
        f"₹{st.session_state['total_fine_collected']}",
    )

    st.divider()

    st.markdown("### 📷 Camera / Location")

    camera_id = st.selectbox(
        "Active camera",
        list(CAMERAS.keys()),
    )

    st.caption(
        f"📍 {CAMERAS[camera_id]}"
    )

    st.divider()

    with st.expander("ℹ️ About this system"):

        st.markdown(
            "This demo pipeline combines a **YOLO-based detector** "
            "for plates and violations, an **OCR engine** for "
            "plate reading, and a **MySQL** backend for owner "
            "and fine records — wrapped in a **Streamlit** "
            "interface for end-to-end automation."
        )

        st.markdown(
            "".join(
                f'<span class="tech-badge">{t}</span>'
                for t in [
                    "YOLOv8",
                    "OpenCV",
                    "OCR",
                    "MySQL",
                    "Streamlit",
                    "Python",
                    "WhatsApp",
                ]
            ),
            unsafe_allow_html=True,
        )


# ============================================================
# MAIN TABS
# ============================================================

tab_detect, tab_history, tab_about = st.tabs(
    [
        "🔍 Detect & Generate Challan",
        "📁 Challan History",
        "🧩 System Overview",
    ]
)


# ============================================================
# TAB 1 — DETECTION
# ============================================================

with tab_detect:

    st.markdown(
        '<div class="section-title">📤 Upload Vehicle Image</div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Choose a vehicle image",
        type=["jpg", "jpeg", "png"],
        help=(
            "Upload a clear vehicle image containing "
            "a visible number plate."
        ),
    )

    if uploaded_file is not None:

        file_bytes = uploaded_file.getbuffer()

        image_path = "outputs/uploaded_vehicle.jpg"

        with open(image_path, "wb") as f:
            f.write(file_bytes)

        challan_id = make_challan_id(
            bytes(file_bytes)
        )

        already_counted = (
            challan_id
            in st.session_state["processed_hashes"]
        )

        st.image(
            image_path,
            caption="Uploaded Vehicle Image",
            use_container_width=True,
        )

        try:

            with st.status(
                "Analyzing vehicle image...",
                expanded=True,
            ) as status:

                status.write(
                    "🔍 Detecting number plate..."
                )

                plates, detected_image_path, cropped_plate_path = (
                    detect_plate(image_path)
                )

                if not plates:

                    status.update(
                        label="Number Plate Detection Failed",
                        state="error",
                    )

                    st.error(
                        "❌ Number plate could not be detected. "
                        "Try a clearer, front/rear-facing image "
                        "of the vehicle."
                    )

                    st.stop()

                status.write(
                    "✅ Number plate located successfully"
                )

                status.write(
                    "🚨 Analyzing traffic violations..."
                )

                violations = detect_violation(
                    image_path
                )

                (
                    violation_label,
                    violation_icon,
                    severity,
                ) = pick_violation(violations)

                status.write(
                    f"✅ Violation category identified: "
                    f"{violation_label}"
                )

                status.write(
                    "🔤 Reading registration number..."
                )

                plate_number = read_plate(
                    cropped_plate_path
                )

                status.write(
                    f"✅ Registration number detected: "
                    f"{plate_number}"
                )

                status.write(
                    "👤 Verifying registered vehicle owner..."
                )

                user = get_user(
                    plate_number
                )

                status.update(
                    label="Vehicle Analysis Completed Successfully",
                    state="complete",
                )

        except Exception as exc:

            st.error(
                f"⚠️ Processing failed unexpectedly: {exc}"
            )

            st.stop()


        # ====================================================
        # DETECTION RESULTS
        # ====================================================

        st.markdown(
            '<div class="section-title">🔎 Detection Results</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:

            st.image(
                detected_image_path,
                caption="Detected Number Plate",
                use_container_width=True,
            )

        with col2:

            if cropped_plate_path is not None:

                st.image(
                    cropped_plate_path,
                    caption="Cropped Number Plate",
                    use_container_width=True,
                )


        # ====================================================
        # VIOLATION BADGE
        # ====================================================

        badge_class = (
            "badge-high"
            if severity == "High"
            else "badge-medium"
        )

        st.markdown(
            f"""
            <div>
                <span style="font-size: 24px;">{violation_icon}</span>
                <span class="badge {badge_class}">
                    {severity} severity
                </span>
                <span class="badge {badge_class}">
                    {violation_label.title()}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


        # ====================================================
        # PLATE NUMBER
        # ====================================================

        st.success(
            f"🔢 Vehicle Registration Read: **{plate_number}**"
        )


        # ====================================================
        # OWNER LOOKUP
        # ====================================================

        if not user:

            st.error(
                f"❌ No vehicle owner found for "
                f"registration number: {plate_number}"
            )

            st.stop()


        # ====================================================
        # VEHICLE OWNER DETAILS
        # ====================================================

        st.markdown(
            '<div class="section-title">👤 Vehicle Owner Details</div>',
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:

            st.info(
                f"**Owner Name**\n\n"
                f"{user['user_name']}"
            )

            st.info(
                f"**Vehicle Registration**\n\n"
                f"{user['vehicle_reg']}"
            )

        with col2:

            st.info(
                f"**Vehicle Type**\n\n"
                f"{user['vehicle_type']}"
            )

            st.info(
                f"**Mobile Number**\n\n"
                f"{user['mobile_number']}"
            )


        # ====================================================
        # VIOLATION & FINE
        # ====================================================

        st.markdown(
            '<div class="section-title">💰 Violation & Fine</div>',
            unsafe_allow_html=True,
        )

        violation = get_violation_fine(
            violation_label
        )

        if not violation:

            st.error(
                f"⚠️ Violation '{violation_label}' "
                "was not found in the challan database."
            )

            st.stop()


        col1, col2 = st.columns(2)

        col1.warning(
            f"🚨 **Violation**\n\n"
            f"{violation['violation_name']}"
        )

        col2.warning(
            f"💰 **Fine Amount**\n\n"
            f"₹{violation['fine']}"
        )


        # ====================================================
        # FINAL CHALLAN
        # ====================================================

        timestamp = datetime.now().strftime(
            "%d %b %Y, %I:%M %p"
        )

        st.divider()

        st.markdown(
            '<div class="challan-card">',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="challan-title">🧾 FINAL CHALLAN</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="challan-id">
                Challan ID: {challan_id}
                &nbsp;|&nbsp;
                {timestamp}
            </div>
            """,
            unsafe_allow_html=True,
        )


        col1, col2 = st.columns(2)

        with col1:

            st.write(
                f"**Vehicle Number:** "
                f"{user['vehicle_reg']}"
            )

            st.write(
                f"**Owner Name:** "
                f"{user['user_name']}"
            )

            st.write(
                f"**Vehicle Type:** "
                f"{user['vehicle_type']}"
            )

            st.write(
                f"**Camera:** "
                f"{camera_id} ({CAMERAS[camera_id]})"
            )

        with col2:

            st.write(
                f"**Violation:** "
                f"{violation['violation_name']}"
            )

            st.write(
                f"**Fine Amount:** "
                f"₹{violation['fine']}"
            )

            st.write(
                f"**Issued On:** "
                f"{timestamp}"
            )


        st.markdown(
            f"""
            <div class="fine-amount">
                Fine Payable: ₹{violation["fine"]}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


        # ====================================================
        # SAVE CHALLAN
        # ====================================================

        try:

            save_challan(
                vehicle_reg=user["vehicle_reg"],
                owner_name=user["user_name"],
                vehicle_type=user["vehicle_type"],
                violation_name=violation["violation_name"],
                fine=violation["fine"],
            )

            st.success(
                "🎫 Challan generated and saved successfully!"
            )

        except Exception as exc:

            st.warning(
                "Challan displayed above but could not "
                f"be saved to the database: {exc}"
            )


        # ====================================================
        # SESSION STATISTICS
        # ====================================================

        if not already_counted:

            st.session_state["processed_hashes"].add(
                challan_id
            )

            st.session_state["vehicles_scanned"] += 1

            st.session_state["total_fine_collected"] += (
                violation["fine"]
            )

            st.session_state["session_log"].append(
                {
                    "Challan ID": challan_id,
                    "Timestamp": timestamp,
                    "Vehicle Number": user["vehicle_reg"],
                    "Owner": user["user_name"],
                    "Violation": violation["violation_name"],
                    "Fine": violation["fine"],
                    "Camera": camera_id,
                }
            )

            scanned_placeholder.metric(
                "Vehicles Scanned",
                st.session_state["vehicles_scanned"],
            )

            fine_placeholder.metric(
                "Fine Collected",
                f"₹{st.session_state['total_fine_collected']}",
            )


        # ====================================================
        # RECEIPT
        # ====================================================

        receipt_text = build_receipt_text(
            challan_id,
            timestamp,
            camera_id,
            CAMERAS[camera_id],
            user,
            violation["violation_name"],
            violation["fine"],
        )


        # ====================================================
        # RECEIPT + WHATSAPP + NEW VEHICLE
        # ====================================================

        col_a, col_b, col_c = st.columns(3)

        with col_a:

            st.download_button(
                "⬇️ Download Receipt",
                data=receipt_text,
                file_name=f"{challan_id}.txt",
                use_container_width=True,
            )

        with col_b:

            if st.button(
                "📱 Send WhatsApp",
                use_container_width=True,
            ):

                try:

                    send_whatsapp_message(
                        vehicle_number=user["vehicle_reg"],
                        owner_name=user["user_name"],
                        violation=violation["violation_name"],
                        fine=violation["fine"],
                        challan_id=challan_id,
                        timestamp=timestamp,
                    )

                    st.success(
                        "📱 WhatsApp opened with the "
                        "challan message!"
                    )

                except Exception as exc:

                    st.error(
                        f"❌ Could not open WhatsApp: {exc}"
                    )

        with col_c:

            if st.button(
                "🔄 Process New Vehicle",
                use_container_width=True,
            ):

                st.rerun()


        # ====================================================
        # TRAFFIC RULES
        # ====================================================

        st.divider()

        render_traffic_rules()


# ============================================================
# TAB 2 — CHALLAN HISTORY
# ============================================================

with tab_history:

    st.markdown(
        '<div class="section-title">📁 Recent Challans</div>',
        unsafe_allow_html=True,
    )

    records = None


    # ========================================================
    # DATABASE HISTORY
    # ========================================================

    if HISTORY_AVAILABLE:

        try:

            records = get_all_challans()

        except Exception:

            records = None


    # ========================================================
    # SESSION HISTORY FALLBACK
    # ========================================================

    if not records:

        records = st.session_state["session_log"]

        if not HISTORY_AVAILABLE:

            st.caption(
                "Showing this session's activity only. "
                "Add a `get_all_challans()` function to "
                "`database/chalan_db.py` to persist history "
                "across sessions."
            )


    # ========================================================
    # DISPLAY HISTORY
    # ========================================================

    if records:

        total_fine = sum(
            r.get(
                "Fine",
                r.get("fine", 0)
            )
            for r in records
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Challans",
            len(records),
        )

        c2.metric(
            "Total Fine Collected",
            f"₹{total_fine}",
        )

        st.dataframe(
            records,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No challans have been generated yet "
            "in this session."
        )


# ============================================================
# TAB 3 — SYSTEM OVERVIEW
# ============================================================

with tab_about:

    st.markdown(
        '<div class="section-title">🧩 How the System Works</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <ol style="
            color:#000000;
            line-height:1.8;
            font-size:15px;
        ">
            <li>
                <b>Image Upload</b> —
                a traffic camera frame or manually captured
                photo is submitted.
            </li>
            <li>
                <b>Number Plate Detection</b> —
                a YOLO-based model locates the plate region.
            </li>
            <li>
                <b>Violation Detection</b> —
                a second detector flags helmet-less riders,
                mobile usage, or improper parking within
                the frame.
            </li>
            <li>
                <b>OCR</b> —
                the cropped plate is passed through an OCR
                engine to extract the registration number.
            </li>
            <li>
                <b>Owner Lookup</b> —
                the registration number is matched against
                the vehicle owner database.
            </li>
            <li>
                <b>Fine Lookup & Challan Generation</b> —
                the detected violation is mapped to a fine
                amount, and a challan record is generated
                and persisted.
            </li>
            <li>
                <b>WhatsApp Notification</b> —
                a WhatsApp chat is opened with the challan
                details pre-filled for the test number.
            </li>
        </ol>
        """,
        unsafe_allow_html=True,
    )


    # ========================================================
    # TECH STACK
    # ========================================================

    st.markdown(
        '<div class="section-title">🛠️ Tech Stack</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "".join(
            f'<span class="tech-badge">{t}</span>'
            for t in [
                "Python",
                "Streamlit",
                "YOLOv8",
                "OpenCV",
                "OCR (Tesseract/EasyOCR)",
                "MySQL",
                "WhatsApp Click-to-Chat",
            ]
        ),
        unsafe_allow_html=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        🚦 TrafficSense AI — Traffic Challan Automation System |
        Computer Vision + OCR + Relational Database + WhatsApp
    </div>
    """,
    unsafe_allow_html=True,
)

