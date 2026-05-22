
import streamlit as st
import pickle
import pandas as pd
import plotly.graph_objects as go
import os
from fpdf import FPDF
import tempfile
from datetime import datetime

st.set_page_config(page_title="BioPredict AI", page_icon="🏥", layout="wide")
def apply_biotech_theme():
    st.markdown("""
    <style>
    .stApp {
        background:
            radial-gradient(circle at 20% 20%, rgba(0, 255, 213, 0.12), transparent 28%),
            radial-gradient(circle at 80% 10%, rgba(92, 70, 255, 0.16), transparent 30%),
            linear-gradient(135deg, #050816 0%, #07111f 45%, #02040a 100%);
        color: #f5f7fb;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(9, 18, 35, 0.98), rgba(4, 8, 18, 0.98));
        border-right: 1px solid rgba(0, 255, 213, 0.18);
    }

    h1, h2, h3 {
        letter-spacing: 0px;
        color: #ffffff;
    }

    div[data-testid="stMetric"] {
        background: rgba(12, 22, 42, 0.72);
        border: 1px solid rgba(0, 255, 213, 0.22);
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 0 28px rgba(0, 255, 213, 0.08);
        animation: cardFloat 4s ease-in-out infinite;
    }

    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(90deg, #00f5d4, #5b6cff);
        color: #02040a;
        border: none;
        border-radius: 12px;
        font-weight: 800;
        padding: 0.8rem 1rem;
        box-shadow: 0 0 24px rgba(0, 245, 212, 0.28);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-2px) scale(1.01);
        box-shadow: 0 0 34px rgba(0, 245, 212, 0.48);
    }

    input, textarea, div[data-baseweb="select"] > div {
        border-radius: 12px !important;
        border: 1px solid rgba(0, 255, 213, 0.16) !important;
    }

    .bio-hero {
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(0, 255, 213, 0.22);
        border-radius: 22px;
        padding: 34px 34px;
        margin-bottom: 28px;
        background:
            linear-gradient(120deg, rgba(10, 22, 44, 0.88), rgba(7, 10, 24, 0.82)),
            radial-gradient(circle at 80% 50%, rgba(0, 245, 212, 0.18), transparent 35%);
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
    }

    .bio-hero h1 {
        font-size: 3rem;
        margin: 0;
        background: linear-gradient(90deg, #ffffff, #80fff1, #aab4ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .bio-hero p {
        color: #b8c7e6;
        font-size: 1.05rem;
        max-width: 680px;
    }

    .dna-wrap {
        position: absolute;
        right: 42px;
        top: 20px;
        width: 170px;
        height: 170px;
        opacity: 0.95;
        animation: slowSpin 18s linear infinite;
    }

    .dna-line {
        position: absolute;
        left: 50%;
        width: 4px;
        height: 170px;
        background: linear-gradient(#00f5d4, #5b6cff);
        border-radius: 999px;
        box-shadow: 0 0 18px rgba(0, 245, 212, 0.8);
    }

    .dna-line.one { transform: rotate(24deg); }
    .dna-line.two { transform: rotate(-24deg); }

    .dna-dot {
        position: absolute;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: #00f5d4;
        box-shadow: 0 0 18px #00f5d4;
        animation: pulseDot 1.8s ease-in-out infinite;
    }

    .dna-dot.d1 { top: 18px; left: 44px; }
    .dna-dot.d2 { top: 48px; right: 38px; animation-delay: .2s; }
    .dna-dot.d3 { top: 82px; left: 34px; animation-delay: .4s; }
    .dna-dot.d4 { top: 116px; right: 46px; animation-delay: .6s; }
    .dna-dot.d5 { top: 145px; left: 60px; animation-delay: .8s; }

    .scan-line {
        height: 2px;
        width: 100%;
        background: linear-gradient(90deg, transparent, #00f5d4, transparent);
        animation: scanMove 2.8s ease-in-out infinite;
        opacity: 0.75;
        margin-top: 22px;
    }

    @keyframes slowSpin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    @keyframes pulseDot {
        0%, 100% { transform: scale(0.85); opacity: 0.65; }
        50% { transform: scale(1.25); opacity: 1; }
    }

    @keyframes scanMove {
        0% { transform: translateX(-100%); }
        50% { transform: translateX(0%); }
        100% { transform: translateX(100%); }
    }

    @keyframes cardFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-4px); }
    }
    </style>
    """, unsafe_allow_html=True)

