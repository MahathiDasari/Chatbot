
import streamlit as st
import pandas as pd
import google.generativeai as genai
import requests
import pdfplumber
from streamlit_lottie import st_lottie
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\mdasari1\Downloads\tesseract.exe"
POPPLER_PATH = r"C:\Users\mdasari1\Downloads\Release-25.07.0-0\poppler-25.07.0\Library\bin"

st.set_page_config(page_title="Smart Chatbot Assistant", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(to right, #f8fafc, #f1f5f9);
    }
    .title {
        font-size: 2.2rem; font-weight: 700; color: #1E293B;
        text-align: center; margin-bottom: 5px;
    }
    .subtitle {
        text-align: center; color: #64748B; font-size: 1.1rem; margin-bottom: 25px;
    }
    .stButton>button {
        background-color: #2563EB; color: white; border: none;
        border-radius: 8px; padding: 8px 16px; font-weight: 600; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #1E40AF; }
    [data-testid="stSidebar"] {
        background-color: #F1F5F9; border-right: 2px solid #E2E8F0;
    }
    </style>
""", unsafe_allow_html=True)

genai.configure(api_key="AIzaSyCriVlGhm5m536SVr-k0Fcd893S6vj6zQw")
model = genai.GenerativeModel("gemini-2.5-flash")

def load_lottie(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

chat_anim = load_lottie("https://assets9.lottiefiles.com/packages/lf20_ydo1amjm.json")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st_lottie(chat_anim, height=180, key="anim")

st.markdown('<div class="title">🤖 Chatbot</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Ask anything from your Excel or PDF data</div>', unsafe_allow_html=True)

if 'data_context' not in st.session_state:
    st.session_state.data_context = ""
if 'messages' not in st.session_state:
    st.session_state.messages = []

st.subheader("📁 Upload Your Knowledge Base")
file_type = st.radio("Select File Type", ["Excel", "PDF"], horizontal=True)

uploaded_file = st.file_uploader(
    "Upload File",
    type=["xlsx", "xls", "pdf"],
    help="Upload your Excel or PDF file as knowledge base"
)

def extract_excel_data(file):
    excel_file = pd.ExcelFile(file)
    context = "Here is the data from the Excel file:\n\n"
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(file, sheet_name=sheet_name)
        context += f"### Sheet: {sheet_name}\n"
        context += f"Columns: {', '.join(df.columns)}\n"
        context += f"Rows: {len(df)}\n\n"
        context += df.head(1000).to_string(index=False)
        context += "\n\n---\n\n"
    return context

def extract_pdf_data(file):
    text = ""
    try:
        # Try reading selectable text first
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        # If text is still empty, use OCR for scanned PDFs
        if not text.strip():
            st.warning("⚠️ Detected scanned PDF — performing OCR. This may take a few seconds...")
            file.seek(0)
            images = convert_from_bytes(file.read(), poppler_path=POPPLER_PATH)

            ocr_text = ""
            for i, image in enumerate(images):
                ocr_result = pytesseract.image_to_string(image)
                ocr_text += f"\n--- Page {i+1} ---\n{ocr_result}"

            text = ocr_text

        return f"Here is the extracted text from the PDF:\n\n{text[:20000]}"

    except Exception as e:
        return f"Error extracting PDF content: {e}"

if uploaded_file:
    try:
        if file_type == "Excel" and uploaded_file.name.endswith((".xlsx", ".xls")):
            st.session_state.data_context = extract_excel_data(uploaded_file)
            st.success("✅ Excel data loaded successfully!")
        elif file_type == "PDF" and uploaded_file.name.endswith(".pdf"):
            st.session_state.data_context = extract_pdf_data(uploaded_file)
            st.success("✅ PDF data extracted successfully!")
        else:
            st.error("⚠️ Please upload a file matching the selected type.")
    except Exception as e:
        st.error(f"Error loading file: {e}")


if st.session_state.data_context:
    st.info("💡 You can now chat with your uploaded data!")

    # Display previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("💭 Ask a question about your data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing... 🧠"):
                try:
                    full_prompt = f"""{st.session_state.data_context}

                    Based on the uploaded data, answer the following question:
                    {prompt}

                   Provide a clear, detailed answer based on the data. Reference specific values, names, dates, or calculations as needed.give me the answer straight forward dont give lengthy answers"""
                    response = model.generate_content(full_prompt)
                    answer = response.text
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Error: {e}")
else:
    st.warning("👆 Upload an Excel or PDF file to start chatting!")

with st.sidebar:
    st.header("⚙️ Options")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    if st.button("🔄 Clear Data"):
        st.session_state.data_context = ""
        st.session_state.messages = []
        st.rerun()
