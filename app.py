import streamlit as st
import streamlit.components.v1 as components
import pickle
import pandas as pd
import plotly.graph_objects as go
import os
from fpdf import FPDF
import tempfile
from datetime import datetime
import re
import hashlib
from io import BytesIO

try:
    from PIL import Image, ImageOps, ImageFilter
except Exception:
    Image = None
    ImageOps = None
    ImageFilter = None

try:
    import pytesseract
except Exception:
    pytesseract = None

try:
    from pypdf import PdfReader
except Exception:
    try:
        from PyPDF2 import PdfReader
    except Exception:
        PdfReader = None


st.set_page_config(page_title="BioPredict AI", page_icon=":material/monitor_heart:", layout="wide")


ORGAN_DATA = {
    "Diabetes": {
        "organ": "Pancreas",
        "subtitle": "Diabetes, insulin resistance, metabolic risk",
        "status": "Medium",
        "tone": "#00e0b8",
        "markers": [
            ("Glucose", "Fasting blood sugar"),
            ("Insulin", "Pancreatic response"),
            ("BMI", "Metabolic load"),
            ("DPF", "Family risk signal"),
        ],
        "summary": "Pancreas and metabolic screening using glucose, insulin, BMI, age, and family-history indicators.",
        "doctor": "Endocrinologist",
        "tests": "HbA1c, fasting glucose, fasting insulin, lipid profile",
        "signals": [
            "Type 2 diabetes screening",
            "Insulin resistance pattern",
            "High-glucose warning signs",
        ],
        "actions": [
            "Track fasting glucose and HbA1c regularly.",
            "Review diet, weight, sleep, and physical activity habits.",
            "Consult a doctor if glucose or BMI stays above range.",
        ],
    },
    "Heart": {
        "organ": "Heart",
        "subtitle": "CAD, hypertension, cardiac strain",
        "status": "High",
        "tone": "#ff5a67",
        "markers": [
            ("Cholesterol", "Lipid burden"),
            ("BP", "Pressure load"),
            ("ECG", "Electrical rhythm"),
            ("Heart Rate", "Exercise response"),
        ],
        "summary": "Cardiac screening using blood pressure, cholesterol, chest-pain pattern, ECG, and exercise-response markers.",
        "doctor": "Cardiologist",
        "tests": "ECG, lipid profile, troponin if symptomatic, echocardiogram",
        "signals": [
            "Coronary artery disease screening",
            "Hypertension-linked cardiac strain",
            "Cholesterol and exercise-risk pattern",
        ],
        "actions": [
            "Monitor blood pressure and cholesterol trends.",
            "Seek urgent help for chest pain, breathlessness, or fainting.",
            "Discuss ECG and lipid follow-up with a physician.",
        ],
    },
    "Liver": {
        "organ": "Liver",
        "subtitle": "Fatty liver, hepatitis, bile flow stress",
        "status": "Low",
        "tone": "#ffb02e",
        "markers": [
            ("Bilirubin", "Bile processing"),
            ("ALT", "Liver-cell stress"),
            ("AST", "Inflammation marker"),
            ("Albumin", "Protein synthesis"),
        ],
        "summary": "Liver screening using bilirubin, liver enzymes, albumin, protein balance, and age indicators.",
        "doctor": "Gastroenterologist / Hepatologist",
        "tests": "LFT, hepatitis panel, ultrasound abdomen, GGT",
        "signals": [
            "Fatty liver screening",
            "Liver inflammation marker pattern",
            "Bilirubin and protein-balance stress",
        ],
        "actions": [
            "Repeat LFT if enzymes or bilirubin remain high.",
            "Avoid alcohol and unnecessary liver-stressing medicines.",
            "Consider ultrasound and hepatitis screening if advised.",
        ],
    },
    "Kidney": {
        "organ": "Kidneys",
        "subtitle": "CKD, nephropathy, filtration risk",
        "status": "Low",
        "tone": "#4da3ff",
        "markers": [
            ("Creatinine", "Filtration signal"),
            ("Urea", "Waste clearance"),
            ("Sodium", "Electrolyte balance"),
            ("Hemoglobin", "CKD impact marker"),
        ],
        "summary": "Kidney screening using creatinine, urea, electrolytes, urine markers, blood count, and blood-pressure signals.",
        "doctor": "Nephrologist",
        "tests": "KFT, urine routine, urine ACR, eGFR, renal ultrasound",
        "signals": [
            "Chronic kidney disease screening",
            "Filtration and waste-clearance pattern",
            "Electrolyte and urine-marker imbalance",
        ],
        "actions": [
            "Track creatinine, urea, eGFR, and urine protein.",
            "Control blood pressure and diabetes if present.",
            "Consult a doctor if swelling, anemia, or abnormal urine persists.",
        ],
    },
}


