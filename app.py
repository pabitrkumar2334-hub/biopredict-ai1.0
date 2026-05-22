import streamlit as st
import pickle
import pandas as pd
import plotly.graph_objects as go
import os
from fpdf import FPDF
import tempfile
from datetime import datetime


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
            right: 8px;
            top: 6px;
            width: 230px;
            height: 210px;
            opacity: .95;
        }

        .dna-rail {
            position: absolute;
            inset: 0;
            border-radius: 50%;
            animation: dnaSway 4s ease-in-out infinite alternate;
        }

        .strand {
            position: absolute;
            top: 5px;
            width: 6px;
            height: 190px;
            border-radius: 999px;
            background: linear-gradient(#27e7c2, transparent, #4da3ff);
            box-shadow: 0 0 18px rgba(39,231,194,.55);
        }

        .strand.left { left: 77px; transform: rotate(22deg); }
        .strand.right { right: 77px; transform: rotate(-22deg); }

        .rung {
            position: absolute;
            left: 78px;
            width: 78px;
            height: 2px;
            background: repeating-linear-gradient(90deg, rgba(77,163,255,.8) 0 6px, transparent 6px 12px);
            opacity: .8;
        }

        .rung.r1 { top: 32px; }
        .rung.r2 { top: 62px; }
        .rung.r3 { top: 92px; }
        .rung.r4 { top: 122px; }
        .rung.r5 { top: 152px; }

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

        @keyframes pulse {
            0%, 100% { transform: scale(.88); opacity: .65; }
            50% { transform: scale(1.12); opacity: 1; }
        }

        @keyframes floatOrb {
            0%, 100% { transform: translate(0, 0); }
            50% { transform: translate(9px, -10px); }
        }

        @keyframes dnaSway {
            from { transform: rotate(-4deg) translateY(0); }
            to { transform: rotate(4deg) translateY(8px); }
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
            .marker-grid, .projection-grid, .intel-grid, .result-actions { grid-template-columns: 1fr 1fr; }
            .result-top { align-items: flex-start; }
        }

        @media (max-width: 620px) {
            .marker-grid, .projection-grid, .intel-grid, .result-actions { grid-template-columns: 1fr; }
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
                <div class="dna-rail">
                    <div class="strand left"></div>
                    <div class="strand right"></div>
                    <div class="rung r1"></div>
                    <div class="rung r2"></div>
                    <div class="rung r3"></div>
                    <div class="rung r4"></div>
                    <div class="rung r5"></div>
                    <div class="orb o1"></div>
                    <div class="orb o2"></div>
                    <div class="orb o3"></div>
                    <div class="orb o4"></div>
                </div>
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


def render_disease_intelligence(disease):
    data = ORGAN_DATA[disease]
    signal_cards = []
    for index, signal in enumerate(data["signals"], start=1):
        signal_cards.append(
            f"""
            <div class="intel-card">
                <span>Signal {index}</span>
                <strong>{signal}</strong>
            </div>
            """
        )

    st.markdown(
        f"""
        <div class="section-panel">
            <h2 style="margin-top:0;">Disease Intelligence</h2>
            <p style="color:#9fc1e7;margin-bottom:0;">
                This module studies biomarker patterns linked with {data['subtitle'].lower()}.
                It is designed for early screening and report discussion, not final diagnosis.
            </p>
            <div class="intel-grid">{''.join(signal_cards)}</div>
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
    pdf.set_fill_color(6, 18, 35)
    pdf.rect(0, 0, 210, 38, "F")
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "", ln=True)
    pdf.cell(0, 15, "  BioPredict AI - Medical Report", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"  Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, f"{disease} Risk Assessment", ln=True)
    pdf.ln(3)

    if risk_level == "HIGH RISK":
        r, g, b = 231, 76, 60
    elif risk_level == "MODERATE RISK":
        r, g, b = 243, 156, 18
    else:
        r, g, b = 39, 174, 96

    pdf.set_fill_color(r, g, b)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 12, f"  Risk Level: {risk_level}  |  Risk Score: {risk_percent:.2f}%", ln=True, fill=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 8, f"Advice: {advice}")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(52, 73, 94)
    pdf.cell(60, 9, "Parameter", border=1, fill=True)
    pdf.cell(40, 9, "Your Value", border=1, fill=True)
    pdf.cell(50, 9, "Normal Range", border=1, fill=True)
    pdf.cell(40, 9, "Status", border=1, fill=True, ln=True)

    pdf.set_font("Helvetica", "", 11)
    for row in rows:
        status = row["Status"].replace("Above: ", "").replace("Normal: ", "").replace("Below: ", "")
        if "Above" in status:
            pdf.set_text_color(231, 76, 60)
        elif "Below" in status:
            pdf.set_text_color(52, 152, 219)
        else:
            pdf.set_text_color(39, 174, 96)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(60, 8, str(row["Parameter"]), border=1, fill=True)
        pdf.cell(40, 8, str(round(row["Your Value"], 2)), border=1, fill=True)
        pdf.cell(50, 8, str(row["Normal Range"]), border=1, fill=True)
        pdf.cell(40, 8, status, border=1, fill=True, ln=True)

    pdf.ln(8)
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
render_marker_tiles(disease)
render_disease_intelligence(disease)


if disease == "Diabetes":
    col1, col2 = st.columns(2)
    with col1:
        gender = st.selectbox("Gender", ["Female", "Male"])
        pregnancies = st.text_input("Pregnancies", "1")
        glucose = st.text_input("Glucose Level", "120")
        bp = st.text_input("Blood Pressure", "70")
    with col2:
        skin = st.text_input("Skin Thickness", "20")
        insulin = st.text_input("Insulin", "80")
        bmi = st.text_input("BMI", "25.0")
        dpf = st.text_input("Diabetes Pedigree Function", "0.5")
        age = st.text_input("Age", "30")
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
        age = st.text_input("Age", "50")
        sex = st.selectbox("Sex", [0, 1], format_func=lambda x: "Female" if x == 0 else "Male")
        cp = st.selectbox("Chest Pain Type (0-3)", [0, 1, 2, 3])
        trestbps = st.text_input("Resting Blood Pressure", "120")
        chol = st.text_input("Cholesterol", "200")
        fbs = st.selectbox("Fasting Blood Sugar > 120", [0, 1])
        restecg = st.selectbox("Resting ECG (0-2)", [0, 1, 2])
    with col2:
        thalach = st.text_input("Max Heart Rate", "150")
        exang = st.selectbox("Exercise Induced Angina", [0, 1])
        oldpeak = st.text_input("ST Depression", "1.0")
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
        age = st.text_input("Age", "40")
        gender = st.selectbox("Gender", [0, 1], format_func=lambda x: "Female" if x == 0 else "Male")
        total_bili = st.text_input("Total Bilirubin", "1.0")
        direct_bili = st.text_input("Direct Bilirubin", "0.3")
        alk_phos = st.text_input("Alkaline Phosphotase", "200")
    with col2:
        alt = st.text_input("Alamine Aminotransferase", "30")
        ast = st.text_input("Aspartate Aminotransferase", "30")
        total_prot = st.text_input("Total Proteins", "6.5")
        albumin = st.text_input("Albumin", "3.5")
        ag_ratio = st.text_input("Albumin/Globulin Ratio", "1.0")
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
        gender = st.selectbox("Gender", ["Female", "Male"])
        age = st.text_input("Age", "40")
        bp = st.text_input("Blood Pressure", "80")
        sg = st.text_input("Specific Gravity", "1.020")
        al = st.text_input("Albumin (0-5)", "0")
        su = st.text_input("Sugar (0-5)", "0")
        rbc = st.selectbox("Red Blood Cells", [0, 1], format_func=lambda x: "Abnormal" if x == 0 else "Normal")
        pc = st.selectbox("Pus Cells", [0, 1], format_func=lambda x: "Abnormal" if x == 0 else "Normal")
        pcc = st.selectbox("Pus Cell Clumps", [0, 1], format_func=lambda x: "Not Present" if x == 0 else "Present")
    with col2:
        ba = st.selectbox("Bacteria", [0, 1], format_func=lambda x: "Not Present" if x == 0 else "Present")
        bgr = st.text_input("Blood Glucose Random", "120")
        bu = st.text_input("Blood Urea", "40")
        sc = st.text_input("Serum Creatinine", "1.2")
        sod = st.text_input("Sodium", "138")
        pot = st.text_input("Potassium", "4.5")
        hemo = st.text_input("Hemoglobin", "15.0")
        pcv = st.text_input("Packed Cell Volume", "44")
    with col3:
        wc = st.text_input("White Blood Cell Count", "8000")
        rc = st.text_input("Red Blood Cell Count", "5.0")
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

    render_projection(disease, risk_percent)

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
