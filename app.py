import streamlit as st
import pickle
import pandas as pd
import plotly.graph_objects as go
import os
from fpdf import FPDF
import tempfile
from datetime import datetime
import re
import hashlib

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
            --panel: rgba(12, 22, 38, 0.78);
            --panel-strong: rgba(15, 26, 46, 0.94);
            --line: rgba(66, 190, 255, 0.18);
            --text: #f5f8ff;
            --muted: #8fb2d8;
            --cyan: #27e7c2;
            --blue: #4da3ff;
            --warning: #ffb02e;
            --danger: #ff5a67;
        }

        .stApp {
            background:
                radial-gradient(circle at 12% 18%, rgba(39, 231, 194, 0.12), transparent 28%),
                radial-gradient(circle at 88% 8%, rgba(77, 163, 255, 0.15), transparent 32%),
                linear-gradient(135deg, #050b16 0%, #081426 48%, #030611 100%);
            color: var(--text);
        }

        .block-container {
            padding-top: 1.5rem;
            max-width: 1220px;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(6, 15, 28, 0.98), rgba(3, 8, 17, 0.98));
            border-right: 1px solid rgba(39, 231, 194, 0.18);
        }

        h1, h2, h3, label, p {
            letter-spacing: 0;
        }

        h1, h2, h3 {
            color: #ffffff;
        }

        div[data-testid="stMetric"],
        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            background: rgba(12, 22, 38, 0.56);
            border: 1px solid rgba(77, 163, 255, 0.16);
            border-radius: 12px;
            padding: 10px;
        }

        input, textarea, div[data-baseweb="select"] > div {
            background: rgba(255, 255, 255, 0.06) !important;
            border: 1px solid rgba(77, 163, 255, 0.20) !important;
            border-radius: 10px !important;
            color: #ffffff !important;
        }

        div[data-testid="stTextInput"],
        div[data-testid="stSelectbox"] {
            background: rgba(255,255,255,.035);
            border: 1px solid rgba(77,163,255,.12);
            border-radius: 12px;
            padding: 10px 12px 12px 12px;
            margin-bottom: 8px;
            transition: border-color .18s ease, background .18s ease, transform .18s ease;
        }

        div[data-testid="stTextInput"]:hover,
        div[data-testid="stSelectbox"]:hover {
            border-color: rgba(39,231,194,.34);
            background: rgba(39,231,194,.045);
            transform: translateY(-1px);
        }

        div[data-testid="stTextInput"] label,
        div[data-testid="stSelectbox"] label {
            color: #7fb9ef !important;
            font-weight: 800 !important;
            text-transform: uppercase;
            font-size: .78rem;
        }

        .stButton > button,
        .stDownloadButton > button {
            background: linear-gradient(90deg, #27e7c2, #4da3ff) !important;
            color: #04101e !important;
            border: 0 !important;
            border-radius: 10px !important;
            min-height: 3.1rem;
            font-size: 1.02rem;
            font-weight: 800;
            box-shadow: 0 0 28px rgba(39, 231, 194, 0.25);
            transition: transform .18s ease, box-shadow .18s ease, filter .18s ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            transform: translateY(-2px);
            filter: brightness(1.08);
            box-shadow: 0 0 38px rgba(39, 231, 194, 0.42);
        }

        .hero {
            position: relative;
            overflow: hidden;
            min-height: 270px;
            border-bottom: 1px solid rgba(39, 231, 194, 0.20);
            padding: 18px 0 26px 0;
            margin-bottom: 22px;
        }

        .hero-pill {
            display: inline-flex;
            align-items: center;
            gap: 9px;
            color: #69f4d8;
            background: rgba(39, 231, 194, 0.10);
            border: 1px solid rgba(39, 231, 194, 0.28);
            border-radius: 999px;
            padding: 6px 16px;
            font-weight: 800;
            margin-bottom: 16px;
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
            line-height: 1.02;
            margin: 0 0 12px 0;
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
            background: rgba(255,255,255,0.045);
            border: 1px solid rgba(143,178,216,0.20);
            border-radius: 10px;
            padding: 13px 16px;
            text-align: center;
            backdrop-filter: blur(8px);
            animation: riseIn .7s ease both;
        }

        .stat-card strong {
            display: block;
            color: #69f4d8;
            font-size: 1.45rem;
            line-height: 1.1;
        }

        .stat-card span {
            color: #8fb2d8;
            font-size: .86rem;
        }

        .dna-stage {
            position: absolute;
            right: 10px;
            top: 4px;
            width: 285px;
            height: 250px;
            opacity: .95;
            perspective: 900px;
        }

        .dna-helix-svg {
            width: 100%;
            height: 100%;
            overflow: visible;
            filter: drop-shadow(0 0 18px rgba(39,231,194,.24));
            animation: dnaFloat3d 6s ease-in-out infinite;
            transform-origin: center;
        }

        .dna-stage:hover .dna-helix-svg {
            animation-duration: 2.2s;
            transform: rotateY(18deg) scale(1.04);
        }

        .dna-strand-a,
        .dna-strand-b {
            fill: none;
            stroke-width: 5;
            stroke-linecap: round;
            stroke-dasharray: 10 12;
            animation: strandFlow 3.4s linear infinite;
        }

        .dna-strand-a { stroke: #27e7c2; }
        .dna-strand-b { stroke: #4da3ff; animation-delay: -.8s; }

        .h-bond {
            stroke: rgba(175, 220, 255, .72);
            stroke-width: 2;
            stroke-dasharray: 4 6;
            animation: bondPulse 2.4s ease-in-out infinite;
        }

        .base-node {
            fill: #07111f;
            stroke-width: 3;
            animation: baseGlow 2.8s ease-in-out infinite;
        }

        .node-a { stroke: #27e7c2; }
        .node-b { stroke: #4da3ff; }

        .dna-label {
            fill: #8fb2d8;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1px;
            opacity: .9;
        }

        .orb {
            position: absolute;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #27e7c2;
            box-shadow: 0 0 14px currentColor;
            animation: floatOrb 3.2s ease-in-out infinite;
        }

        .orb.o1 { left: 50px; top: 10px; color: #27e7c2; }
        .orb.o2 { right: 42px; top: 18px; color: #4da3ff; animation-delay: .25s; }
        .orb.o3 { left: 28px; top: 88px; color: #27e7c2; animation-delay: .5s; }
        .orb.o4 { right: 26px; top: 130px; color: #4da3ff; animation-delay: .75s; }

        .organ-visual-intro {
            background:
                radial-gradient(circle at 82% 35%, rgba(39,231,194,.10), transparent 35%),
                rgba(12, 22, 38, 0.62);
            border: 1px solid rgba(77, 163, 255, 0.16);
            border-radius: 16px;
            padding: 18px;
            margin: 12px 0 20px 0;
            box-shadow: 0 20px 60px rgba(0,0,0,.18);
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
            border-radius: 14px;
            border: 1px solid rgba(77,163,255,.14);
            background:
                radial-gradient(circle at 50% 50%, rgba(77,163,255,.12), transparent 46%),
                rgba(255,255,255,.035);
            padding: 14px;
            box-sizing: border-box;
        }

        .organ-main {
            fill: rgba(39,231,194,.16);
            stroke: var(--organ-tone);
            stroke-width: 3;
            filter: drop-shadow(0 0 18px rgba(39,231,194,.25));
            transform-origin: center;
            animation: organBreathe 3.4s ease-in-out infinite;
        }

        .organ-secondary {
            fill: none;
            stroke: rgba(143,178,216,.75);
            stroke-width: 2;
            stroke-linecap: round;
            stroke-dasharray: 7 9;
            animation: vesselFlow 3s linear infinite;
        }

        .organ-node {
            fill: var(--organ-tone);
            opacity: .95;
            filter: drop-shadow(0 0 8px var(--organ-tone));
            animation: baseGlow 2.2s ease-in-out infinite;
        }

        .organ-svg:hover .organ-main {
            animation-duration: 1.4s;
            filter: drop-shadow(0 0 28px var(--organ-tone));
        }

        .organ-svg:hover .organ-secondary {
            stroke-dashoffset: -34;
        }

        .section-panel {
            background: rgba(12, 22, 38, 0.62);
            border: 1px solid rgba(77, 163, 255, 0.16);
            border-radius: 14px;
            padding: 18px;
            margin: 12px 0 18px 0;
            box-shadow: 0 20px 60px rgba(0,0,0,.18);
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
            background: rgba(255,255,255,.045);
            border: 1px solid rgba(77,163,255,.16);
            border-radius: 12px;
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
            border: 1px solid rgba(39,231,194,.55);
            position: relative;
            box-shadow: inset 0 0 18px rgba(39,231,194,.13);
        }

        .marker-icon:before,
        .marker-icon:after {
            content: "";
            position: absolute;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #27e7c2;
            box-shadow: 0 0 12px #27e7c2;
        }

        .marker-icon:before { left: 5px; top: 8px; }
        .marker-icon:after { right: 6px; bottom: 7px; background: #4da3ff; }

        .marker-card strong { color: #dcecff; }
        .marker-card span { color: #6fa9dd; font-size: .82rem; text-align: center; }

        .organ-card {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            background: rgba(255,255,255,.045);
            border: 1px solid rgba(77,163,255,.14);
            border-radius: 12px;
            padding: 12px 13px;
            margin-bottom: 10px;
        }

        .organ-card.active {
            border-color: rgba(39,231,194,.75);
            background: rgba(39,231,194,.08);
            box-shadow: 0 0 22px rgba(39,231,194,.10);
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
        }

        .cell {
            position: absolute;
            border-radius: 50%;
            border: 1px solid rgba(255,90,103,.6);
            background: radial-gradient(circle at 50% 50%, rgba(255,90,103,.45), rgba(80,25,80,.40));
            box-shadow: 0 0 18px rgba(255,90,103,.18);
            animation: drift 6s ease-in-out infinite alternate;
        }

        .cell.c1 { width: 22px; height: 14px; left: 14%; top: 28%; }
        .cell.c2 { width: 38px; height: 24px; left: 42%; top: 44%; animation-delay: .6s; }
        .cell.c3 { width: 20px; height: 13px; right: 18%; top: 30%; animation-delay: 1s; }
        .cell.c4 { width: 20px; height: 13px; left: 10%; bottom: 20%; animation-delay: 1.4s; }
        .cell.c5 { width: 24px; height: 14px; right: 10%; bottom: 18%; animation-delay: 1.8s; }

        .wbc {
            position: absolute;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            border: 1px solid #4da3ff;
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
            background: rgba(255,255,255,.045);
            border: 1px solid rgba(77,163,255,.16);
            border-radius: 12px;
            padding: 14px;
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
        }

        .input-console {
            background:
                linear-gradient(135deg, rgba(15,26,46,.94), rgba(6,15,28,.82)),
                radial-gradient(circle at 88% 22%, rgba(77,163,255,.12), transparent 34%);
            border: 1px solid rgba(77,163,255,.18);
            border-radius: 16px;
            padding: 18px;
            margin: 16px 0 18px 0;
            box-shadow: 0 18px 55px rgba(0,0,0,.18);
        }

        .input-console-top {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 18px;
        }

        .input-console h2 {
            margin: 0 0 8px 0;
        }

        .input-console p {
            color: #9fc1e7;
            margin: 0;
            line-height: 1.5;
        }

        .console-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 14px;
        }

        .console-chip {
            background: rgba(255,255,255,.045);
            border: 1px solid rgba(77,163,255,.16);
            border-radius: 999px;
            padding: 7px 12px;
            color: #cfe6ff;
            font-size: .84rem;
            font-weight: 750;
        }

        .console-chip b {
            color: #69f4d8;
        }

        .upload-panel {
            background:
                linear-gradient(135deg, rgba(39,231,194,.08), rgba(77,163,255,.06)),
                rgba(255,255,255,.035);
            border: 1px solid rgba(39,231,194,.22);
            border-radius: 16px;
            padding: 18px;
            margin: 14px 0 20px 0;
        }

        .upload-panel h2 {
            margin: 0 0 8px 0;
        }

        .upload-panel p {
            color: #9fc1e7;
            margin: 0;
            line-height: 1.5;
        }

        .extraction-list {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-top: 12px;
        }

        .extract-pill {
            background: rgba(255,255,255,.045);
            border: 1px solid rgba(77,163,255,.16);
            border-radius: 10px;
            padding: 9px 11px;
            color: #dcecff;
            font-size: .86rem;
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
            background: rgba(255,255,255,.045);
            border: 1px solid rgba(77,163,255,.16);
            border-radius: 12px;
            padding: 14px;
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

        .result-card {
            position: relative;
            overflow: hidden;
            background:
                linear-gradient(135deg, rgba(15, 26, 46, .96), rgba(6, 15, 28, .86)),
                radial-gradient(circle at 85% 18%, rgba(39,231,194,.18), transparent 35%);
            border: 1px solid rgba(39,231,194,.22);
            border-radius: 16px;
            padding: 22px;
            margin: 4px 0 18px 0;
            box-shadow: 0 24px 70px rgba(0,0,0,.25);
        }

        .result-card:after {
            content: "";
            position: absolute;
            left: -45%;
            top: 0;
            width: 40%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,.08), transparent);
            animation: resultScan 3s ease-in-out infinite;
        }

        .result-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            position: relative;
            z-index: 1;
        }

        .risk-ring {
            width: 132px;
            height: 132px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background: conic-gradient(var(--risk-color) var(--risk-angle), rgba(255,255,255,.08) 0);
            box-shadow: 0 0 32px rgba(39,231,194,.14);
        }

        .risk-ring-inner {
            width: 102px;
            height: 102px;
            border-radius: 50%;
            background: #07111f;
            display: grid;
            place-items: center;
            text-align: center;
            border: 1px solid rgba(255,255,255,.08);
        }

        .risk-ring-inner strong {
            color: white;
            font-size: 1.45rem;
            line-height: 1;
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
            background: rgba(255,255,255,.045);
            border: 1px solid rgba(77,163,255,.14);
            border-radius: 12px;
            padding: 12px;
            color: #dcecff;
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

        .disease-risk-card {
            background:
                linear-gradient(135deg, rgba(15,26,46,.94), rgba(6,15,28,.82)),
                rgba(255,255,255,.035);
            border: 1px solid rgba(77,163,255,.18);
            border-radius: 14px;
            padding: 16px;
            box-shadow: 0 16px 42px rgba(0,0,0,.14);
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
        }

        .risk-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #27e7c2, #ffb02e, #ff5a67);
        }

        .risk-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .risk-mini {
            background: rgba(255,255,255,.045);
            border: 1px solid rgba(77,163,255,.14);
            border-radius: 10px;
            padding: 9px;
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

        @keyframes pulse {
            0%, 100% { transform: scale(.88); opacity: .65; }
            50% { transform: scale(1.12); opacity: 1; }
        }

        @keyframes floatOrb {
            0%, 100% { transform: translate(0, 0); }
            50% { transform: translate(9px, -10px); }
        }

        @keyframes dnaFloat3d {
            0%, 100% { transform: rotateY(-10deg) rotateZ(-2deg) translateY(0); }
            50% { transform: rotateY(12deg) rotateZ(2deg) translateY(8px); }
        }

        @keyframes strandFlow {
            from { stroke-dashoffset: 0; }
            to { stroke-dashoffset: -44; }
        }

        @keyframes bondPulse {
            0%, 100% { opacity: .35; stroke-width: 1.4; }
            50% { opacity: .95; stroke-width: 2.4; }
        }

        @keyframes baseGlow {
            0%, 100% { opacity: .65; transform: scale(.92); }
            50% { opacity: 1; transform: scale(1.08); }
        }

        @keyframes organBreathe {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.035); }
        }

        @keyframes vesselFlow {
            from { stroke-dashoffset: 0; }
            to { stroke-dashoffset: -32; }
        }

        @keyframes riseIn {
            from { transform: translateY(10px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        @keyframes drift {
            from { transform: translate(-5px, 4px) rotate(0deg); }
            to { transform: translate(9px, -8px) rotate(16deg); }
        }

        @keyframes resultScan {
            0% { left: -45%; }
            55%, 100% { left: 120%; }
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
                <svg class="dna-helix-svg" viewBox="0 0 260 250" role="img" aria-label="Interactive DNA double helix">
                    <defs>
                        <linearGradient id="dnaA" x1="0" x2="1">
                            <stop offset="0%" stop-color="#27e7c2"/>
                            <stop offset="100%" stop-color="#64ffe8"/>
                        </linearGradient>
                        <linearGradient id="dnaB" x1="0" x2="1">
                            <stop offset="0%" stop-color="#4da3ff"/>
                            <stop offset="100%" stop-color="#9dbdff"/>
                        </linearGradient>
                    </defs>
                    <path class="dna-strand-a" stroke="url(#dnaA)" d="M82 20 C178 48, 178 78, 82 106 C-14 134, -14 166, 82 194 C134 209, 170 222, 182 236"/>
                    <path class="dna-strand-b" stroke="url(#dnaB)" d="M178 20 C82 48, 82 78, 178 106 C274 134, 274 166, 178 194 C126 209, 90 222, 78 236"/>
                    <line class="h-bond" x1="88" y1="34" x2="172" y2="34"/>
                    <line class="h-bond" x1="113" y1="62" x2="147" y2="62"/>
                    <line class="h-bond" x1="84" y1="92" x2="176" y2="92"/>
                    <line class="h-bond" x1="78" y1="124" x2="182" y2="124"/>
                    <line class="h-bond" x1="86" y1="156" x2="174" y2="156"/>
                    <line class="h-bond" x1="111" y1="186" x2="149" y2="186"/>
                    <line class="h-bond" x1="84" y1="216" x2="176" y2="216"/>
                    <circle class="base-node node-a" cx="88" cy="34" r="7"/>
                    <circle class="base-node node-b" cx="172" cy="34" r="7"/>
                    <circle class="base-node node-a" cx="113" cy="62" r="6"/>
                    <circle class="base-node node-b" cx="147" cy="62" r="6"/>
                    <circle class="base-node node-a" cx="84" cy="92" r="7"/>
                    <circle class="base-node node-b" cx="176" cy="92" r="7"/>
                    <circle class="base-node node-a" cx="78" cy="124" r="7"/>
                    <circle class="base-node node-b" cx="182" cy="124" r="7"/>
                    <circle class="base-node node-a" cx="86" cy="156" r="7"/>
                    <circle class="base-node node-b" cx="174" cy="156" r="7"/>
                    <circle class="base-node node-a" cx="111" cy="186" r="6"/>
                    <circle class="base-node node-b" cx="149" cy="186" r="6"/>
                    <circle class="base-node node-a" cx="84" cy="216" r="7"/>
                    <circle class="base-node node-b" cx="176" cy="216" r="7"/>
                    <text class="dna-label" x="12" y="236">H-BONDS</text>
                    <text class="dna-label" x="176" y="18">DNA HELIX</text>
                </svg>
            </div>
        </div>
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
            <path class="organ-main" d="M63 130 C80 76, 132 72, 164 103 C186 124, 217 104, 247 84 C288 58, 333 80, 327 125 C321 169, 275 179, 235 158 C204 142, 185 145, 164 166 C132 199, 76 184, 63 130 Z"/>
            <path class="organ-secondary" d="M96 135 C135 103, 180 128, 222 108 C254 94, 282 95, 306 116"/>
            <path class="organ-secondary" d="M118 158 C145 143, 175 149, 204 137"/>
            <circle class="organ-node" cx="118" cy="111" r="6"/>
            <circle class="organ-node" cx="203" cy="132" r="7"/>
            <circle class="organ-node" cx="287" cy="116" r="6"/>
            <text x="118" y="220" fill="#8fb2d8" font-size="13" font-weight="800">PANCREAS / INSULIN RESPONSE</text>
        </svg>
        """
    if disease == "Heart":
        return f"""
        <svg class="organ-svg" viewBox="0 0 360 240" style="--organ-tone:{tone};" role="img" aria-label="Interactive heart organ drawing">
            <path class="organ-main" d="M180 205 C72 136, 55 65, 106 43 C137 30, 165 49, 180 76 C196 49, 224 30, 255 43 C306 65, 288 136, 180 205 Z"/>
            <path class="organ-secondary" d="M180 76 C169 111, 173 144, 180 205"/>
            <path class="organ-secondary" d="M130 78 C150 94, 166 112, 181 135 C203 116, 225 100, 251 86"/>
            <path class="organ-secondary" d="M145 35 C142 18, 151 11, 168 23"/>
            <path class="organ-secondary" d="M217 35 C220 18, 211 11, 194 23"/>
            <circle class="organ-node" cx="142" cy="91" r="6"/>
            <circle class="organ-node" cx="218" cy="91" r="6"/>
            <circle class="organ-node" cx="180" cy="141" r="7"/>
            <text x="118" y="225" fill="#8fb2d8" font-size="13" font-weight="800">HEART / CARDIAC RISK</text>
        </svg>
        """
    if disease == "Liver":
        return f"""
        <svg class="organ-svg" viewBox="0 0 360 240" style="--organ-tone:{tone};" role="img" aria-label="Interactive liver organ drawing">
            <path class="organ-main" d="M45 111 C68 57, 142 43, 224 55 C294 66, 333 98, 313 145 C291 198, 201 186, 154 161 C116 141, 71 163, 50 140 C41 131, 39 122, 45 111 Z"/>
            <path class="organ-secondary" d="M142 60 C154 100, 153 133, 136 166"/>
            <path class="organ-secondary" d="M162 112 C201 101, 244 111, 286 137"/>
            <path class="organ-secondary" d="M95 125 C123 109, 157 109, 184 128"/>
            <circle class="organ-node" cx="142" cy="103" r="7"/>
            <circle class="organ-node" cx="210" cy="115" r="6"/>
            <circle class="organ-node" cx="276" cy="139" r="6"/>
            <text x="112" y="222" fill="#8fb2d8" font-size="13" font-weight="800">LIVER / ENZYME PATTERN</text>
        </svg>
        """
    return f"""
    <svg class="organ-svg" viewBox="0 0 360 240" style="--organ-tone:{tone};" role="img" aria-label="Interactive kidney organ drawing">
        <path class="organ-main" d="M127 41 C77 51, 54 111, 76 158 C91 190, 124 202, 153 184 C175 170, 170 138, 154 122 C139 107, 157 82, 156 63 C155 47, 144 38, 127 41 Z"/>
        <path class="organ-main" d="M233 41 C283 51, 306 111, 284 158 C269 190, 236 202, 207 184 C185 170, 190 138, 206 122 C221 107, 203 82, 204 63 C205 47, 216 38, 233 41 Z"/>
        <path class="organ-secondary" d="M180 54 C177 94, 177 128, 180 172"/>
        <path class="organ-secondary" d="M156 125 C172 128, 178 138, 180 172"/>
        <path class="organ-secondary" d="M204 125 C188 128, 182 138, 180 172"/>
        <circle class="organ-node" cx="126" cy="102" r="6"/>
        <circle class="organ-node" cx="234" cy="102" r="6"/>
        <circle class="organ-node" cx="180" cy="172" r="7"/>
        <text x="110" y="225" fill="#8fb2d8" font-size="13" font-weight="800">KIDNEYS / FILTRATION</text>
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
            <h2>Upload Blood Report PDF</h2>
            <p>
                Upload a hospital blood report PDF to auto-detect available values.
                You can still edit every field before running prediction.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader(
        "Upload hospital blood report PDF",
        type=["pdf"],
        key=f"{disease}_report_upload",
        help="Works best with text-based lab PDFs. Scanned image PDFs may need manual entry.",
    )

    report_text, report_id = extract_pdf_text(uploaded_file)
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
                "I could not confidently find matching values in this PDF. "
                "This can happen with scanned reports or unusual lab formats. Please enter values manually."
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


@st.cache_resource
def load_models():
    models = {}
    model_dir = "./saved_models"
    for disease in ["diabetes", "heart", "liver", "kidney"]:
        path = f"{model_dir}/{disease}_model.pkl"
        if os.path.exists(path):
            with open(path, "rb") as f:
                models[disease.capitalize()] = pickle.load(f)
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


apply_dashboard_theme()
render_hero()


disease = st.sidebar.selectbox(
    "Select Disease to Predict",
    ["Diabetes", "Heart", "Liver", "Kidney"],
)
render_sidebar(disease)
st.sidebar.info("Fill in the blood report values and click Predict.")


if disease not in models:
    st.error(f"{disease} model was not found in saved_models. Please check the uploaded model files.")
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
    risk_level, risk_percent, advice, color = predict_disease(disease, input_values)
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