def render_biotech_hero():
    st.markdown("""
    <div class="bio-hero">
        <div class="dna-wrap">
            <div class="dna-line one"></div>
            <div class="dna-line two"></div>
            <div class="dna-dot d1"></div>
            <div class="dna-dot d2"></div>
            <div class="dna-dot d3"></div>
            <div class="dna-dot d4"></div>
            <div class="dna-dot d5"></div>
        </div>
        <h1>BioPredict AI</h1>
        <p>AI-powered early disease risk prediction from blood reports, with organ-based analysis, biomarker comparison, risk scoring, and downloadable medical screening reports.</p>
        <div class="scan-line"></div>
    </div>
    """, unsafe_allow_html=True)

apply_biotech_theme()

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
    try: return float(val)
    except: return default

def get_int(val, default=0):
    try: return int(val)
    except: return default

def predict_disease(disease, input_values):
    info = models[disease]
    model = info["model"]
    features = info["features"]
    input_df = pd.DataFrame([input_values])[features]
    probability = model.predict_proba(input_df)[0]
    risk_percent = round(probability[1] * 100, 2)
    if risk_percent >= 70:
        return "HIGH RISK", risk_percent, "Please consult a physician immediately.", "red"
    elif risk_percent >= 40:
        return "MODERATE RISK", risk_percent, "Monitor your health and consult a doctor soon.", "orange"
    else:
        return "LOW RISK", risk_percent, "You appear healthy. Maintain a good lifestyle!", "green"

normal_ranges = {
    "Glucose": (70, 100), "BloodPressure": (60, 80),
    "BMI": (18.5, 24.9), "Insulin": (16, 166),
    "SkinThickness": (10, 30), "Age": (0, 120),
    "Pregnancies": (0, 10), "DiabetesPedigreeFunction": (0, 1),
    "chol": (125, 200), "trestbps": (90, 120),
    "thalach": (60, 100), "oldpeak": (0, 2),
    "Total_Bilirubin": (0.2, 1.2), "Direct_Bilirubin": (0, 0.3),
    "Alkaline_Phosphotase": (44, 147), "Alamine_Aminotransferase": (7, 56),
    "Aspartate_Aminotransferase": (10, 40), "Total_Protiens": (6, 8.3),
    "Albumin": (3.5, 5), "Albumin_and_Globulin_Ratio": (1, 2.5),
    "bp": (60, 80), "bgr": (70, 120), "bu": (7, 25),
    "sc": (0.6, 1.2), "sod": (135, 145), "pot": (3.5, 5),
    "hemo": (12, 17), "pcv": (36, 50), "wc": (4500, 11000), "rc": (4.5, 5.5),
}

def plot_risk_chart(input_values, disease):
    numeric_inputs = {k: v for k, v in input_values.items()
                     if isinstance(v, (int, float)) and k in normal_ranges}
    params = list(numeric_inputs.keys())
    values = list(numeric_inputs.values())
    colors = []
    normal_high = []
    for param, val in zip(params, values):
        low, high = normal_ranges[param]
        normal_high.append(high)
        colors.append('red' if val < low or val > high else 'green')
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Normal Range Max', x=params, y=normal_high,
                         marker_color='rgba(0,200,0,0.15)', showlegend=True))
    fig.add_trace(go.Bar(name='Your Value', x=params, y=values,
                         marker_color=colors, showlegend=True))
    fig.update_layout(
        title=f"{disease} - Your Values vs Normal Range",
        barmode="overlay",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=400
    )
    return fig

def generate_pdf(disease, input_values, risk_level, risk_percent, advice, rows):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(41, 128, 185)
    pdf.rect(0, 0, 210, 35, "F")
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
    pdf.cell(0, 12, f"  Risk Level: {risk_level}  |  Risk Score: {risk_percent}%", ln=True, fill=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, f"Advice: {advice}", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(52, 73, 94)
    pdf.cell(60, 9, "Parameter", border=1, fill=True)
    pdf.cell(40, 9, "Your Value", border=1, fill=True)
    pdf.cell(50, 9, "Normal Range", border=1, fill=True)
    pdf.cell(40, 9, "Status", border=1, fill=True, ln=True)
    pdf.set_font("Helvetica", "", 11)
    for row in rows:
        status = row["Status"].replace("🔴 ", "").replace("🟢 ", "").replace("🔵 ", "")
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
    pdf.multi_cell(0, 6, "DISCLAIMER: This report is generated by an AI screening tool and is NOT a substitute for professional medical advice. Always consult a qualified physician for proper diagnosis and treatment.")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmp.name)
    return tmp.name