def apply_dashboard_theme():
    st.markdown(
        """
        <style>
        :root {
            --bg: #050b16;
            --panel: rgba(12, 22, 38, 0.72);
            --panel-strong: rgba(15, 26, 46, 0.94);
            --line: rgba(66, 190, 255, 0.18);
            --text: #f5f8ff;
            --muted: #8fb2d8;
            --cyan: #27e7c2;
            --blue: #4da3ff;
            --warning: #ffb02e;
            --danger: #ff5a67;
            --shadow-3d: 0 20px 40px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.08);
        }

        /* 3D Global Perspective */
        body {
            perspective: 1200px;
        }

        .stApp {
            background:
                radial-gradient(circle at 12% 18%, rgba(39, 231, 194, 0.09), transparent 28%),
                radial-gradient(circle at 88% 8%, rgba(77, 163, 255, 0.12), transparent 32%),
                linear-gradient(135deg, #050b16 0%, #081426 48%, #030611 100%);
            color: var(--text);
            font-family: 'Outfit', 'Inter', sans-serif;
        }

        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(5, 11, 22, 0.5);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(77, 163, 255, 0.25);
            border-radius: 99px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(39, 231, 194, 0.5);
        }

        .block-container {
            padding-top: 1.5rem;
            max-width: 1220px;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(6, 15, 28, 0.98), rgba(3, 8, 17, 0.98));
            border-right: 1px solid rgba(77, 163, 255, 0.15);
        }

        h1, h2, h3, label, p {
            letter-spacing: 0;
        }

        h1, h2, h3 {
            color: #ffffff;
            text-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }

        /* Interactive 3D Cards */
        .section-panel,
        .result-card,
        .input-console,
        .upload-panel,
        .disease-risk-card,
        .intel-card,
        .stat-card,
        .marker-card {
            background: var(--panel) !important;
            border: 1px solid rgba(77, 163, 255, 0.16) !important;
            border-radius: 16px !important;
            padding: 20px !important;
            margin: 14px 0 20px 0 !important;
            box-shadow: var(--shadow-3d) !important;
            backdrop-filter: blur(12px) !important;
            transform-style: preserve-3d;
            transition: transform 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), 
                        box-shadow 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), 
                        border-color 0.4s cubic-bezier(0.25, 0.8, 0.25, 1),
                        background 0.4s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        }

        /* Hover Tilt and Lighting Effects */
        .section-panel:hover,
        .input-console:hover,
        .upload-panel:hover {
            transform: translateY(-3px) translateZ(5px);
            border-color: rgba(39, 231, 194, 0.3) !important;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.15) !important;
        }

        .disease-risk-card:hover,
        .intel-card:hover,
        .stat-card:hover,
        .marker-card:hover {
            transform: perspective(800px) rotateX(3deg) rotateY(-3deg) translateZ(10px) translateY(-4px);
            border-color: rgba(39, 231, 194, 0.4) !important;
            background: rgba(15, 27, 48, 0.85) !important;
            box-shadow: 0 25px 45px rgba(0, 0, 0, 0.6), 
                        0 0 25px rgba(77, 163, 255, 0.18),
                        inset 0 1px 2px rgba(255, 255, 255, 0.2) !important;
        }

        div[data-testid="stMetric"],
        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            background: rgba(12, 22, 38, 0.56);
            border: 1px solid rgba(77, 163, 255, 0.16);
            border-radius: 12px;
            padding: 10px;
            box-shadow: inset 0 2px 8px rgba(0,0,0,0.3);
        }

        input, textarea, div[data-baseweb="select"] > div {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(77, 163, 255, 0.16) !important;
            border-radius: 10px !important;
            color: #ffffff !important;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2) !important;
            transition: all 0.25s ease !important;
        }

        input:focus, textarea:focus, div[data-baseweb="select"] > div:focus-within {
            border-color: var(--cyan) !important;
            box-shadow: 0 0 10px rgba(39, 231, 194, 0.25), inset 0 2px 4px rgba(0, 0, 0, 0.2) !important;
        }

        div[data-testid="stTextInput"],
        div[data-testid="stSelectbox"] {
            background: rgba(255,255,255,.02);
            border: 1px solid rgba(77,163,255,.1);
            border-radius: 12px;
            padding: 10px 12px 12px 12px;
            margin-bottom: 8px;
            transition: all .25s ease;
        }

        div[data-testid="stTextInput"]:hover,
        div[data-testid="stSelectbox"]:hover {
            border-color: rgba(39,231,194,.3);
            background: rgba(39,231,194,.03);
            transform: translateY(-1px) translateZ(2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        div[data-testid="stTextInput"] label,
        div[data-testid="stSelectbox"] label {
            color: #7fb9ef !important;
            font-weight: 800 !important;
            text-transform: uppercase;
            font-size: .78rem;
            letter-spacing: 0.5px;
        }

        /* 3D Action Buttons */
        .stButton > button,
        .stDownloadButton > button {
            background: linear-gradient(135deg, #27e7c2, #1eb4ff) !important;
            color: #04101e !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 12px !important;
            min-height: 3.1rem;
            font-size: 1.02rem;
            font-weight: 800;
            text-shadow: 0 1px 1px rgba(255, 255, 255, 0.2);
            box-shadow: 0 10px 25px rgba(39, 231, 194, 0.2), inset 0 2px 0 rgba(255,255,255,0.2) !important;
            transition: all .25s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            transform: translateY(-3px) scale(1.01) translateZ(10px) !important;
            filter: brightness(1.1);
            box-shadow: 0 15px 35px rgba(39, 231, 194, 0.35), 0 0 15px rgba(77, 163, 255, 0.2), inset 0 2px 0 rgba(255,255,255,0.3) !important;
        }

        .stButton > button:active,
        .stDownloadButton > button:active {
            transform: translateY(1px) !important;
            box-shadow: 0 5px 12px rgba(39, 231, 194, 0.2) !important;
        }

        /* Hero Banner & Interactive DNA Stage */
        .hero {
            position: relative;
            overflow: hidden;
            min-height: 270px;
            border-bottom: 1px solid rgba(77, 163, 255, 0.18);
            padding: 20px 0 26px 0;
            margin-bottom: 22px;
            transform-style: preserve-3d;
        }

        .hero-pill {
            display: inline-flex;
            align-items: center;
            gap: 9px;
            color: #69f4d8;
            background: rgba(39, 231, 194, 0.08);
            border: 1px solid rgba(39, 231, 194, 0.22);
            border-radius: 999px;
            padding: 6px 16px;
            font-weight: 800;
            margin-bottom: 16px;
            text-transform: uppercase;
            font-size: 0.78rem;
            letter-spacing: 1px;
            box-shadow: 0 0 15px rgba(39, 231, 194, 0.05);
        }

        .hero-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #27e7c2;
            box-shadow: 0 0 16px #27e7c2;
            animation: pulse 1.8s infinite ease-in-out;
        }

        .hero h1 {
            max-width: 620px;
            font-size: clamp(2.1rem, 5vw, 4.2rem);
            line-height: 1.05;
            margin: 0 0 12px 0;
            font-weight: 900;
        }

        .hero-copy {
            max-width: 720px;
            color: #9fc1e7;
            font-size: 1.08rem;
            line-height: 1.55;
        }

        .stat-row {
            display: flex;
            flex-wrap: wrap;
            gap: 14px;
            margin-top: 22px;
        }

        .stat-card {
            min-width: 142px;
            padding: 14px 18px !important;
            text-align: center;
            animation: riseIn .7s ease both;
        }

        .stat-card strong {
            display: block;
            color: #69f4d8;
            font-size: 1.45rem;
            line-height: 1.1;
            text-shadow: 0 0 10px rgba(105, 244, 216, 0.3);
        }

        .stat-card span {
            color: #8fb2d8;
            font-size: .86rem;
        }

        .dna-stage {
            position: absolute;
            right: 15px;
            top: 4px;
            width: 280px;
            height: 250px;
            opacity: .95;
            perspective: 900px;
            cursor: grab;
        }
        .dna-stage:active {
            cursor: grabbing;
        }

        .organ-visual-intro {
            background:
                radial-gradient(circle at 82% 35%, rgba(39,231,194,.08), transparent 35%),
                rgba(12, 22, 38, 0.62) !important;
        }

        .organ-copy h2 {
            margin: 0 0 8px 0;
        }

        .organ-copy p {
            color: #9fc1e7;
            line-height: 1.5;
            margin: 0;
        }

        .organ-svg {
            width: min(100%, 360px);
            height: 230px;
            overflow: visible;
            border-radius: 16px;
            border: 1px solid rgba(77,163,255,.14);
            background:
                radial-gradient(circle at 50% 50%, rgba(77,163,255,.12), transparent 46%),
                rgba(255,255,255,.03);
            padding: 14px;
            box-sizing: border-box;
            box-shadow: var(--shadow-3d);
            transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
        }

        .organ-svg:hover {
            transform: perspective(800px) rotateX(4deg) rotateY(-4deg) scale(1.02);
            border-color: var(--organ-tone);
            box-shadow: 0 20px 40px rgba(0,0,0,0.5), 0 0 25px rgba(77, 163, 255, 0.15);
        }

        .organ-main {
            fill: rgba(39,231,194,.06);
            stroke: var(--organ-tone);
            stroke-width: 3;
            filter: drop-shadow(0 0 12px var(--organ-tone));
            transform-origin: center;
            animation: organBreathe 3.4s ease-in-out infinite;
        }

        .organ-secondary {
            fill: none;
            stroke: rgba(143,178,216,.75);
            stroke-width: 2.2;
            stroke-linecap: round;
            stroke-dasharray: 8 10;
            animation: vesselFlow 3.2s linear infinite;
        }

        .organ-node {
            fill: var(--organ-tone);
            opacity: .95;
            filter: drop-shadow(0 0 8px var(--organ-tone));
            animation: baseGlow 2.2s ease-in-out infinite;
        }

        .organ-svg:hover .organ-main {
            animation-duration: 1.6s;
            filter: drop-shadow(0 0 22px var(--organ-tone));
            fill: rgba(39,231,194,.12);
        }

        .organ-heading {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 8px 0 16px 0;
        }

        .organ-heading .live-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #27e7c2;
            box-shadow: 0 0 18px #27e7c2;
            animation: pulse 2s infinite ease-in-out;
        }

        .marker-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(130px, 1fr));
            gap: 12px;
            margin: 12px 0 22px 0;
        }

        .marker-card {
            min-height: 94px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 7px;
            animation: riseIn .7s ease both;
        }

        .marker-icon {
            width: 42px;
            height: 42px;
            border-radius: 50%;
            border: 1px solid rgba(39,231,194,.4);
            position: relative;
            box-shadow: inset 0 0 18px rgba(39,231,194,.1);
            background: rgba(39,231,194,0.05);
        }

        .marker-icon:before,
        .marker-icon:after {
            content: "";
            position: absolute;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #27e7c2;
            box-shadow: 0 0 12px #27e7c2;
        }

        .marker-icon:before { left: 7px; top: 10px; }
        .marker-icon:after { right: 8px; bottom: 9px; background: #4da3ff; }

        .marker-card strong { color: #dcecff; }
        .marker-card span { color: #6fa9dd; font-size: .82rem; text-align: center; }

        .organ-card {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            background: rgba(255,255,255,.03);
            border: 1px solid rgba(77,163,255,.1);
            border-radius: 12px;
            padding: 12px 14px;
            margin-bottom: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: all 0.3s ease;
        }

        .organ-card:hover {
            transform: translateY(-2px) translateZ(4px);
            border-color: rgba(77, 163, 255, 0.3);
            background: rgba(255,255,255,.05);
        }

        .organ-card.active {
            border-color: rgba(39,231,194,.7) !important;
            background: rgba(39,231,194,.08) !important;
            box-shadow: 0 8px 24px rgba(39,231,194,.15) !important;
        }

        .organ-left {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .organ-dot {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            box-shadow: 0 0 14px currentColor;
        }

        .organ-name {
            color: white;
            font-weight: 850;
            line-height: 1.1;
        }

        .organ-sub {
            color: #6fa9dd;
            font-size: .78rem;
            max-width: 140px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .badge {
            color: #04101e;
            background: #27e7c2;
            border-radius: 999px;
            padding: 3px 8px;
            font-size: .72rem;
            font-weight: 900;
            box-shadow: 0 2px 8px rgba(39, 231, 194, 0.3);
        }

        .blood-viewer {
            height: 120px;
            position: relative;
            overflow: hidden;
            border-radius: 14px;
            border: 1px solid rgba(77,163,255,.14);
            background:
                radial-gradient(circle at 50% 50%, rgba(77,163,255,.10), transparent 42%),
                rgba(255,255,255,.03);
            margin-top: 10px;
            box-shadow: inset 0 4px 20px rgba(0,0,0,0.4);
            perspective: 500px;
        }

        .cell {
            position: absolute;
            border-radius: 50%;
            border: 1px solid rgba(255,90,103,.5);
            background: radial-gradient(circle at 35% 35%, rgba(255,90,103,.5), rgba(80,25,80,.4));
            box-shadow: 0 5px 15px rgba(255,90,103,.2);
            animation: drift 6s ease-in-out infinite alternate;
        }

        .cell.c1 { width: 24px; height: 16px; left: 14%; top: 28%; }
        .cell.c2 { width: 38px; height: 26px; left: 42%; top: 44%; animation-delay: .6s; }
        .cell.c3 { width: 22px; height: 14px; right: 18%; top: 30%; animation-delay: 1s; }
        .cell.c4 { width: 20px; height: 13px; left: 10%; bottom: 20%; animation-delay: 1.4s; }
        .cell.c5 { width: 26px; height: 16px; right: 10%; bottom: 18%; animation-delay: 1.8s; }

        .wbc {
            position: absolute;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            border: 1px solid #4da3ff;
            background: radial-gradient(circle at 30% 30%, #ffffff, #4da3ff);
            box-shadow: 0 0 12px rgba(77,163,255,.45);
            animation: floatOrb 4s ease-in-out infinite;
        }

        .wbc.w1 { left: 26%; top: 18%; }
        .wbc.w2 { right: 32%; bottom: 24%; animation-delay: .9s; }

        .projection-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }

        .projection-card {
            background: rgba(255,255,255,.03);
            border: 1px solid rgba(77,163,255,.12);
            border-radius: 12px;
            padding: 14px;
            box-shadow: var(--shadow-3d);
            transition: all 0.3s ease;
        }
        .projection-card:hover {
            transform: translateY(-2px) scale(1.02);
            border-color: rgba(39, 231, 194, 0.25);
        }

        .projection-card span {
            color: #8fb2d8;
            font-size: .82rem;
        }

        .projection-card strong {
            color: white;
            display: block;
            font-size: 1.35rem;
            margin-top: 4px;
            text-shadow: 0 0 8px rgba(255,255,255,0.15);
        }

        .input-console-top {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 18px;
        }

        .console-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 14px;
        }

        .console-chip {
            background: rgba(255,255,255,.04);
            border: 1px solid rgba(77,163,255,.14);
            border-radius: 999px;
            padding: 7px 14px;
            color: #cfe6ff;
            font-size: .84rem;
            font-weight: 750;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }

        .console-chip b {
            color: #69f4d8;
        }

        .extraction-list {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-top: 12px;
        }

        .extract-pill {
            background: rgba(255,255,255,.04);
            border: 1px solid rgba(77,163,255,.14);
            border-radius: 10px;
            padding: 9px 11px;
            color: #dcecff;
            font-size: .86rem;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }

        .extract-pill b {
            color: #69f4d8;
        }

        .intel-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-top: 14px;
        }

        .intel-card {
            min-height: 108px;
        }

        .intel-card span {
            color: #6fa9dd;
            display: block;
            font-size: .78rem;
            font-weight: 800;
            margin-bottom: 8px;
            text-transform: uppercase;
        }

        .intel-card strong {
            color: #ffffff;
            display: block;
            line-height: 1.32;
        }

        /* 3D Dial Risk assessment dashboard */
        .result-card {
            position: relative;
            overflow: hidden;
            background:
                linear-gradient(135deg, rgba(15, 26, 46, .96), rgba(6, 15, 28, .86)),
                radial-gradient(circle at 85% 18%, rgba(39,231,194,.15), transparent 35%) !important;
            border: 1px solid rgba(39,231,194,.22) !important;
        }

        .result-card:after {
            content: "";
            position: absolute;
            left: -45%;
            top: 0;
            width: 40%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,.08), transparent);
            animation: resultScan 3.5s ease-in-out infinite;
        }

        .result-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            position: relative;
            z-index: 1;
        }

        /* Concave Instrument Dial Look */
        .risk-ring {
            width: 132px;
            height: 132px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background: conic-gradient(var(--risk-color) var(--risk-angle), rgba(255,255,255,.04) 0);
            box-shadow: 0 0 0 6px rgba(0,0,0,0.3), 0 10px 25px rgba(0,0,0,0.6), 0 0 25px var(--risk-color);
            position: relative;
            transform: translateZ(20px);
        }

        .risk-ring-inner {
            width: 102px;
            height: 102px;
            border-radius: 50%;
            background: radial-gradient(circle at 35% 35%, #0c182d, #050b16);
            display: grid;
            place-items: center;
            text-align: center;
            box-shadow: inset 0 5px 15px rgba(0,0,0,0.85), inset 0 -2px 6px rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,.08);
        }

        .risk-ring-inner strong {
            color: white;
            font-size: 1.45rem;
            line-height: 1;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }

        .risk-ring-inner span {
            color: #8fb2d8;
            font-size: .78rem;
        }

        .result-title {
            flex: 1;
        }

        .result-title span {
            color: #8fb2d8;
            font-size: .85rem;
            font-weight: 800;
            text-transform: uppercase;
        }

        .result-title h2 {
            margin: 5px 0 8px 0;
            font-size: 2rem;
        }

        .result-title p {
            margin: 0;
            color: #9fc1e7;
            line-height: 1.5;
        }

        .result-actions {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-top: 16px;
            position: relative;
            z-index: 1;
        }

        .mini-action {
            background: rgba(255,255,255,.03);
            border: 1px solid rgba(77,163,255,.14);
            border-radius: 12px;
            padding: 12px;
            color: #dcecff;
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
            transition: all 0.3s ease;
        }
        .mini-action:hover {
            transform: translateY(-2px);
            border-color: rgba(77, 163, 255, 0.25);
            background: rgba(255,255,255,.05);
        }

        .mini-action span {
            display: block;
            color: #6fa9dd;
            font-size: .76rem;
            font-weight: 800;
            margin-bottom: 5px;
            text-transform: uppercase;
        }

        .disease-risk-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 14px;
            margin-top: 14px;
        }

        .disease-risk-card h3 {
            margin: 0 0 8px 0;
            font-size: 1.05rem;
        }

        .disease-risk-card p {
            color: #9fc1e7;
            line-height: 1.45;
            margin: 0 0 12px 0;
            font-size: .92rem;
        }

        .risk-meter {
            height: 8px;
            border-radius: 999px;
            background: rgba(255,255,255,.08);
            overflow: hidden;
            margin: 7px 0 10px 0;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.5);
        }

        .risk-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #27e7c2, #ffb02e, #ff5a67);
            box-shadow: 0 0 8px rgba(39, 231, 194, 0.5);
        }

        .risk-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .risk-mini {
            background: rgba(255,255,255,.03);
            border: 1px solid rgba(77,163,255,.12);
            border-radius: 10px;
            padding: 9px;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }

        .risk-mini span {
            display: block;
            color: #6fa9dd;
            font-size: .72rem;
            font-weight: 850;
            text-transform: uppercase;
        }

        .risk-mini strong {
            color: #ffffff;
            font-size: 1.05rem;
        }

        /* Upgraded animations */
        @keyframes pulse {
            0%, 100% { transform: scale(.88); opacity: .65; }
            50% { transform: scale(1.12); opacity: 1; }
        }

        @keyframes floatOrb {
            0%, 100% { transform: translate(0, 0) translateZ(0); }
            50% { transform: translate(6px, -8px) translateZ(10px); }
        }

        @keyframes baseGlow {
            0%, 100% { opacity: .65; transform: scale(.94); }
            50% { opacity: 1; transform: scale(1.06); }
        }

        @keyframes organBreathe {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.025); }
        }

        @keyframes vesselFlow {
            from { stroke-dashoffset: 0; }
            to { stroke-dashoffset: -36; }
        }

        @keyframes riseIn {
            from { transform: translateY(12px) translateZ(-10px); opacity: 0; }
            to { transform: translateY(0) translateZ(0); opacity: 1; }
        }

        @keyframes drift {
            from { transform: translate(-4px, 3px) rotate(0deg); }
            to { transform: translate(7px, -6px) rotate(12deg); }
        }

        @keyframes resultScan {
            0% { left: -45%; }
            60%, 100% { left: 120%; }
        }

        @media (max-width: 900px) {
            .dna-stage { opacity: .3; right: -40px; }
            .marker-grid, .projection-grid, .intel-grid, .result-actions, .extraction-list, .disease-risk-grid { grid-template-columns: 1fr 1fr; }
            .result-top { align-items: flex-start; }
        }

        @media (max-width: 620px) {
            .marker-grid, .projection-grid, .intel-grid, .result-actions, .extraction-list, .disease-risk-grid { grid-template-columns: 1fr; }
            .hero { min-height: 330px; }
            .result-top { flex-direction: column; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-pill"><span class="hero-dot"></span> AI-powered blood analysis</div>
            <h1>Organ-level disease risk intelligence</h1>
            <div class="hero-copy">
                Input your blood report values to get instant risk scores, biomarker comparison,
                downloadable reports, and estimated future health projections.
            </div>
            <div class="stat-row">
                <div class="stat-card"><strong>4</strong><span>Organs monitored</span></div>
                <div class="stat-card"><strong>12+</strong><span>Disease signals</span></div>
                <div class="stat-card"><strong>PDF</strong><span>Medical report</span></div>
            </div>
            <div class="dna-stage">
                <canvas id="dnaCanvas" width="280" height="250" style="display:block; width:280px; height:250px;"></canvas>
            </div>
        </div>
        <script>
        (function() {
            const canvas = document.getElementById('dnaCanvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            
            const width = 280;
            const height = 250;
            
            let angle = 0;
            let scrollRotation = 0;
            let targetScrollRotation = 0;
            let mouseX = 0;
            let mouseY = 0;
            let hoverActive = false;
            
            // Listen to page scroll to rotate DNA helix
            window.addEventListener('scroll', () => {
                targetScrollRotation = window.scrollY * 0.0055;
            }, { passive: true });
            
            canvas.addEventListener('mousemove', (e) => {
                const rect = canvas.getBoundingClientRect();
                mouseX = (e.clientX - rect.left - width / 2) / (width / 2);
                mouseY = (e.clientY - rect.top - height / 2) / (height / 2);
                hoverActive = true;
            });
            
            canvas.addEventListener('mouseleave', () => {
                mouseX = 0;
                mouseY = 0;
                hoverActive = false;
            });
            
            const numNodes = 14;
            const radius = 60;
            const baseSpeed = 0.012;
            
            function draw() {
                ctx.clearRect(0, 0, width, height);
                
                // Interpolate scroll position for inertia
                scrollRotation += (targetScrollRotation - scrollRotation) * 0.1;
                
                const speed = baseSpeed + (hoverActive ? Math.abs(mouseX) * 0.025 : 0);
                angle += speed;
                
                const totalAngle = angle + scrollRotation + (hoverActive ? mouseX * 0.4 : 0);
                const tiltX = hoverActive ? mouseY * 0.25 : 0.05;
                
                let nodes = [];
                for (let i = 0; i < numNodes; i++) {
                    const progress = i / (numNodes - 1);
                    const y = progress * (height - 60) + 30;
                    
                    const phase = progress * Math.PI * 2.3;
                    
                    // Strand A
                    const thetaA = totalAngle + phase;
                    let xA = Math.cos(thetaA) * radius;
                    let zA = Math.sin(thetaA) * radius;
                    let yA = y + zA * tiltX;
                    
                    // Strand B (180 degrees out of phase)
                    const thetaB = totalAngle + phase + Math.PI;
                    let xB = Math.cos(thetaB) * radius;
                    let zB = Math.sin(thetaB) * radius;
                    let yB = y + zB * tiltX;
                    
                    nodes.push({
                        xA: xA + width / 2, yA: yA, zA: zA,
                        xB: xB + width / 2, yB: yB, zB: zB
                    });
                }
                
                // Draw connecting hydrogen bonds with depth alpha
                for (let i = 0; i < numNodes; i++) {
                    const node = nodes[i];
                    const avgZ = (node.zA + node.zB) / 2;
                    const opacity = 0.12 + 0.48 * ((avgZ + radius) / (2 * radius));
                    
                    ctx.beginPath();
                    ctx.moveTo(node.xA, node.yA);
                    ctx.lineTo(node.xB, node.yB);
                    
                    const grad = ctx.createLinearGradient(node.xA, node.yA, node.xB, node.yB);
                    grad.addColorStop(0, `rgba(39, 231, 194, ${opacity})`);
                    grad.addColorStop(1, `rgba(77, 163, 255, ${opacity})`);
                    
                    ctx.strokeStyle = grad;
                    ctx.lineWidth = 1.8;
                    ctx.setLineDash([3, 4]);
                    ctx.stroke();
                    ctx.setLineDash([]);
                }
                
                // Gather spheres for depth-sorting
                let spheres = [];
                for (let i = 0; i < numNodes; i++) {
                    const node = nodes[i];
                    spheres.push({
                        x: node.xA, y: node.yA, z: node.zA,
                        color: '#27e7c2', glow: 'rgba(39, 231, 194, 0.32)'
                    });
                    spheres.push({
                        x: node.xB, y: node.yB, z: node.zB,
                        color: '#4da3ff', glow: 'rgba(77, 163, 255, 0.32)'
                    });
                }
                
                // Sort spheres from back to front
                spheres.sort((a, b) => a.z - b.z);
                
                // Draw spheres
                spheres.forEach(s => {
                    const scale = 0.65 + 0.35 * ((s.z + radius) / (2 * radius));
                    const size = 6.2 * scale;
                    
                    if (s.z > -15) {
                        ctx.beginPath();
                        ctx.arc(s.x, s.y, size * 2.3, 0, Math.PI * 2);
                        ctx.fillStyle = s.glow;
                        ctx.fill();
                    }
                    
                    ctx.beginPath();
                    ctx.arc(s.x, s.y, size, 0, Math.PI * 2);
                    
                    const grad = ctx.createRadialGradient(
                        s.x - size * 0.35, s.y - size * 0.35, size * 0.1,
                        s.x, s.y, size
                    );
                    grad.addColorStop(0, '#ffffff');
                    grad.addColorStop(0.3, s.color);
                    grad.addColorStop(1, '#050b16');
                    
                    ctx.fillStyle = grad;
                    ctx.fill();
                });
                
                requestAnimationFrame(draw);
            }
            
            draw();
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(selected):
    cards = []
    for disease, data in ORGAN_DATA.items():
        active = "active" if disease == selected else ""
        cards.append(
            f"""
            <div class="organ-card {active}">
                <div class="organ-left">
                    <div class="organ-dot" style="background:{data['tone']}; color:{data['tone']};"></div>
                    <div>
                        <div class="organ-name">{data['organ']}</div>
                        <div class="organ-sub">{data['subtitle']}</div>
                    </div>
                </div>
                <div class="badge" style="background:{data['tone']};">{data['status']}</div>
            </div>
            """
        )

    st.sidebar.markdown("### ORGAN SYSTEMS")
    st.sidebar.markdown("".join(cards), unsafe_allow_html=True)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### BLOOD CELL VIEWER")
    st.sidebar.markdown(
        """
        <div class="blood-viewer">
            <div class="cell c1"></div>
            <div class="cell c2"></div>
            <div class="cell c3"></div>
            <div class="cell c4"></div>
            <div class="cell c5"></div>
            <div class="wbc w1"></div>
            <div class="wbc w2"></div>
        </div>
        <div style="color:#6fa9dd;font-size:.78rem;text-align:center;margin-top:6px;">RBC | WBC | Platelet view</div>
        """,
        unsafe_allow_html=True,
    )


def render_marker_tiles(disease):
    tiles = []
    for title, caption in ORGAN_DATA[disease]["markers"]:
        tiles.append(
            f'<div class="marker-card"><div class="marker-icon"></div><strong>{title}</strong><span>{caption}</span></div>'
        )
    st.markdown(f'<div class="marker-grid">{"".join(tiles)}</div>', unsafe_allow_html=True)


def render_context_panel(disease):
    data = ORGAN_DATA[disease]
    st.markdown(
        f"""
        <div class="section-panel">
            <div class="organ-heading">
                <span class="live-dot" style="background:{data['tone']}; box-shadow:0 0 18px {data['tone']};"></span>
                <h2 style="margin:0;">{data['organ']} - blood markers</h2>
            </div>
            <p style="color:#9fc1e7;margin-top:0;">{data['summary']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def organ_svg_markup(disease):
    tone = ORGAN_DATA[disease]["tone"]
    if disease == "Diabetes":
        return f"""
        <svg class="organ-svg" viewBox="0 0 360 240" style="--organ-tone:{tone};" role="img" aria-label="Interactive pancreas organ drawing">
            <defs>
                <linearGradient id="pancGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="{tone}" stop-opacity="0.25"/>
                    <stop offset="100%" stop-color="{tone}" stop-opacity="0.05"/>
                </linearGradient>
            </defs>
            <style>
                @keyframes isletPulse {{
                    0%, 100% {{ transform: scale(0.85); opacity: 0.5; }}
                    50% {{ transform: scale(1.2); opacity: 1; filter: drop-shadow(0 0 8px {tone}); }}
                }}
                @keyframes particleFloat {{
                    0% {{ transform: translate(0, 0); opacity: 0; }}
                    20% {{ opacity: 0.8; }}
                    80% {{ opacity: 0.8; }}
                    100% {{ transform: translate(40px, -50px); opacity: 0; }}
                }}
                .islet {{
                    animation: isletPulse 3s ease-in-out infinite;
                    transform-origin: center;
                }}
                .panc-particle {{
                    animation: particleFloat 4s ease-in-out infinite;
                    fill: {tone};
                }}
            </style>
            <!-- Pancreas Outer Shape -->
            <path class="organ-main" fill="url(#pancGrad)" d="M63 130 C80 76, 132 72, 164 103 C186 124, 217 104, 247 84 C288 58, 333 80, 327 125 C321 169, 275 179, 235 158 C204 142, 185 145, 164 166 C132 199, 76 184, 63 130 Z"/>
            
            <!-- Capillaries -->
            <path class="organ-secondary" d="M96 135 C135 103, 180 128, 222 108 C254 94, 282 95, 306 116"/>
            <path class="organ-secondary" d="M118 158 C145 143, 175 149, 204 137"/>
            
            <!-- Islets of Langerhans (Pulsing clusters) -->
            <circle class="organ-node islet" cx="118" cy="111" r="7" style="animation-delay: 0s;"/>
            <circle class="organ-node islet" cx="150" cy="125" r="5" style="animation-delay: 0.5s;"/>
            <circle class="organ-node islet" cx="203" cy="132" r="8" style="animation-delay: 1s;"/>
            <circle class="organ-node islet" cx="245" cy="120" r="6" style="animation-delay: 1.5s;"/>
            <circle class="organ-node islet" cx="287" cy="116" r="7" style="animation-delay: 2s;"/>
            
            <!-- Floating insulin/glucose particles -->
            <circle class="panc-particle" cx="130" cy="150" r="3" style="animation-delay: 0.2s;"/>
            <circle class="panc-particle" cx="180" cy="160" r="2.5" style="animation-delay: 1.2s;"/>
            <circle class="panc-particle" cx="220" cy="145" r="3.5" style="animation-delay: 2.2s;"/>
            <circle class="panc-particle" cx="260" cy="130" r="2" style="animation-delay: 0.8s;"/>
            
            <text x="100" y="215" fill="#8fb2d8" font-size="12" font-weight="800" letter-spacing="1">PANCREAS / METABOLIC</text>
        </svg>
        """
    if disease == "Heart":
        return f"""
        <svg class="organ-svg" viewBox="0 0 360 240" style="--organ-tone:{tone};" role="img" aria-label="Interactive heart organ drawing">
            <defs>
                <linearGradient id="heartGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="{tone}" stop-opacity="0.25"/>
                    <stop offset="100%" stop-color="{tone}" stop-opacity="0.05"/>
                </linearGradient>
            </defs>
            <style>
                @keyframes heartbeat {{
                    0%, 100% {{ transform: scale(1); }}
                    15% {{ transform: scale(1.06); }}
                    30% {{ transform: scale(0.98); }}
                    45% {{ transform: scale(1.12); }}
                    70% {{ transform: scale(1); }}
                }}
                .heart-main {{
                    animation: heartbeat 1.5s ease-in-out infinite;
                    transform-origin: 180px 120px;
                }}
                .capillary-pulse {{
                    stroke-dasharray: 6 12;
                    animation: vesselFlow 2s linear infinite;
                }}
            </style>
            <!-- Aorta & Vena Cava back structures -->
            <path d="M160 50 C155 20, 195 15, 200 40 L200 70" fill="none" stroke="{tone}" stroke-width="7" stroke-linecap="round" opacity="0.6"/>
            <path d="M130 25 L130 65" fill="none" stroke="#4da3ff" stroke-width="8" stroke-linecap="round" opacity="0.6"/>
            
            <!-- Heart silhouette (Beating) -->
            <path class="organ-main heart-main" fill="url(#heartGrad)" d="M180 205 C72 136, 55 65, 106 43 C137 30, 165 49, 180 76 C196 49, 224 30, 255 43 C306 65, 288 136, 180 205 Z"/>
            
            <!-- Heart Coronary Arteries (Dashed Flowing) -->
            <path class="organ-secondary capillary-pulse" d="M180 76 C169 111, 173 144, 180 205" stroke="{tone}"/>
            <path class="organ-secondary capillary-pulse" d="M130 78 C150 94, 166 112, 181 135" stroke="#4da3ff"/>
            <path class="organ-secondary capillary-pulse" d="M203 116 C225 100, 251 86, 260 70" stroke="{tone}"/>
            
            <!-- Node indicators -->
            <circle class="organ-node" cx="142" cy="91" r="6"/>
            <circle class="organ-node" cx="218" cy="91" r="6"/>
            <circle class="organ-node" cx="180" cy="141" r="7"/>
            
            <text x="110" y="222" fill="#8fb2d8" font-size="12" font-weight="800" letter-spacing="1">HEART / CARDIOVASCULAR</text>
        </svg>
        """
    if disease == "Liver":
        return f"""
        <svg class="organ-svg" viewBox="0 0 360 240" style="--organ-tone:{tone};" role="img" aria-label="Interactive liver organ drawing">
            <defs>
                <linearGradient id="liverGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="{tone}" stop-opacity="0.25"/>
                    <stop offset="100%" stop-color="{tone}" stop-opacity="0.05"/>
                </linearGradient>
            </defs>
            <style>
                @keyframes detoxBubble {{
                    0% {{ transform: translate(0, 0); opacity: 0; }}
                    20% {{ opacity: 0.7; }}
                    80% {{ opacity: 0.7; }}
                    100% {{ transform: translate(60px, -20px); opacity: 0; }}
                }}
                .bubble {{
                    animation: detoxBubble 5s ease-in-out infinite;
                    fill: {tone};
                }}
            </style>
            <!-- Main Liver Shape -->
            <path class="organ-main" fill="url(#liverGrad)" d="M45 111 C68 57, 142 43, 224 55 C294 66, 333 98, 313 145 C291 198, 201 186, 154 161 C116 141, 71 163, 50 140 C41 131, 39 122, 45 111 Z"/>
            
            <!-- Hepatic portal vein flows -->
            <path class="organ-secondary" d="M142 60 C154 100, 153 133, 136 166"/>
            <path class="organ-secondary" d="M162 112 C201 101, 244 111, 286 137"/>
            <path class="organ-secondary" d="M95 125 C123 109, 157 109, 184 128"/>
            
            <!-- Detox/Enzyme bubbles -->
            <circle class="bubble" cx="100" cy="110" r="2.5" style="animation-delay: 0.5s;"/>
            <circle class="bubble" cx="130" cy="90" r="3.5" style="animation-delay: 1.8s;"/>
            <circle class="bubble" cx="180" cy="120" r="2" style="animation-delay: 3s;"/>
            <circle class="bubble" cx="220" cy="100" r="3" style="animation-delay: 0.2s;"/>
            <circle class="bubble" cx="250" cy="130" r="2.5" style="animation-delay: 1.5s;"/>
            
            <!-- Functional nodes -->
            <circle class="organ-node" cx="142" cy="103" r="7"/>
            <circle class="organ-node" cx="210" cy="115" r="6"/>
            <circle class="organ-node" cx="276" cy="139" r="6"/>
            
            <text x="120" y="215" fill="#8fb2d8" font-size="12" font-weight="800" letter-spacing="1">LIVER / HEPATOBILIARY</text>
        </svg>
        """
    return f"""
    <svg class="organ-svg" viewBox="0 0 360 240" style="--organ-tone:{tone};" role="img" aria-label="Interactive kidney organ drawing">
        <defs>
            <linearGradient id="kidneyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="{tone}" stop-opacity="0.25"/>
                <stop offset="100%" stop-color="{tone}" stop-opacity="0.05"/>
            </linearGradient>
        </defs>
        <style>
            @keyframes excretionFlow {{
                0% {{ stroke-dashoffset: 0; }}
                100% {{ stroke-dashoffset: -32; }}
            }}
            .excretion-path {{
                stroke-dasharray: 5 8;
                animation: excretionFlow 2.5s linear infinite;
            }}
        </style>
        <!-- Left Kidney -->
        <path class="organ-main" fill="url(#kidneyGrad)" d="M127 41 C77 51, 54 111, 76 158 C91 190, 124 202, 153 184 C175 170, 170 138, 154 122 C139 107, 157 82, 156 63 C155 47, 144 38, 127 41 Z"/>
        
        <!-- Right Kidney -->
        <path class="organ-main" fill="url(#kidneyGrad)" d="M233 41 C283 51, 306 111, 284 158 C269 190, 236 202, 207 184 C185 170, 190 138, 206 122 C221 107, 203 82, 204 63 C205 47, 216 38, 233 41 Z"/>
        
        <!-- Renal Vessels / Ureters -->
        <path class="organ-secondary excretion-path" d="M180 54 C177 94, 177 128, 180 172" stroke="#4da3ff"/>
        <path class="organ-secondary excretion-path" d="M156 125 C172 128, 178 138, 180 172" stroke="{tone}"/>
        <path class="organ-secondary excretion-path" d="M204 125 C188 128, 182 138, 180 172" stroke="{tone}"/>
        
        <!-- Functional nodes -->
        <circle class="organ-node" cx="126" cy="102" r="6"/>
        <circle class="organ-node" cx="234" cy="102" r="6"/>
        <circle class="organ-node" cx="180" cy="172" r="7"/>
        
        <text x="120" y="215" fill="#8fb2d8" font-size="12" font-weight="800" letter-spacing="1">KIDNEYS / RENAL SYSTEM</text>
    </svg>
    """

def render_organ_visual(disease):
    data = ORGAN_DATA[disease]
    col1, col2 = st.columns([1.05, 0.95])
    with col1:
        st.markdown(
            f"""
            <div class="organ-visual-intro organ-copy">
                <h2>{data['organ']} interactive map</h2>
                <p>
                    This visual highlights the organ system connected to the selected blood-marker panel.
                    Hover the drawing to speed up the motion and emphasize the active biological pathways.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(organ_svg_markup(disease), unsafe_allow_html=True)


def render_hero():
    components.html(
        """
        <div class="hero-wrap">
            <div class="hero-content">
                <div class="hero-pill"><span></span> AI-powered blood analysis</div>
                <h1>Organ-level disease risk intelligence</h1>
                <p>
                    Input your blood report values to get instant risk scores, biomarker comparison,
                    downloadable reports, and estimated future health projections.
                </p>
                <div class="stat-row">
                    <div class="stat-card"><strong>4</strong><small>Organs monitored</small></div>
                    <div class="stat-card"><strong>12+</strong><small>Disease signals</small></div>
                    <div class="stat-card"><strong>PDF</strong><small>Medical report</small></div>
                </div>
            </div>
            <canvas id="dnaCanvas" width="360" height="300" aria-label="Interactive DNA double helix"></canvas>
        </div>
        <style>
            html, body {
                margin: 0;
                background: transparent;
                color: #f5f8ff;
                font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                overflow: hidden;
            }
            .hero-wrap {
                min-height: 292px;
                position: relative;
                overflow: hidden;
                border: 1px solid rgba(77, 163, 255, 0.16);
                border-radius: 18px;
                background:
                    radial-gradient(circle at 82% 24%, rgba(39, 231, 194, 0.14), transparent 32%),
                    radial-gradient(circle at 16% 12%, rgba(77, 163, 255, 0.12), transparent 34%),
                    linear-gradient(135deg, rgba(7, 15, 29, 0.96), rgba(5, 11, 22, 0.92));
                box-shadow: 0 24px 50px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.08);
                transform-style: preserve-3d;
            }
            .hero-content {
                position: relative;
                z-index: 2;
                max-width: 720px;
                padding: 28px 32px;
            }
            .hero-pill {
                display: inline-flex;
                align-items: center;
                gap: 9px;
                color: #69f4d8;
                background: rgba(39, 231, 194, 0.08);
                border: 1px solid rgba(39, 231, 194, 0.22);
                border-radius: 999px;
                padding: 7px 16px;
                font-weight: 850;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 1px;
            }
            .hero-pill span {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #27e7c2;
                box-shadow: 0 0 16px #27e7c2;
                animation: pulse 1.8s infinite ease-in-out;
            }
            h1 {
                max-width: 620px;
                font-size: clamp(34px, 5vw, 58px);
                line-height: 1.04;
                margin: 18px 0 12px 0;
                font-weight: 900;
                text-shadow: 0 8px 22px rgba(0,0,0,.38);
            }
            p {
                max-width: 660px;
                color: #a7c8ee;
                font-size: 17px;
                line-height: 1.55;
                margin: 0;
            }
            .stat-row {
                display: flex;
                flex-wrap: wrap;
                gap: 14px;
                margin-top: 22px;
            }
            .stat-card {
                min-width: 128px;
                padding: 14px 17px;
                border: 1px solid rgba(77, 163, 255, .18);
                border-radius: 14px;
                background: rgba(15, 26, 46, .72);
                box-shadow: 0 16px 30px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.08);
                transition: transform .25s ease, border-color .25s ease;
            }
            .stat-card:hover {
                transform: perspective(700px) rotateX(4deg) rotateY(-5deg) translateY(-3px);
                border-color: rgba(39, 231, 194, .42);
            }
            .stat-card strong {
                display: block;
                color: #69f4d8;
                font-size: 24px;
                line-height: 1;
            }
            .stat-card small {
                color: #8fb2d8;
                font-size: 13px;
            }
            #dnaCanvas {
                position: absolute;
                right: 10px;
                top: -2px;
                width: 360px;
                height: 300px;
                z-index: 1;
                cursor: grab;
            }
            @keyframes pulse {
                0%, 100% { transform: scale(.86); opacity: .65; }
                50% { transform: scale(1.15); opacity: 1; }
            }
            @media (max-width: 820px) {
                #dnaCanvas { opacity: .32; right: -90px; }
                .hero-content { padding: 24px; }
            }
        </style>
        <script>
            const canvas = document.getElementById("dnaCanvas");
            const ctx = canvas.getContext("2d");
            const width = canvas.width;
            const height = canvas.height;
            let angle = 0;
            let scrollRotation = 0;
            let targetScrollRotation = 0;
            let mouseX = 0;
            let mouseY = 0;
            let hover = false;

            function updateScrollRotation() {
                try {
                    const parentScroll = window.parent && window.parent.scrollY ? window.parent.scrollY : 0;
                    targetScrollRotation = parentScroll * 0.006;
                } catch (error) {
                    targetScrollRotation = window.scrollY * 0.006;
                }
            }
            window.addEventListener("scroll", updateScrollRotation, { passive: true });
            try {
                window.parent.addEventListener("scroll", updateScrollRotation, { passive: true });
            } catch (error) {}

            canvas.addEventListener("mousemove", (event) => {
                const rect = canvas.getBoundingClientRect();
                mouseX = (event.clientX - rect.left - rect.width / 2) / (rect.width / 2);
                mouseY = (event.clientY - rect.top - rect.height / 2) / (rect.height / 2);
                hover = true;
            });
            canvas.addEventListener("mouseleave", () => {
                mouseX = 0;
                mouseY = 0;
                hover = false;
            });

            function sphere(x, y, z, color) {
                const depth = (z + 62) / 124;
                const radius = 4.5 + depth * 4.2;
                const glow = color === "#27e7c2" ? "rgba(39,231,194,.32)" : "rgba(77,163,255,.32)";
                if (z > -18) {
                    ctx.beginPath();
                    ctx.arc(x, y, radius * 2.2, 0, Math.PI * 2);
                    ctx.fillStyle = glow;
                    ctx.fill();
                }
                const gradient = ctx.createRadialGradient(x - radius * .3, y - radius * .3, 1, x, y, radius);
                gradient.addColorStop(0, "#ffffff");
                gradient.addColorStop(.28, color);
                gradient.addColorStop(1, "#06101f");
                ctx.beginPath();
                ctx.arc(x, y, radius, 0, Math.PI * 2);
                ctx.fillStyle = gradient;
                ctx.fill();
            }

            function draw() {
                ctx.clearRect(0, 0, width, height);
                updateScrollRotation();
                scrollRotation += (targetScrollRotation - scrollRotation) * 0.08;
                angle += 0.014 + (hover ? Math.abs(mouseX) * 0.02 : 0);

                const nodes = [];
                const count = 16;
                const strandRadius = 70;
                const totalAngle = angle + scrollRotation + mouseX * .35;
                const tilt = .06 + mouseY * .22;

                for (let i = 0; i < count; i++) {
                    const progress = i / (count - 1);
                    const y = 28 + progress * (height - 56);
                    const phase = progress * Math.PI * 2.6;
                    const a = totalAngle + phase;
                    const b = a + Math.PI;
                    const zA = Math.sin(a) * strandRadius;
                    const zB = Math.sin(b) * strandRadius;
                    nodes.push({
                        ax: width / 2 + Math.cos(a) * strandRadius,
                        ay: y + zA * tilt,
                        az: zA,
                        bx: width / 2 + Math.cos(b) * strandRadius,
                        by: y + zB * tilt,
                        bz: zB,
                    });
                }

                nodes.forEach((node) => {
                    const opacity = .18 + .36 * (((node.az + node.bz) / 2 + strandRadius) / (2 * strandRadius));
                    const gradient = ctx.createLinearGradient(node.ax, node.ay, node.bx, node.by);
                    gradient.addColorStop(0, `rgba(39,231,194,${opacity})`);
                    gradient.addColorStop(1, `rgba(77,163,255,${opacity})`);
                    ctx.beginPath();
                    ctx.moveTo(node.ax, node.ay);
                    ctx.lineTo(node.bx, node.by);
                    ctx.strokeStyle = gradient;
                    ctx.lineWidth = 2;
                    ctx.setLineDash([4, 5]);
                    ctx.stroke();
                    ctx.setLineDash([]);
                });

                const spheres = [];
                nodes.forEach((node) => {
                    spheres.push({ x: node.ax, y: node.ay, z: node.az, color: "#27e7c2" });
                    spheres.push({ x: node.bx, y: node.by, z: node.bz, color: "#4da3ff" });
                });
                spheres.sort((left, right) => left.z - right.z);
                spheres.forEach((item) => sphere(item.x, item.y, item.z, item.color));
                requestAnimationFrame(draw);
            }
            draw();
        </script>
        """,
        height=315,
        scrolling=False,
    )


def render_organ_visual(disease):
    data = ORGAN_DATA[disease]
    col1, col2 = st.columns([1.05, 0.95])
    with col1:
        st.markdown(
            f"""
            <div class="organ-visual-intro organ-copy">
                <h2>{data['organ']} interactive map</h2>
                <p>
                    This visual highlights the organ system connected to the selected blood-marker panel.
                    Hover the drawing to speed up the motion and emphasize the active biological pathways.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        components.html(
            f"""
            <html>
                <body style="margin:0;background:transparent;display:flex;justify-content:center;align-items:center;">
                    {organ_svg_markup(disease)}
                </body>
            </html>
            """,
            height=270,
            scrolling=False,
        )