# Header

render_biotech_hero()

disease = st.sidebar.selectbox("Select Disease to Predict",
    ["Diabetes", "Heart", "Liver", "Kidney"])
st.sidebar.markdown("---")
st.sidebar.info("Fill in the blood report values and click Predict!")

st.header(f"🔬 {disease} Risk Prediction")

if disease == "Diabetes":
    col1, col2 = st.columns(2)
    with col1:
        gender      = st.selectbox("Gender", ["Female", "Male"])
        pregnancies = st.text_input("Pregnancies", "1")
        glucose     = st.text_input("Glucose Level", "120")
        bp          = st.text_input("Blood Pressure", "70")
    with col2:
        skin        = st.text_input("Skin Thickness", "20")
        insulin     = st.text_input("Insulin", "80")
        bmi         = st.text_input("BMI", "25.0")
        dpf         = st.text_input("Diabetes Pedigree Function", "0.5")
        age         = st.text_input("Age", "30")
    input_values = {
        "Pregnancies": get_int(pregnancies),
        "Glucose": get_float(glucose),
        "BloodPressure": get_float(bp),
        "SkinThickness": get_float(skin),
        "Insulin": get_float(insulin),
        "BMI": get_float(bmi),
        "DiabetesPedigreeFunction": get_float(dpf),
        "Age": get_int(age)
    }

elif disease == "Heart":
    col1, col2 = st.columns(2)
    with col1:
        age      = st.text_input("Age", "50")
        sex      = st.selectbox("Sex", [0,1], format_func=lambda x: "Female" if x==0 else "Male")
        cp       = st.selectbox("Chest Pain Type (0-3)", [0,1,2,3])
        trestbps = st.text_input("Resting Blood Pressure", "120")
        chol     = st.text_input("Cholesterol", "200")
        fbs      = st.selectbox("Fasting Blood Sugar > 120", [0,1])
        restecg  = st.selectbox("Resting ECG (0-2)", [0,1,2])
    with col2:
        thalach  = st.text_input("Max Heart Rate", "150")
        exang    = st.selectbox("Exercise Induced Angina", [0,1])
        oldpeak  = st.text_input("ST Depression", "1.0")
        slope    = st.selectbox("Slope of ST (0-2)", [0,1,2])
        ca       = st.selectbox("Major Vessels (0-4)", [0,1,2,3,4])
        thal     = st.selectbox("Thal (0-3)", [0,1,2,3])
    input_values = {
        "age": get_int(age), "sex": sex, "cp": cp,
        "trestbps": get_float(trestbps), "chol": get_float(chol),
        "fbs": fbs, "restecg": restecg, "thalach": get_float(thalach),
        "exang": exang, "oldpeak": get_float(oldpeak),
        "slope": slope, "ca": ca, "thal": thal
    }

elif disease == "Liver":
    col1, col2 = st.columns(2)
    with col1:
        age        = st.text_input("Age", "40")
        gender     = st.selectbox("Gender", [0,1], format_func=lambda x: "Female" if x==0 else "Male")
        total_bili = st.text_input("Total Bilirubin", "1.0")
        direct_bili= st.text_input("Direct Bilirubin", "0.3")
        alk_phos   = st.text_input("Alkaline Phosphotase", "200")
    with col2:
        alt        = st.text_input("Alamine Aminotransferase", "30")
        ast        = st.text_input("Aspartate Aminotransferase", "30")
        total_prot = st.text_input("Total Proteins", "6.5")
        albumin    = st.text_input("Albumin", "3.5")
        ag_ratio   = st.text_input("Albumin/Globulin Ratio", "1.0")
    input_values = {
        "Age": get_int(age), "Gender": gender,
        "Total_Bilirubin": get_float(total_bili),
        "Direct_Bilirubin": get_float(direct_bili),
        "Alkaline_Phosphotase": get_float(alk_phos),
        "Alamine_Aminotransferase": get_float(alt),
        "Aspartate_Aminotransferase": get_float(ast),
        "Total_Protiens": get_float(total_prot),
        "Albumin": get_float(albumin),
        "Albumin_and_Globulin_Ratio": get_float(ag_ratio)
    }

elif disease == "Kidney":
    col1, col2, col3 = st.columns(3)
    with col1:
        gender = st.selectbox("Gender", ["Female", "Male"])
        age  = st.text_input("Age", "40")
        bp   = st.text_input("Blood Pressure", "80")
        sg   = st.text_input("Specific Gravity", "1.020")
        al   = st.text_input("Albumin (0-5)", "0")
        su   = st.text_input("Sugar (0-5)", "0")
        rbc  = st.selectbox("Red Blood Cells", [0,1], format_func=lambda x: "Abnormal" if x==0 else "Normal")
        pc   = st.selectbox("Pus Cells", [0,1], format_func=lambda x: "Abnormal" if x==0 else "Normal")
        pcc  = st.selectbox("Pus Cell Clumps", [0,1], format_func=lambda x: "Not Present" if x==0 else "Present")
    with col2:
        ba   = st.selectbox("Bacteria", [0,1], format_func=lambda x: "Not Present" if x==0 else "Present")
        bgr  = st.text_input("Blood Glucose Random", "120")
        bu   = st.text_input("Blood Urea", "40")
        sc   = st.text_input("Serum Creatinine", "1.2")
        sod  = st.text_input("Sodium", "138")
        pot  = st.text_input("Potassium", "4.5")
        hemo = st.text_input("Hemoglobin", "15.0")
        pcv  = st.text_input("Packed Cell Volume", "44")
    with col3:
        wc   = st.text_input("White Blood Cell Count", "8000")
        rc   = st.text_input("Red Blood Cell Count", "5.0")
        htn  = st.selectbox("Hypertension", [0,1], format_func=lambda x: "No" if x==0 else "Yes")
        dm   = st.selectbox("Diabetes Mellitus", [0,1], format_func=lambda x: "No" if x==0 else "Yes")
        cad  = st.selectbox("Coronary Artery Disease", [0,1], format_func=lambda x: "No" if x==0 else "Yes")
        appet= st.selectbox("Appetite", [0,1], format_func=lambda x: "Poor" if x==0 else "Good")
        pe   = st.selectbox("Pedal Edema", [0,1], format_func=lambda x: "No" if x==0 else "Yes")
        ane  = st.selectbox("Anemia", [0,1], format_func=lambda x: "No" if x==0 else "Yes")
    input_values = {
        "age": get_float(age), "bp": get_float(bp), "sg": get_float(sg),
        "al": get_float(al), "su": get_float(su), "rbc": rbc, "pc": pc,
        "pcc": pcc, "ba": ba, "bgr": get_float(bgr), "bu": get_float(bu),
        "sc": get_float(sc), "sod": get_float(sod), "pot": get_float(pot),
        "hemo": get_float(hemo), "pcv": get_float(pcv), "wc": get_float(wc),
        "rc": get_float(rc), "htn": htn, "dm": dm, "cad": cad,
        "appet": appet, "pe": pe, "ane": ane
    }

st.markdown("---")
if st.button(f"🔍 Predict {disease} Risk", use_container_width=True):
    risk_level, risk_percent, advice, color = predict_disease(disease, input_values)
    st.markdown("---")
    st.header("📊 Prediction Result")
    col1, col2 = st.columns(2)
    with col1:
        emoji = "🔴" if risk_level=="HIGH RISK" else "🟡" if risk_level=="MODERATE RISK" else "🟢"
        st.metric("Risk Level", f"{emoji} {risk_level}")
        st.metric("Risk Score", f"{risk_percent}%")
    with col2:
        st.progress(int(risk_percent))
        st.info(f"💡 {advice}")
    st.markdown("---")
    st.header("📈 Your Values vs Normal Range")
    fig = plot_risk_chart(input_values, disease)
    st.plotly_chart(fig, use_container_width=True)
    st.header("🔎 Parameter Analysis")
    numeric_inputs = {k: v for k, v in input_values.items()
                     if isinstance(v, (int, float)) and k in normal_ranges}
    rows = []
    for param, val in numeric_inputs.items():
        low, high = normal_ranges[param]
        if val < low: status = "🔵 Below Normal"
        elif val > high: status = "🔴 Above Normal"
        else: status = "🟢 Normal"
        rows.append({"Parameter": param, "Your Value": val,
                     "Normal Range": f"{low} - {high}", "Status": status})
    st.table(pd.DataFrame(rows))
    st.markdown("---")
    st.header("📄 Download Report")
    pdf_path = generate_pdf(disease, input_values, risk_level, risk_percent, advice, rows)
    with open(pdf_path, "rb") as f:
        st.download_button(
            label="⬇️ Download PDF Report",
            data=f,
            file_name=f"BioPredict_{disease}_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    st.markdown("---")
    st.warning("This is an AI screening tool only. Always consult a qualified physician.")

st.markdown("---")
st.markdown("**BioPredict AI** | Built with heart using Machine Learning")