def render_disease_intelligence(disease):
    data = ORGAN_DATA[disease]
    st.markdown(
        f"""
        <div class="section-panel">
            <h2 style="margin-top:0;">Disease Intelligence</h2>
            <p style="color:#9fc1e7;margin-bottom:0;">
                This module studies biomarker patterns linked with {data['subtitle'].lower()}.
                It is designed for early screening and report discussion, not final diagnosis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    for index, signal in enumerate(data["signals"], start=1):
        with cols[index - 1]:
            st.markdown(
                f"""
                <div class="intel-card">
                    <span>Signal {index}</span>
                    <strong>{signal}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_result_dashboard(disease, risk_level, risk_percent, advice):
    data = ORGAN_DATA[disease]
    risk_color = "#27e7c2"
    if risk_level == "HIGH RISK":
        risk_color = "#ff5a67"
    elif risk_level == "MODERATE RISK":
        risk_color = "#ffb02e"

    action_1, action_2, action_3 = data["actions"]
    risk_angle = max(0, min(100, risk_percent)) * 3.6

    st.markdown(
        f"""
        <div class="result-card" style="--risk-color:{risk_color}; --risk-angle:{risk_angle}deg;">
            <div class="result-top">
                <div class="result-title">
                    <span>{data['organ']} risk assessment</span>
                    <h2>{risk_level}</h2>
                    <p>{advice}</p>
                </div>
                <div class="risk-ring">
                    <div class="risk-ring-inner">
                        <div>
                            <strong>{risk_percent:.2f}%</strong>
                            <span>Risk score</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="result-actions">
                <div class="mini-action"><span>Next step</span>{action_1}</div>
                <div class="mini-action"><span>Watch point</span>{action_2}</div>
                <div class="mini-action"><span>Care path</span>{action_3}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_input_console(disease):
    data = ORGAN_DATA[disease]
    marker_names = ", ".join(marker[0] for marker in data["markers"])
    st.markdown(
        f"""
        <div class="input-console">
            <div class="input-console-top">
                <div>
                    <h2>Blood Report Input Console</h2>
                    <p>
                        Enter the available values from your report. The model will analyze the
                        {data['organ'].lower()} marker pattern and compare numeric values with common reference ranges.
                    </p>
                </div>
            </div>
            <div class="console-chip-row">
                <div class="console-chip"><b>Model:</b> {disease} risk</div>
                <div class="console-chip"><b>Key markers:</b> {marker_names}</div>
                <div class="console-chip"><b>Output:</b> risk score, graph, table, PDF</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def clean_report_text(text):
    lines = []
    for line in (text or "").replace("\r", "\n").split("\n"):
        cleaned = re.sub(r"\s+", " ", line).strip()
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


def extract_pdf_text(uploaded_file):
    if uploaded_file is None:
        return "", ""
    file_bytes = uploaded_file.getvalue()
    report_id = hashlib.md5(file_bytes).hexdigest()[:10]

    if PdfReader is None:
        st.error("PDF reading is not available yet. Add pypdf to requirements.txt, then redeploy.")
        return "", report_id

    try:
        uploaded_file.seek(0)
        reader = PdfReader(uploaded_file)
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return clean_report_text(" ".join(pages)), report_id
    except Exception as exc:
        st.error(f"Could not read this PDF report. Try another PDF or enter values manually. Details: {exc}")
        return "", report_id


def preprocess_report_image(image):
    image = ImageOps.exif_transpose(image)
    image = image.convert("L")
    width, height = image.size
    scale = max(1, int(1600 / max(1, width)))
    if scale > 1:
        image = image.resize((width * scale, height * scale))
    image = ImageOps.autocontrast(image)
    image = image.filter(ImageFilter.SHARPEN)
    return image


def extract_image_text(uploaded_file):
    if uploaded_file is None:
        return "", ""
    file_bytes = uploaded_file.getvalue()
    report_id = hashlib.md5(file_bytes).hexdigest()[:10]

    if Image is None or pytesseract is None:
        st.error("Image OCR is not available yet. Add pytesseract and Pillow to requirements.txt, plus tesseract-ocr to packages.txt.")
        return "", report_id

    try:
        image = Image.open(BytesIO(file_bytes))
        processed = preprocess_report_image(image)
        text = pytesseract.image_to_string(processed, config="--psm 6")
        return clean_report_text(text), report_id
    except Exception as exc:
        st.error(f"Could not read this image report. Try a clearer image or enter values manually. Details: {exc}")
        return "", report_id


def extract_report_text(uploaded_file):
    if uploaded_file is None:
        return "", ""

    name = (uploaded_file.name or "").lower()
    mime = (uploaded_file.type or "").lower()

    if name.endswith(".pdf") or "pdf" in mime:
        return extract_pdf_text(uploaded_file)

    if name.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif")) or mime.startswith("image/"):
        return extract_image_text(uploaded_file)

    st.error("Unsupported report format. Please upload PDF, PNG, JPG, JPEG, WEBP, BMP, or TIFF.")
    return "", ""


def numeric_candidates(line):
    return re.findall(r"(?<![A-Za-z])([0-9]+(?:\.[0-9]+)?)(?![A-Za-z])", line)


def line_has_label(line, label):
    escaped = re.escape(label)
    if label and label[0].isalnum() and label[-1].isalnum():
        return re.search(rf"(?<![A-Za-z]){escaped}(?![A-Za-z])", line, flags=re.IGNORECASE)
    return re.search(escaped, line, flags=re.IGNORECASE)


def looks_like_prose(line):
    prose_words = [
        "patient",
        "patients",
        "recommended",
        "screening",
        "explanation",
        "reflects",
        "concentration",
        "measurement",
        "accepted",
        "risk",
        "diabetes mellitus",
        "normal urinary",
        "defined as",
        "indicative",
        "specimens",
    ]
    lowered = line.lower()
    return len(line) > 150 or any(word in lowered for word in prose_words)


def looks_like_range_only(line):
    numbers = numeric_candidates(line)
    has_range = re.search(r"[0-9]+(?:\.[0-9]+)?\s*[-\u2013]\s*[0-9]+(?:\.[0-9]+)?", line)
    return bool(has_range and len(numbers) <= 2 and not looks_like_result_context(line))


def choose_best_number(line, label):
    after_label = re.split(re.escape(label), line, maxsplit=1, flags=re.IGNORECASE)
    search_area = after_label[1] if len(after_label) > 1 else line

    explicit = re.search(
        r"(?:result|value|observed|reading)\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)",
        search_area,
        flags=re.IGNORECASE,
    )
    if explicit:
        return explicit.group(1)

    numbers = numeric_candidates(search_area)
    if not numbers:
        numbers = numeric_candidates(line)

    if not numbers:
        return None

    return numbers[-1]


def looks_like_result_context(text):
    keywords = [
        "method",
        "calculated",
        "colorimetric",
        "enzymatic",
        "oxidase",
        "peroxidase",
        "impedance",
        "chromatography",
        "turbidimetric",
        "bromocresol",
        "direct",
        "ifcc",
        "ise",
        "cube",
        "derived",
        "amidohydrolase",
        "urease",
        "azobilirubin",
    ]
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def find_marker_value(text, labels):
    detail = find_marker_detail(text, labels)
    return detail["value"] if detail else None


def find_marker_detail(text, labels):
    lines = text.splitlines() if "\n" in text else [text]
    for label in labels:
        for index, line in enumerate(lines):
            if line_has_label(line, label):
                for result_line in lines[index : min(len(lines), index + 6)]:
                    if line_has_label(result_line, label) and looks_like_result_context(result_line):
                        numbers = numeric_candidates(result_line)
                        if numbers:
                            return {
                                "value": numbers[-1],
                                "label": label,
                                "source": result_line[:160],
                                "confidence": "High",
                            }

                split_result_labels = ["hba1c", "glycated hemoglobin", "glycosylated hemoglobin"]
                if label.lower() in split_result_labels:
                    for result_line in lines[index + 1 : min(len(lines), index + 10)]:
                        if looks_like_result_context(result_line):
                            numbers = numeric_candidates(result_line)
                            if numbers:
                                return {
                                    "value": numbers[-1],
                                    "label": label,
                                    "source": f"{line[:70]} ... {result_line[:90]}",
                                    "confidence": "Medium",
                                }

                if (looks_like_result_context(line) or not looks_like_prose(line)) and not looks_like_range_only(line):
                    value = choose_best_number(line, label)
                    if value is not None:
                        confidence = "High" if looks_like_result_context(line) else "Medium"
                        return {
                            "value": value,
                            "label": label,
                            "source": line[:160],
                            "confidence": confidence,
                        }

    return None


def find_age(text):
    patterns = [
        r"\b(?:male|female|m|f)\s*/\s*([0-9]{1,3})\s*(?:years|yrs|yr|y)?\b",
        r"\b([0-9]{1,3})\s*(?:years|yrs|yr|y)\s*[-/]\s*(?:male|female|m|f)\b",
        r"(?:age|patient age)\s*[:\-]?\s*([0-9]{1,3})\s*(?:years|yrs|yr|y)?",
        r"(?:age\s*/\s*sex|age\s*/\s*gender)\s*[:\-]?\s*([0-9]{1,3})",
        r"([0-9]{1,3})\s*(?:years|yrs|yr)\s*/\s*(?:male|female|m|f)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def find_gender_label(text):
    patterns = [
        r"\b(male|female|m|f)\s*/\s*[0-9]{1,3}\s*(?:years|yrs|yr|y)?\b",
        r"\b[0-9]{1,3}\s*(?:years|yrs|yr|y)\s*[-/]\s*(male|female|m|f)\b",
        r"(?:gender|sex)\s*[:\-]?\s*(male|female|m|f)\b",
        r"(?:age\s*/\s*sex|age\s*/\s*gender)\s*[:\-]?\s*[0-9]{1,3}\s*/?\s*(male|female|m|f)\b",
        r"[0-9]{1,3}\s*(?:years|yrs|yr)?\s*/\s*(male|female|m|f)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = match.group(1).lower()
            return "Male" if value in ["male", "m"] else "Female"
    return None


REPORT_MARKERS = {
    "Diabetes": {
        "pregnancies": ["Pregnancies"],
        "glucose": ["Fasting Blood Sugar", "FBS", "Blood Sugar Fasting", "Glucose Fasting", "Plasma Glucose", "Blood Glucose", "Glucose Level", "Glucose"],
        "bp": ["Blood Pressure", "B.P.", "BP"],
        "skin": ["Skin Thickness", "Triceps Skin Fold"],
        "insulin": ["Insulin", "Fasting Insulin"],
        "bmi": ["BMI", "Body Mass Index"],
        "dpf": ["Diabetes Pedigree Function", "Pedigree Function"],
        "age": ["Age", "Patient Age"],
        "hba1c": ["HbA1c", "HBA1C", "Glycated Hemoglobin", "Glycosylated Hemoglobin"],
    },
    "Heart": {
        "age": ["Age", "Patient Age"],
        "trestbps": ["Resting Blood Pressure", "Blood Pressure", "B.P.", "BP"],
        "chol": ["Total Cholesterol", "Serum Cholesterol", "Cholesterol"],
        "thalach": ["Max Heart Rate", "Maximum Heart Rate", "Heart Rate", "Pulse Rate"],
        "oldpeak": ["ST Depression", "Oldpeak"],
        "fbs_value": ["Fasting Blood Sugar", "FBS", "Blood Sugar Fasting"],
    },
    "Liver": {
        "age": ["Age", "Patient Age"],
        "total_bili": ["Total Bilirubin", "Bilirubin Total", "Bilirubin - Total"],
        "direct_bili": ["Direct Bilirubin", "Conjugated Bilirubin", "Bilirubin Direct", "Bilirubin - Direct"],
        "alk_phos": ["Alkaline Phosphotase", "Alkaline Phosphatase", "Alk Phos", "ALP"],
        "alt": ["Alamine Aminotransferase", "Alanine Aminotransferase", "ALT", "SGPT"],
        "ast": ["Aspartate Aminotransferase", "AST", "SGOT"],
        "total_prot": ["Total Proteins", "Total Protein", "Protein Total"],
        "albumin": ["Serum Albumin", "Albumin"],
        "ag_ratio": ["Albumin Globulin Ratio", "A/G Ratio", "Albumin/Globulin Ratio", "AG Ratio"],
    },
    "Kidney": {
        "age": ["Age", "Patient Age"],
        "bp": ["Blood Pressure", "B.P.", "BP"],
        "sg": ["Specific Gravity", "Urine Specific Gravity"],
        "al": ["Urine Albumin", "Albumin (Urine)", "Albumin Urine"],
        "su": ["Urine Sugar", "Sugar (Urine)", "Sugar Urine"],
        "bgr": ["Blood Glucose Random", "Random Blood Sugar", "RBS", "Glucose Random"],
        "bu": ["Blood Urea Nitrogen", "Blood Urea", "Urea", "BUN"],
        "sc": ["Serum Creatinine", "Creatinine"],
        "sod": ["Serum Sodium", "Sodium", "Na+"],
        "pot": ["Serum Potassium", "Potassium", "K+"],
        "hemo": ["Hemoglobin", "Haemoglobin", "Hb"],
        "pcv": ["Packed Cell Volume", "PCV", "Hematocrit", "HCT"],
        "wc": ["White Blood Cell Count", "WBC Count", "WBC", "Total Leukocyte Count", "TLC"],
        "rc": ["Red Blood Cell Count", "RBC Count", "RBC"],
    },
}


FIELD_DISPLAY_NAMES = {
    "age": "Age",
    "gender_label": "Gender",
    "gender_binary": "Gender code",
    "pregnancies": "Pregnancies",
    "glucose": "Fasting glucose",
    "hba1c": "HbA1c",
    "bp": "Blood pressure",
    "skin": "Skin thickness",
    "insulin": "Insulin",
    "bmi": "BMI",
    "dpf": "Diabetes pedigree function",
    "trestbps": "Resting blood pressure",
    "chol": "Total cholesterol",
    "thalach": "Max heart rate",
    "oldpeak": "ST depression",
    "fbs_value": "Fasting blood sugar",
    "fbs": "FBS > 120 flag",
    "total_bili": "Total bilirubin",
    "direct_bili": "Direct bilirubin",
    "alk_phos": "Alkaline phosphatase",
    "alt": "ALT / SGPT",
    "ast": "AST / SGOT",
    "total_prot": "Total protein",
    "albumin": "Albumin",
    "ag_ratio": "A/G ratio",
    "sg": "Specific gravity",
    "al": "Urine albumin",
    "su": "Urine sugar",
    "bgr": "Random blood glucose",
    "bu": "Blood urea / BUN",
    "sc": "Serum creatinine",
    "sod": "Sodium",
    "pot": "Potassium",
    "hemo": "Hemoglobin",
    "pcv": "Packed cell volume",
    "wc": "WBC count",
    "rc": "RBC count",
}


FIELD_TO_MODEL_PARAM = {
    "Diabetes": {
        "glucose": "Glucose",
        "bp": "BloodPressure",
        "skin": "SkinThickness",
        "insulin": "Insulin",
        "bmi": "BMI",
        "dpf": "DiabetesPedigreeFunction",
        "age": "Age",
        "pregnancies": "Pregnancies",
    },
    "Heart": {
        "age": "age",
        "trestbps": "trestbps",
        "chol": "chol",
        "thalach": "thalach",
        "oldpeak": "oldpeak",
    },
    "Liver": {
        "age": "Age",
        "total_bili": "Total_Bilirubin",
        "direct_bili": "Direct_Bilirubin",
        "alk_phos": "Alkaline_Phosphotase",
        "alt": "Alamine_Aminotransferase",
        "ast": "Aspartate_Aminotransferase",
        "total_prot": "Total_Protiens",
        "albumin": "Albumin",
        "ag_ratio": "Albumin_and_Globulin_Ratio",
    },
    "Kidney": {
        "age": "age",
        "bp": "bp",
        "sg": "sg",
        "al": "al",
        "su": "su",
        "bgr": "bgr",
        "bu": "bu",
        "sc": "sc",
        "sod": "sod",
        "pot": "pot",
        "hemo": "hemo",
        "pcv": "pcv",
        "wc": "wc",
        "rc": "rc",
    },
}


def parse_report_values(text, disease):
    details = parse_report_details(text, disease)
    return {field: detail["value"] for field, detail in details.items()}


def parse_report_details(text, disease):
    values = {}
    if not text:
        return values
    age = find_age(text)
    if age is not None:
        values["age"] = {
            "value": age,
            "label": "Age/Sex",
            "source": "Patient information header",
            "confidence": "High",
        }

    gender_label = find_gender_label(text)
    if gender_label is not None:
        values["gender_label"] = {
            "value": gender_label,
            "label": "Sex/Gender",
            "source": "Patient information header",
            "confidence": "High",
        }
        values["gender_binary"] = {
            "value": 1 if gender_label == "Male" else 0,
            "label": "Sex/Gender",
            "source": "Patient information header",
            "confidence": "High",
        }

    for field, labels in REPORT_MARKERS[disease].items():
        if field == "age" and "age" in values:
            continue
        detail = find_marker_detail(text, labels)
        if detail is not None:
            values[field] = detail

    if disease == "Heart" and "fbs_value" in values:
        values["fbs"] = {
            "value": 1 if get_float(values["fbs_value"]["value"]) > 120 else 0,
            "label": "Derived from FBS",
            "source": f"FBS value {values['fbs_value']['value']}",
            "confidence": values["fbs_value"]["confidence"],
        }
    return values


def render_report_upload(disease):
    st.markdown(
        """
        <div class="upload-panel">
            <h2>Upload Blood Report</h2>
            <p>
                Upload a hospital blood report PDF or image to auto-detect available values.
                You can still edit every field before running prediction.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader(
        "Upload hospital blood report PDF or image",
        type=["pdf", "png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif"],
        key=f"{disease}_report_upload",
        help="PDFs use text extraction. Images use OCR, so clear, straight, high-resolution photos work best.",
    )

    report_text, report_id = extract_report_text(uploaded_file)
    module_details = {}
    if report_text:
        module_details = {
            module: parse_report_details(report_text, module)
            for module in ["Diabetes", "Heart", "Liver", "Kidney"]
        }
    extracted_details = module_details.get(disease, {})
    extracted_values = {field: detail["value"] for field, detail in extracted_details.items()}

    if uploaded_file is not None:
        any_values = any(details for details in module_details.values())
        if any_values:
            st.success("The report was read successfully. Review the detected modules and extracted values below.")
            render_module_detection(module_details)
            if extracted_values:
                render_extraction_review(disease, extracted_details)
            else:
                st.warning(
                    f"The report contains readable values, but I did not find strong matches for the {disease} module. "
                    "Try another organ module from the sidebar or enter values manually."
                )
        else:
            st.warning(
                "I could not confidently find matching values in this report. "
                "This can happen with blurry images, scanned reports, or unusual lab formats. Please enter values manually."
            )
            with st.expander("Show extracted text preview"):
                st.write(report_text[:2500] if report_text else "No readable text found.")

    return extracted_values, report_id


def render_module_detection(module_details):
    rows = []
    for module, details in module_details.items():
        model_fields = set(FIELD_TO_MODEL_PARAM[module].keys())
        found_model_fields = model_fields.intersection(details.keys())
        coverage = round((len(found_model_fields) / max(1, len(model_fields))) * 100)
        status = "Ready" if coverage >= 45 else "Partial" if coverage > 0 else "Missing"
        rows.append(
            {
                "Module": module,
                "Extracted values": len(details),
                "Model fields found": f"{len(found_model_fields)} / {len(model_fields)}",
                "Coverage": f"{coverage}%",
                "Status": status,
            }
        )
    st.subheader("Auto-detected disease modules")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_extraction_review(disease, extracted_details):
    rows = []
    model_fields = set(FIELD_TO_MODEL_PARAM[disease].keys())
    for field, detail in extracted_details.items():
        rows.append(
            {
                "Marker": FIELD_DISPLAY_NAMES.get(field, field),
                "Value": detail["value"],
                "Source label": detail["label"],
                "Confidence": detail["confidence"],
                "Used in model": "Yes" if field in model_fields or field in ["gender_binary"] else "Reference only",
            }
        )
    if rows:
        st.subheader("Extracted-value review")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def classify_marker(model_param, raw_value):
    if model_param not in normal_ranges:
        return "Reference", "No reference range in app"
    try:
        value = float(raw_value)
    except Exception:
        return "Reference", "Non-numeric value"
    low, high = normal_ranges[model_param]
    if value < low:
        return "Below normal", f"{value:g} is below {low:g}-{high:g}"
    if value > high:
        return "Above normal", f"{value:g} is above {low:g}-{high:g}"
    return "Normal", f"{value:g} is within {low:g}-{high:g}"


def render_report_summary(disease, report_values):
    if not report_values:
        return

    mapped = FIELD_TO_MODEL_PARAM[disease]
    found = []
    abnormal = []
    normal = []

    for field, model_param in mapped.items():
        if field not in report_values:
            continue
        status, note = classify_marker(model_param, report_values[field])
        found.append(FIELD_DISPLAY_NAMES.get(field, field))
        if status in ["Above normal", "Below normal"]:
            abnormal.append(f"{FIELD_DISPLAY_NAMES.get(field, field)}: {note}")
        elif status == "Normal":
            normal.append(FIELD_DISPLAY_NAMES.get(field, field))

    if not found:
        return

    st.subheader("AI Report Summary")
    if abnormal:
        st.warning("Key attention points: " + " | ".join(abnormal[:4]))
    else:
        st.success("The extracted model markers are mostly within the app's reference ranges.")

    st.info(
        f"Detected {len(found)} usable {disease} markers from the uploaded PDF. "
        "Review and correct the auto-filled fields before running prediction."
    )


def autofill(report_values, field, fallback):
    return str(report_values.get(field, fallback))


def selected_gender_index(report_values, options):
    gender = report_values.get("gender_label")
    if gender in options:
        return options.index(gender)
    return 0


def selected_binary_index(report_values, field, fallback=0):
    try:
        value = int(report_values.get(field, fallback))
        return 1 if value == 1 else 0
    except Exception:
        return fallback


def field_key(disease, field, report_id):
    return f"{disease}_{field}_{report_id or 'manual'}"


MODEL_LOAD_ERRORS = {}


@st.cache_resource
def load_models():
    models = {}
    MODEL_LOAD_ERRORS.clear()
    model_dir = "./saved_models"
    for disease in ["diabetes", "heart", "liver", "kidney"]:
        path = f"{model_dir}/{disease}_model.pkl"
        if os.path.exists(path):
            model_name = disease.capitalize()
            try:
                with open(path, "rb") as f:
                    model_package = pickle.load(f)

                if not isinstance(model_package, dict):
                    raise ValueError("The saved file is not a model package dictionary.")
                if "model" not in model_package or "features" not in model_package:
                    raise ValueError("The saved model package must include 'model' and 'features'.")

                models[model_name] = model_package
            except Exception as exc:
                MODEL_LOAD_ERRORS[model_name] = f"{type(exc).__name__}: {exc}"
    return models


models = load_models()


def get_float(val, default=0.0):
    try:
        return float(val)
    except Exception:
        return default


def get_int(val, default=0):
    try:
        return int(val)
    except Exception:
        return default


def predict_disease(disease, input_values):
    info = models[disease]
    model = info["model"]
    features = info["features"]
    input_df = pd.DataFrame([input_values])[features]
    probability = model.predict_proba(input_df)[0]
    risk_percent = round(float(probability[1]) * 100, 2)

    if risk_percent >= 70:
        return "HIGH RISK", risk_percent, "Please consult a physician immediately.", "red"
    if risk_percent >= 40:
        return "MODERATE RISK", risk_percent, "Monitor your health and consult a doctor soon.", "orange"
    return "LOW RISK", risk_percent, "You appear healthy. Maintain a good lifestyle!", "green"


normal_ranges = {
    "Glucose": (70, 100),
    "BloodPressure": (60, 80),
    "BMI": (18.5, 24.9),
    "Insulin": (16, 166),
    "SkinThickness": (10, 30),
    "Age": (0, 120),
    "age": (0, 120),
    "Pregnancies": (0, 10),
    "DiabetesPedigreeFunction": (0, 1),
    "chol": (125, 200),
    "trestbps": (90, 120),
    "thalach": (60, 100),
    "oldpeak": (0, 2),
    "Total_Bilirubin": (0.2, 1.2),
    "Direct_Bilirubin": (0, 0.3),
    "Alkaline_Phosphotase": (44, 147),
    "Alamine_Aminotransferase": (7, 56),
    "Aspartate_Aminotransferase": (10, 40),
    "Total_Protiens": (6, 8.3),
    "Albumin": (3.5, 5),
    "Albumin_and_Globulin_Ratio": (1, 2.5),
    "bp": (60, 80),
    "sg": (1.005, 1.030),
    "al": (0, 0),
    "su": (0, 0),
    "bgr": (70, 120),
    "bu": (7, 25),
    "sc": (0.6, 1.2),
    "sod": (135, 145),
    "pot": (3.5, 5),
    "hemo": (12, 17),
    "pcv": (36, 50),
    "wc": (4500, 11000),
    "rc": (4.5, 5.5),
}


def plot_risk_chart(input_values, disease):
    numeric_inputs = {
        k: v
        for k, v in input_values.items()
        if isinstance(v, (int, float)) and k in normal_ranges
    }
    params = list(numeric_inputs.keys())
    values = list(numeric_inputs.values())
    normal_high = []
    colors = []

    for param, val in zip(params, values):
        low, high = normal_ranges[param]
        normal_high.append(high)
        colors.append("#ff5a67" if val < low or val > high else "#27e7c2")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Normal Range Max",
            x=params,
            y=normal_high,
            marker_color="rgba(77, 163, 255, 0.22)",
            showlegend=True,
        )
    )
    fig.add_trace(
        go.Bar(
            name="Your Value",
            x=params,
            y=values,
            marker_color=colors,
            showlegend=True,
        )
    )
    fig.update_layout(
        title=f"{disease} - Your Values vs Normal Range",
        barmode="overlay",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=430,
        margin=dict(l=20, r=20, t=70, b=30),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.06)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)")
    return fig


def generate_pdf(disease, input_values, risk_level, risk_percent, advice, rows):
    pdf = FPDF()
    pdf.add_page()
    data = ORGAN_DATA[disease]

    if risk_level == "HIGH RISK":
        r, g, b = 231, 76, 60
        risk_note = "Priority review recommended"
    elif risk_level == "MODERATE RISK":
        r, g, b = 243, 156, 18
        risk_note = "Monitor closely and follow up"
    else:
        r, g, b = 39, 174, 96
        risk_note = "Maintain healthy habits"

    pdf.set_fill_color(5, 12, 24)
    pdf.rect(0, 0, 210, 42, "F")
    pdf.set_fill_color(39, 231, 194)
    pdf.rect(0, 40, 210, 2, "F")
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 13, "", ln=True)
    pdf.cell(0, 13, "  BioPredict AI", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(190, 210, 230)
    pdf.cell(0, 7, "  Organ-level AI screening report", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}", ln=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(5, 12, 24)
    pdf.cell(0, 9, f"{data['organ']} Risk Assessment", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 100, 115)
    pdf.multi_cell(0, 6, data["summary"])
    pdf.ln(2)

    pdf.set_fill_color(r, g, b)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(62, 14, f" Risk Level: {risk_level}", border=0, fill=True)
    pdf.cell(48, 14, f" Score: {risk_percent:.2f}%", border=0, fill=True)
    pdf.cell(80, 14, f" {risk_note}", border=0, fill=True, ln=True)
    pdf.ln(5)

    pdf.set_fill_color(245, 248, 252)
    pdf.set_draw_color(220, 228, 238)
    pdf.rect(10, pdf.get_y(), 190, 32, "DF")
    box_y = pdf.get_y()
    pdf.set_xy(14, box_y + 4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(5, 12, 24)
    pdf.cell(0, 7, "Clinical Guidance", ln=True)
    pdf.set_x(14)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(70, 82, 96)
    pdf.multi_cell(180, 5.5, advice)
    pdf.set_x(14)
    pdf.multi_cell(180, 5.5, f"Suggested specialist: {data['doctor']}. Useful follow-up tests: {data['tests']}.")
    pdf.set_y(box_y + 37)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(5, 12, 24)
    pdf.cell(0, 8, "Disease Signals Reviewed", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(70, 82, 96)
    for signal in data["signals"]:
        pdf.cell(5)
        pdf.cell(0, 6, f"- {signal}", ln=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(5, 12, 24)
    pdf.cell(58, 9, "Parameter", border=1, fill=True)
    pdf.cell(38, 9, "Your Value", border=1, fill=True)
    pdf.cell(46, 9, "Normal Range", border=1, fill=True)
    pdf.cell(48, 9, "Status", border=1, fill=True, ln=True)

    pdf.set_font("Helvetica", "", 10)
    fill = False
    for row in rows:
        status = row["Status"].replace("Above: ", "").replace("Normal: ", "").replace("Below: ", "")
        if "Above" in status:
            pdf.set_text_color(231, 76, 60)
        elif "Below" in status:
            pdf.set_text_color(52, 152, 219)
        else:
            pdf.set_text_color(39, 174, 96)
        if fill:
            pdf.set_fill_color(248, 250, 253)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.cell(58, 8, str(row["Parameter"]), border=1, fill=True)
        pdf.cell(38, 8, str(round(row["Your Value"], 2)), border=1, fill=True)
        pdf.cell(46, 8, str(row["Normal Range"]), border=1, fill=True)
        pdf.cell(48, 8, status, border=1, fill=True, ln=True)
        fill = not fill

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(5, 12, 24)
    pdf.cell(0, 8, "Recommended Next Steps", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(70, 82, 96)
    for action in data["actions"]:
        pdf.set_x(15)
        pdf.multi_cell(180, 6, f"- {action}")

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(
        0,
        6,
        "DISCLAIMER: This report is generated by an AI screening tool and is NOT a substitute for professional medical advice. Always consult a qualified physician for proper diagnosis and treatment.",
    )

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name


def build_analysis_rows(input_values):
    numeric_inputs = {
        k: v
        for k, v in input_values.items()
        if isinstance(v, (int, float)) and k in normal_ranges
    }
    rows = []
    for param, val in numeric_inputs.items():
        low, high = normal_ranges[param]
        if val < low:
            status = "Below: Below Normal"
        elif val > high:
            status = "Above: Above Normal"
        else:
            status = "Normal: Normal"
        rows.append(
            {
                "Parameter": param,
                "Your Value": val,
                "Normal Range": f"{low} - {high}",
                "Status": status,
            }
        )
    return rows


def render_projection(disease, risk_percent):
    one_year = min(99.0, risk_percent * 1.08 + 2)
    five_year = min(99.0, risk_percent * 1.22 + 6)
    ten_year = min(99.0, risk_percent * 1.38 + 10)
    data = ORGAN_DATA[disease]

    st.markdown(
        f"""
        <div class="section-panel">
            <h2 style="margin-top:0;">Future Risk Projection</h2>
            <p style="color:#9fc1e7;">
                These are estimated screening projections based on the current model score.
                They are not a medical diagnosis or a guaranteed future outcome.
            </p>
            <div class="projection-grid">
                <div class="projection-card"><span>1-year watch score</span><strong>{one_year:.2f}%</strong></div>
                <div class="projection-card"><span>5-year watch score</span><strong>{five_year:.2f}%</strong></div>
                <div class="projection-card"><span>10-year watch score</span><strong>{ten_year:.2f}%</strong></div>
            </div>
            <p style="color:#9fc1e7;margin-bottom:0;margin-top:14px;">
                Suggested specialist: <b style="color:white;">{data['doctor']}</b><br>
                Useful follow-up tests: <b style="color:white;">{data['tests']}</b>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_clinical_explanation(disease, rows, risk_level, risk_percent):
    data = ORGAN_DATA[disease]
    abnormal_rows = [
        row for row in rows
        if "Above" in row["Status"] or "Below" in row["Status"]
    ]
    if abnormal_rows:
        marker_text = ", ".join(
            f"{row['Parameter']} ({row['Your Value']})" for row in abnormal_rows[:5]
        )
    else:
        marker_text = "No major extracted numeric markers are outside the app's reference ranges."

    if risk_level == "HIGH RISK":
        tone = "This result should be treated as a priority screening alert."
    elif risk_level == "MODERATE RISK":
        tone = "This result suggests a watch zone where follow-up and trend monitoring are useful."
    else:
        tone = "This result is reassuring, but it should still be interpreted with symptoms and medical history."

    st.markdown(
        f"""
        <div class="section-panel">
            <h2 style="margin-top:0;">Clinical Explanation</h2>
            <p style="color:#9fc1e7;">
                The {data['organ'].lower()} model produced a <b style="color:white;">{risk_percent:.2f}%</b>
                screening score, categorized as <b style="color:white;">{risk_level}</b>.
                {tone}
            </p>
            <p style="color:#9fc1e7;">
                Main markers to review: <b style="color:white;">{marker_text}</b>
            </p>
            <p style="color:#9fc1e7;margin-bottom:0;">
                Suggested follow-up: discuss the report with a <b style="color:white;">{data['doctor']}</b>
                and consider: <b style="color:white;">{data['tests']}</b>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def safe_float_value(value):
    try:
        return float(value)
    except Exception:
        return None


def merged_biomarkers(input_values, report_values):
    values = {}
    for key, value in input_values.items():
        values[key] = value
    for key, value in report_values.items():
        values[key] = value
    return values


def value_from(values, *keys):
    for key in keys:
        if key in values:
            numeric = safe_float_value(values[key])
            if numeric is not None:
                return numeric
    return None


def clamp_score(value):
    return round(max(0, min(99, value)), 1)


def high_marker_score(value, normal_high, warning_high=None):
    if value is None:
        return 18
    if warning_high is None:
        warning_high = normal_high * 1.25
    if value <= normal_high:
        return 18
    if value >= warning_high:
        return 82
    return 35 + ((value - normal_high) / max(1, warning_high - normal_high)) * 42


def low_marker_score(value, normal_low, warning_low=None):
    if value is None:
        return 18
    if warning_low is None:
        warning_low = normal_low * 0.75
    if value >= normal_low:
        return 18
    if value <= warning_low:
        return 82
    return 35 + ((normal_low - value) / max(1, normal_low - warning_low)) * 42


def combine_scores(*scores):
    usable = [score for score in scores if score is not None]
    if not usable:
        return 20
    return sum(usable) / len(usable)


def future_watch_score(current, *risk_modifiers):
    modifier = sum([m for m in risk_modifiers if m is not None])
    return clamp_score(current + modifier)


def disease_pattern_cards(disease, input_values, report_values, model_risk):
    values = merged_biomarkers(input_values, report_values)
    age = value_from(values, "Age", "age")
    bmi = value_from(values, "BMI", "bmi")
    glucose = value_from(values, "Glucose", "glucose", "bgr")
    hba1c = value_from(values, "hba1c")
    insulin = value_from(values, "Insulin", "insulin")
    bp = value_from(values, "BloodPressure", "bp", "trestbps")
    chol = value_from(values, "chol")
    fbs_flag = value_from(values, "fbs")
    oldpeak = value_from(values, "oldpeak")
    thalach = value_from(values, "thalach")
    total_bili = value_from(values, "Total_Bilirubin", "total_bili")
    direct_bili = value_from(values, "Direct_Bilirubin", "direct_bili")
    alt = value_from(values, "Alamine_Aminotransferase", "alt")
    ast = value_from(values, "Aspartate_Aminotransferase", "ast")
    albumin = value_from(values, "Albumin", "albumin")
    total_prot = value_from(values, "Total_Protiens", "total_prot")
    creatinine = value_from(values, "sc")
    urea = value_from(values, "bu")
    sodium = value_from(values, "sod")
    potassium = value_from(values, "pot")
    hemo = value_from(values, "hemo")
    wbc = value_from(values, "wc")
    rbc = value_from(values, "rc")
    pcv = value_from(values, "pcv")

    cards = []

    if disease == "Diabetes":
        type2 = combine_scores(
            high_marker_score(glucose, 125, 180),
            high_marker_score(hba1c, 6.4, 8.5),
            high_marker_score(bmi, 29.9, 40),
            model_risk,
        )
        prediabetes = combine_scores(
            65 if glucose is not None and 100 <= glucose <= 125 else high_marker_score(glucose, 99, 140),
            65 if hba1c is not None and 5.7 <= hba1c <= 6.4 else high_marker_score(hba1c, 5.6, 7),
            high_marker_score(bmi, 24.9, 32),
        )
        resistance = combine_scores(
            high_marker_score(insulin, 166, 250),
            high_marker_score(bmi, 27, 36),
            high_marker_score(glucose, 110, 160),
        )
        metabolic = combine_scores(
            high_marker_score(bmi, 24.9, 35),
            high_marker_score(glucose, 110, 160),
            high_marker_score(age, 45, 70),
        )
        cards = [
            ("Type 2 Diabetes", "Fasting glucose, HbA1c, BMI, age and model probability.", type2),
            ("Prediabetes Pattern", "Borderline glucose or HbA1c with metabolic markers.", prediabetes),
            ("Insulin Resistance", "Insulin, glucose and BMI pattern suggesting reduced insulin sensitivity.", resistance),
            ("Metabolic Syndrome Watch", "Combined glucose, BMI and age-related metabolic stress.", metabolic),
        ]
    elif disease == "Heart":
        cad = combine_scores(
            high_marker_score(chol, 200, 260),
            high_marker_score(oldpeak, 2, 4),
            low_marker_score(thalach, 100, 70),
            model_risk,
        )
        hypertension = combine_scores(
            high_marker_score(bp, 120, 160),
            high_marker_score(age, 50, 75),
        )
        dyslipidemia = combine_scores(
            high_marker_score(chol, 200, 260),
        )
        diabetic_cardiac = combine_scores(
            70 if fbs_flag == 1 else 20,
            high_marker_score(glucose, 125, 180),
            high_marker_score(chol, 200, 260),
        )
        cards = [
            ("Coronary Artery Disease Pattern", "Cholesterol, ST depression, heart-rate response and ML score.", cad),
            ("Hypertension-Linked Risk", "Resting blood pressure and age-related cardiovascular load.", hypertension),
            ("Dyslipidemia Pattern", "Total cholesterol pattern linked with plaque and vessel risk.", dyslipidemia),
            ("Diabetic Cardiac Risk", "Fasting sugar plus cholesterol markers that raise heart risk.", diabetic_cardiac),
        ]
    elif disease == "Liver":
        fatty = combine_scores(
            high_marker_score(alt, 56, 100),
            high_marker_score(ast, 40, 90),
            high_marker_score(glucose, 125, 180),
            high_marker_score(bmi, 27, 36),
            model_risk,
        )
        inflammation = combine_scores(
            high_marker_score(alt, 56, 120),
            high_marker_score(ast, 40, 100),
        )
        bilirubin = combine_scores(
            high_marker_score(total_bili, 1.2, 3),
            high_marker_score(direct_bili, 0.3, 1),
        )
        synthetic = combine_scores(
            low_marker_score(albumin, 3.5, 2.5),
            low_marker_score(total_prot, 6, 4.5),
        )
        cards = [
            ("Fatty Liver / Metabolic Liver Pattern", "ALT, AST, glucose/BMI and liver model score.", fatty),
            ("Liver Inflammation Pattern", "SGPT/ALT and SGOT/AST enzyme elevation.", inflammation),
            ("Bilirubin Clearance Disorder", "Total and direct bilirubin pattern.", bilirubin),
            ("Low Protein Synthesis Watch", "Albumin and total protein pattern.", synthetic),
        ]
    elif disease == "Kidney":
        ckd = combine_scores(
            high_marker_score(creatinine, 1.2, 2.5),
            high_marker_score(urea, 25, 60),
            high_marker_score(bp, 80, 110),
            model_risk,
        )
        diabetic_nephro = combine_scores(
            high_marker_score(glucose, 125, 180),
            high_marker_score(creatinine, 1.2, 2.5),
            high_marker_score(urea, 25, 60),
        )
        electrolyte = combine_scores(
            high_marker_score(sodium, 145, 155),
            low_marker_score(sodium, 135, 125),
            high_marker_score(potassium, 5.1, 6),
            low_marker_score(potassium, 3.5, 2.8),
        )
        renal_anemia = combine_scores(
            low_marker_score(hemo, 12, 9),
            low_marker_score(rbc, 4.5, 3.5),
            low_marker_score(pcv, 36, 28),
        )
        cards = [
            ("Chronic Kidney Disease Pattern", "Creatinine, urea, blood pressure and kidney model score.", ckd),
            ("Diabetic Nephropathy Watch", "Glucose plus creatinine/urea stress pattern.", diabetic_nephro),
            ("Electrolyte Imbalance", "Sodium and potassium deviation pattern.", electrolyte),
            ("Renal Anemia Pattern", "Hemoglobin, RBC count and packed cell volume.", renal_anemia),
        ]

    rendered = []
    for name, pattern, current in cards:
        future = future_watch_score(
            current,
            5 if age is not None and age >= 45 else 0,
            5 if glucose is not None and glucose > 125 else 0,
            4 if bp is not None and bp > 120 else 0,
        )
        rendered.append(
            {
                "Disease": name,
                "Pattern": pattern,
                "Current Risk": clamp_score(current),
                "Future Risk": future,
            }
        )
    return rendered


def render_specific_disease_patterns(disease, input_values, report_values, model_risk):
    cards = disease_pattern_cards(disease, input_values, report_values, model_risk)

    st.markdown(
        f"""
        <div class="section-panel">
            <h2 style="margin-top:0;">Specific Disease Pattern Screening</h2>
            <p style="color:#9fc1e7;">
                These cards show practical disease patterns that can be estimated from available blood-report
                markers for the {ORGAN_DATA[disease]['organ'].lower()}. They are screening estimates, not diagnosis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for start in range(0, len(cards), 2):
        cols = st.columns(2)
        for offset, card in enumerate(cards[start : start + 2]):
            current = card["Current Risk"]
            future = card["Future Risk"]
            with cols[offset]:
                st.markdown(
                    f"""
                    <div class="disease-risk-card">
                        <h3>{card['Disease']}</h3>
                        <p>{card['Pattern']}</p>
                        <div class="risk-row">
                            <div class="risk-mini">
                                <span>Current screening risk</span>
                                <strong>{current:.1f}%</strong>
                                <div class="risk-meter"><div class="risk-fill" style="width:{current}%;"></div></div>
                            </div>
                            <div class="risk-mini">
                                <span>Future watch risk</span>
                                <strong>{future:.1f}%</strong>
                                <div class="risk-meter"><div class="risk-fill" style="width:{future}%;"></div></div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_hero():
    dna_pairs = "\n".join(
        [
            f'<span class="dna-pair" style="--i:{i}; --top:{18 + i * 16}px; --rot:{(i * 28) % 360}deg;"></span>'
            for i in range(15)
        ]
    )
    st.markdown(
        f"""
        <style>
        .safe-hero {{
            position: relative;
            overflow: hidden;
            min-height: 310px;
            border: 1px solid rgba(77, 163, 255, 0.18);
            border-radius: 18px;
            padding: 30px 34px;
            margin: 8px 0 24px 0;
            background:
                radial-gradient(circle at 82% 28%, rgba(39,231,194,.16), transparent 30%),
                radial-gradient(circle at 18% 12%, rgba(77,163,255,.14), transparent 34%),
                linear-gradient(135deg, rgba(7,15,29,.98), rgba(4,10,20,.94));
            box-shadow: 0 24px 55px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.08);
            transform-style: preserve-3d;
        }}
        .safe-hero-content {{
            position: relative;
            z-index: 2;
            max-width: 690px;
        }}
        .safe-pill {{
            display: inline-flex;
            align-items: center;
            gap: 9px;
            color: #69f4d8;
            background: rgba(39, 231, 194, 0.08);
            border: 1px solid rgba(39, 231, 194, 0.24);
            border-radius: 999px;
            padding: 7px 16px;
            font-weight: 850;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 1px;
        }}
        .safe-pill-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #27e7c2;
            box-shadow: 0 0 16px #27e7c2;
            animation: safePulse 1.8s infinite ease-in-out;
        }}
        .safe-hero h1 {{
            margin: 18px 0 12px 0;
            max-width: 650px;
            font-size: clamp(2.2rem, 5vw, 4rem);
            line-height: 1.04;
            font-weight: 900;
        }}
        .safe-hero-copy {{
            color: #a7c8ee;
            max-width: 660px;
            font-size: 1.08rem;
            line-height: 1.55;
        }}
        .safe-stat-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 14px;
            margin-top: 24px;
        }}
        .safe-stat {{
            min-width: 128px;
            padding: 14px 17px;
            border: 1px solid rgba(77, 163, 255, .18);
            border-radius: 14px;
            background: rgba(15, 26, 46, .72);
            box-shadow: 0 16px 30px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.08);
            transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease;
        }}
        .safe-stat:hover {{
            transform: perspective(700px) rotateX(4deg) rotateY(-5deg) translateY(-3px);
            border-color: rgba(39, 231, 194, .42);
            box-shadow: 0 22px 42px rgba(0,0,0,.36), 0 0 22px rgba(39,231,194,.12);
        }}
        .safe-stat strong {{
            display: block;
            color: #69f4d8;
            font-size: 1.5rem;
            line-height: 1;
        }}
        .safe-stat span {{
            color: #8fb2d8;
            font-size: .86rem;
        }}
        .safe-dna-stage {{
            position: absolute;
            right: 42px;
            top: 18px;
            z-index: 1;
            width: 280px;
            height: 270px;
            perspective: 900px;
            transform-style: preserve-3d;
            animation: safeDnaFloat 5.5s ease-in-out infinite;
        }}
        .safe-dna-stage::before {{
            content: "";
            position: absolute;
            inset: 18px 34px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(39,231,194,.12), transparent 62%);
            filter: blur(4px);
        }}
        .dna-pair {{
            position: absolute;
            top: var(--top);
            left: 50%;
            width: 158px;
            height: 2px;
            transform: translateX(-50%) rotate(var(--rot));
            transform-origin: center;
            background: linear-gradient(90deg, rgba(39,231,194,.05), rgba(39,231,194,.78), rgba(77,163,255,.78), rgba(77,163,255,.05));
            box-shadow: 0 0 12px rgba(77,163,255,.24);
            animation: safeDnaTwist 4.8s linear infinite;
            animation-delay: calc(var(--i) * -0.12s);
        }}
        .dna-pair::before,
        .dna-pair::after {{
            content: "";
            position: absolute;
            top: 50%;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            transform: translateY(-50%);
            box-shadow: 0 0 18px currentColor;
        }}
        .dna-pair::before {{
            left: -6px;
            color: #27e7c2;
            background: radial-gradient(circle at 30% 30%, #ffffff, #27e7c2 34%, #06251f 100%);
        }}
        .dna-pair::after {{
            right: -6px;
            color: #4da3ff;
            background: radial-gradient(circle at 30% 30%, #ffffff, #4da3ff 34%, #06182c 100%);
        }}
        .safe-dna-stage:hover .dna-pair {{
            animation-duration: 1.8s;
        }}
        @keyframes safePulse {{
            0%, 100% {{ transform: scale(.86); opacity: .65; }}
            50% {{ transform: scale(1.15); opacity: 1; }}
        }}
        @keyframes safeDnaFloat {{
            0%, 100% {{ transform: rotateX(7deg) rotateY(-13deg) translateY(0); }}
            50% {{ transform: rotateX(11deg) rotateY(-2deg) translateY(-10px); }}
        }}
        @keyframes safeDnaTwist {{
            from {{ transform: translateX(-50%) rotate(var(--rot)); }}
            to {{ transform: translateX(-50%) rotate(calc(var(--rot) + 360deg)); }}
        }}
        @media (max-width: 900px) {{
            .safe-dna-stage {{ opacity: .32; right: -70px; }}
            .safe-hero {{ min-height: 350px; }}
        }}
        </style>
        <div class="safe-hero">
            <div class="safe-hero-content">
                <div class="safe-pill"><span class="safe-pill-dot"></span> AI-powered blood analysis</div>
                <h1>Organ-level disease risk intelligence</h1>
                <div class="safe-hero-copy">
                    Input your blood report values to get instant risk scores, biomarker comparison,
                    downloadable reports, and estimated future health projections.
                </div>
                <div class="safe-stat-row">
                    <div class="safe-stat"><strong>4</strong><span>Organs monitored</span></div>
                    <div class="safe-stat"><strong>12+</strong><span>Disease signals</span></div>
                    <div class="safe-stat"><strong>PDF</strong><span>Medical report</span></div>
                </div>
            </div>
            <div class="safe-dna-stage" aria-label="Animated DNA double helix">
                {dna_pairs}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


apply_dashboard_theme()
render_hero()


disease = st.sidebar.selectbox(
    "Select Disease to Predict",
    ["Diabetes", "Heart", "Liver", "Kidney"],
)
render_sidebar(disease)
st.sidebar.info("Fill in the blood report values and click Predict.")

if MODEL_LOAD_ERRORS:
    st.sidebar.warning("Some saved models could not be loaded.")
    with st.sidebar.expander("Model load details"):
        for model_name, error_message in MODEL_LOAD_ERRORS.items():
            st.caption(f"{model_name}: {error_message}")


if disease not in models:
    st.error(f"{disease} model was not found in saved_models. Please check the uploaded model files.")
    if disease in MODEL_LOAD_ERRORS:
        st.warning("This model file exists, but Streamlit Cloud could not open it.")
        st.code(MODEL_LOAD_ERRORS[disease])
    st.stop()


render_context_panel(disease)
render_organ_visual(disease)
render_marker_tiles(disease)
render_disease_intelligence(disease)
render_input_console(disease)
report_values, report_id = render_report_upload(disease)
render_report_summary(disease, report_values)


if disease == "Diabetes":
    col1, col2 = st.columns(2)
    with col1:
        gender = st.selectbox(
            "Gender",
            ["Female", "Male"],
            index=selected_gender_index(report_values, ["Female", "Male"]),
            key=field_key(disease, "gender", report_id),
        )
        pregnancies = st.text_input("Pregnancies", autofill(report_values, "pregnancies", "1"), key=field_key(disease, "pregnancies", report_id))
        glucose = st.text_input("Glucose Level", autofill(report_values, "glucose", "120"), key=field_key(disease, "glucose", report_id))
        bp = st.text_input("Blood Pressure", autofill(report_values, "bp", "70"), key=field_key(disease, "bp", report_id))
    with col2:
        skin = st.text_input("Skin Thickness", autofill(report_values, "skin", "20"), key=field_key(disease, "skin", report_id))
        insulin = st.text_input("Insulin", autofill(report_values, "insulin", "80"), key=field_key(disease, "insulin", report_id))
        bmi = st.text_input("BMI", autofill(report_values, "bmi", "25.0"), key=field_key(disease, "bmi", report_id))
        dpf = st.text_input("Diabetes Pedigree Function", autofill(report_values, "dpf", "0.5"), key=field_key(disease, "dpf", report_id))
        age = st.text_input("Age", autofill(report_values, "age", "30"), key=field_key(disease, "age", report_id))
    input_values = {
        "Pregnancies": get_int(pregnancies),
        "Glucose": get_float(glucose),
        "BloodPressure": get_float(bp),
        "SkinThickness": get_float(skin),
        "Insulin": get_float(insulin),
        "BMI": get_float(bmi),
        "DiabetesPedigreeFunction": get_float(dpf),
        "Age": get_int(age),
    }

elif disease == "Heart":
    col1, col2 = st.columns(2)
    with col1:
        age = st.text_input("Age", autofill(report_values, "age", "50"), key=field_key(disease, "age", report_id))
        sex = st.selectbox(
            "Sex",
            [0, 1],
            index=selected_binary_index(report_values, "gender_binary"),
            format_func=lambda x: "Female" if x == 0 else "Male",
            key=field_key(disease, "sex", report_id),
        )
        cp = st.selectbox("Chest Pain Type (0-3)", [0, 1, 2, 3])
        trestbps = st.text_input("Resting Blood Pressure", autofill(report_values, "trestbps", "120"), key=field_key(disease, "trestbps", report_id))
        chol = st.text_input("Cholesterol", autofill(report_values, "chol", "200"), key=field_key(disease, "chol", report_id))
        fbs = st.selectbox(
            "Fasting Blood Sugar > 120",
            [0, 1],
            index=selected_binary_index(report_values, "fbs"),
            key=field_key(disease, "fbs", report_id),
        )
        restecg = st.selectbox("Resting ECG (0-2)", [0, 1, 2])
    with col2:
        thalach = st.text_input("Max Heart Rate", autofill(report_values, "thalach", "150"), key=field_key(disease, "thalach", report_id))
        exang = st.selectbox("Exercise Induced Angina", [0, 1])
        oldpeak = st.text_input("ST Depression", autofill(report_values, "oldpeak", "1.0"), key=field_key(disease, "oldpeak", report_id))
        slope = st.selectbox("Slope of ST (0-2)", [0, 1, 2])
        ca = st.selectbox("Major Vessels (0-4)", [0, 1, 2, 3, 4])
        thal = st.selectbox("Thal (0-3)", [0, 1, 2, 3])
    input_values = {
        "age": get_int(age),
        "sex": sex,
        "cp": cp,
        "trestbps": get_float(trestbps),
        "chol": get_float(chol),
        "fbs": fbs,
        "restecg": restecg,
        "thalach": get_float(thalach),
        "exang": exang,
        "oldpeak": get_float(oldpeak),
        "slope": slope,
        "ca": ca,
        "thal": thal,
    }

elif disease == "Liver":
    col1, col2 = st.columns(2)
    with col1:
        age = st.text_input("Age", autofill(report_values, "age", "40"), key=field_key(disease, "age", report_id))
        gender = st.selectbox(
            "Gender",
            [0, 1],
            index=selected_binary_index(report_values, "gender_binary"),
            format_func=lambda x: "Female" if x == 0 else "Male",
            key=field_key(disease, "gender", report_id),
        )
        total_bili = st.text_input("Total Bilirubin", autofill(report_values, "total_bili", "1.0"), key=field_key(disease, "total_bili", report_id))
        direct_bili = st.text_input("Direct Bilirubin", autofill(report_values, "direct_bili", "0.3"), key=field_key(disease, "direct_bili", report_id))
        alk_phos = st.text_input("Alkaline Phosphotase", autofill(report_values, "alk_phos", "200"), key=field_key(disease, "alk_phos", report_id))
    with col2:
        alt = st.text_input("Alamine Aminotransferase", autofill(report_values, "alt", "30"), key=field_key(disease, "alt", report_id))
        ast = st.text_input("Aspartate Aminotransferase", autofill(report_values, "ast", "30"), key=field_key(disease, "ast", report_id))
        total_prot = st.text_input("Total Proteins", autofill(report_values, "total_prot", "6.5"), key=field_key(disease, "total_prot", report_id))
        albumin = st.text_input("Albumin", autofill(report_values, "albumin", "3.5"), key=field_key(disease, "albumin", report_id))
        ag_ratio = st.text_input("Albumin/Globulin Ratio", autofill(report_values, "ag_ratio", "1.0"), key=field_key(disease, "ag_ratio", report_id))
    input_values = {
        "Age": get_int(age),
        "Gender": gender,
        "Total_Bilirubin": get_float(total_bili),
        "Direct_Bilirubin": get_float(direct_bili),
        "Alkaline_Phosphotase": get_float(alk_phos),
        "Alamine_Aminotransferase": get_float(alt),
        "Aspartate_Aminotransferase": get_float(ast),
        "Total_Protiens": get_float(total_prot),
        "Albumin": get_float(albumin),
        "Albumin_and_Globulin_Ratio": get_float(ag_ratio),
    }

elif disease == "Kidney":
    col1, col2, col3 = st.columns(3)
    with col1:
        gender = st.selectbox(
            "Gender",
            ["Female", "Male"],
            index=selected_gender_index(report_values, ["Female", "Male"]),
            key=field_key(disease, "gender", report_id),
        )
        age = st.text_input("Age", autofill(report_values, "age", "40"), key=field_key(disease, "age", report_id))
        bp = st.text_input("Blood Pressure", autofill(report_values, "bp", "80"), key=field_key(disease, "bp", report_id))
        sg = st.text_input("Specific Gravity", autofill(report_values, "sg", "1.020"), key=field_key(disease, "sg", report_id))
        al = st.text_input("Albumin (0-5)", autofill(report_values, "al", "0"), key=field_key(disease, "al", report_id))
        su = st.text_input("Sugar (0-5)", autofill(report_values, "su", "0"), key=field_key(disease, "su", report_id))
        rbc = st.selectbox("Red Blood Cells", [0, 1], format_func=lambda x: "Abnormal" if x == 0 else "Normal")
        pc = st.selectbox("Pus Cells", [0, 1], format_func=lambda x: "Abnormal" if x == 0 else "Normal")
        pcc = st.selectbox("Pus Cell Clumps", [0, 1], format_func=lambda x: "Not Present" if x == 0 else "Present")
    with col2:
        ba = st.selectbox("Bacteria", [0, 1], format_func=lambda x: "Not Present" if x == 0 else "Present")
        bgr = st.text_input("Blood Glucose Random", autofill(report_values, "bgr", "120"), key=field_key(disease, "bgr", report_id))
        bu = st.text_input("Blood Urea", autofill(report_values, "bu", "40"), key=field_key(disease, "bu", report_id))
        sc = st.text_input("Serum Creatinine", autofill(report_values, "sc", "1.2"), key=field_key(disease, "sc", report_id))
        sod = st.text_input("Sodium", autofill(report_values, "sod", "138"), key=field_key(disease, "sod", report_id))
        pot = st.text_input("Potassium", autofill(report_values, "pot", "4.5"), key=field_key(disease, "pot", report_id))
        hemo = st.text_input("Hemoglobin", autofill(report_values, "hemo", "15.0"), key=field_key(disease, "hemo", report_id))
        pcv = st.text_input("Packed Cell Volume", autofill(report_values, "pcv", "44"), key=field_key(disease, "pcv", report_id))
    with col3:
        wc = st.text_input("White Blood Cell Count", autofill(report_values, "wc", "8000"), key=field_key(disease, "wc", report_id))
        rc = st.text_input("Red Blood Cell Count", autofill(report_values, "rc", "5.0"), key=field_key(disease, "rc", report_id))
        htn = st.selectbox("Hypertension", [0, 1], format_func=lambda x: "No" if x == 0 else "Yes")
        dm = st.selectbox("Diabetes Mellitus", [0, 1], format_func=lambda x: "No" if x == 0 else "Yes")
        cad = st.selectbox("Coronary Artery Disease", [0, 1], format_func=lambda x: "No" if x == 0 else "Yes")
        appet = st.selectbox("Appetite", [0, 1], format_func=lambda x: "Poor" if x == 0 else "Good")
        pe = st.selectbox("Pedal Edema", [0, 1], format_func=lambda x: "No" if x == 0 else "Yes")
        ane = st.selectbox("Anemia", [0, 1], format_func=lambda x: "No" if x == 0 else "Yes")
    input_values = {
        "age": get_float(age),
        "bp": get_float(bp),
        "sg": get_float(sg),
        "al": get_float(al),
        "su": get_float(su),
        "rbc": rbc,
        "pc": pc,
        "pcc": pcc,
        "ba": ba,
        "bgr": get_float(bgr),
        "bu": get_float(bu),
        "sc": get_float(sc),
        "sod": get_float(sod),
        "pot": get_float(pot),
        "hemo": get_float(hemo),
        "pcv": get_float(pcv),
        "wc": get_float(wc),
        "rc": get_float(rc),
        "htn": htn,
        "dm": dm,
        "cad": cad,
        "appet": appet,
        "pe": pe,
        "ane": ane,
    }


st.markdown("---")
if st.button(f"Analyse & predict {disease} risk", use_container_width=True):
    try:
        risk_level, risk_percent, advice, color = predict_disease(disease, input_values)
    except Exception as exc:
        st.error(f"{disease} prediction could not run with the current saved model.")
        st.warning("The website is working, but this model file needs to be retrained or saved again with matching features.")
        st.code(f"{type(exc).__name__}: {exc}")
        st.stop()

    rows = build_analysis_rows(input_values)

    st.markdown("---")
    st.header("Prediction Result")
    render_result_dashboard(disease, risk_level, risk_percent, advice)
    render_specific_disease_patterns(disease, input_values, report_values, risk_percent)

    render_projection(disease, risk_percent)
    render_clinical_explanation(disease, rows, risk_level, risk_percent)

    st.markdown("---")
    st.header("Graphical Biomarker Comparison")
    fig = plot_risk_chart(input_values, disease)
    st.plotly_chart(fig, use_container_width=True)

    st.header("Parameter Analysis")
    st.table(pd.DataFrame(rows))

    st.markdown("---")
    st.header("Download Report")
    pdf_path = generate_pdf(disease, input_values, risk_level, risk_percent, advice, rows)
    with open(pdf_path, "rb") as f:
        st.download_button(
            label="Download PDF Report",
            data=f,
            file_name=f"BioPredict_{disease}_Report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    st.warning("This is an AI screening tool only. Always consult a qualified physician.")


st.markdown("---")
st.markdown("**BioPredict AI** | Organ-level AI screening dashboard built with Machine Learning")

