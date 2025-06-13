import streamlit as st
from ocr_pdf import ocr_pdf
import os
from datetime import datetime
from md_translate import setup_env, load_mbart_model, md_translate_to_html
from transform_html import convert_html_to_pdf_with_math_images

# 환경설정 (옵션)
setup_env("/mnt/t7/dnn/llm_practicing/.env")

# 모델 및 토크나이저 로드
MODEL_NAME = "aeolian83/mbart-en-ko-ptt-latex"
DEVICE = "cuda"  # or "cpu"

model, tokenizer = load_mbart_model(MODEL_NAME, device=DEVICE)

# 현재 스크립트의 절대 경로를 기준으로 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
HTML_DIR = os.path.join(BASE_DIR, "html")

# HTML 디렉토리가 없으면 생성
os.makedirs(HTML_DIR, exist_ok=True)

st.title("PDF OCR 및 마크다운 변환")

# 기존 HTML 파일 목록 가져오기
existing_html_files = []
if os.path.exists(HTML_DIR):
    for file in os.listdir(HTML_DIR):
        if file.endswith('.html'):
            file_path = os.path.join(HTML_DIR, file)
            existing_html_files.append((file, file_path))

# 기존 HTML 파일 선택 옵션
if existing_html_files:
    st.subheader("기존 HTML 파일 선택")
    selected_html = st.selectbox(
        "이전에 번역된 HTML 파일을 선택하세요",
        options=[file for file, _ in existing_html_files],
        format_func=lambda x: x
    )
    
    if selected_html:
        selected_html_path = next(path for file, path in existing_html_files if file == selected_html)
        with open(selected_html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # HTML 미리보기
        st.subheader("HTML 미리보기")
        st.components.v1.html(html_content, height=400, scrolling=True)
        
        # PDF 변환 버튼
        if st.button("선택한 HTML을 PDF로 변환"):
            with st.spinner("PDF 변환 중입니다..."):
                # PDF 파일 경로 설정
                output_pdf = os.path.join(HTML_DIR, f"{os.path.splitext(selected_html)[0]}.pdf")
                
                # HTML을 PDF로 변환
                convert_html_to_pdf_with_math_images(html_content, output_pdf, base_dir=os.path.join(BASE_DIR, "outputs"))
                
                # PDF 파일 다운로드 버튼
                with open(output_pdf, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    "PDF 다운로드",
                    pdf_bytes,
                    file_name=f"{os.path.splitext(selected_html)[0]}.pdf",
                    mime="application/pdf"
                )

# 기존 outputs 폴더의 마크다운 파일 목록 가져오기
existing_md_files = []
if os.path.exists(OUTPUTS_DIR):
    for folder in os.listdir(OUTPUTS_DIR):
        folder_path = os.path.join(OUTPUTS_DIR, folder)
        if os.path.isdir(folder_path):
            md_path = os.path.join(folder_path, "markdown", "output.md")
            if os.path.exists(md_path):
                existing_md_files.append((folder, md_path))

# 기존 마크다운 파일 선택 옵션
if existing_md_files:
    st.subheader("기존 마크다운 파일 선택")
    selected_folder = st.selectbox(
        "이전에 변환된 마크다운 파일을 선택하세요",
        options=[folder for folder, _ in existing_md_files],
        format_func=lambda x: x
    )
    
    if selected_folder:
        selected_md_path = next(path for folder, path in existing_md_files if folder == selected_folder)
        with open(selected_md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        
        # 변환된 md 파일 다운로드 버튼
        st.download_button("선택한 마크다운 다운로드", md_content, file_name="output.md")
        
        # 변환된 md 일부 미리보기
        st.subheader("마크다운 일부 미리보기")
        st.markdown(md_content[:2000])  # 앞 2000글자만 보여줌
        
        # 번역 버튼
        if st.button("선택한 파일 번역하기"):
            with st.spinner("번역 중입니다..."):
                # HTML로 변환
                html_content = md_translate_to_html(selected_md_path, model, tokenizer, device=DEVICE)
                st.success("번역 완료!")
                
                # HTML 파일 저장
                html_filename = f"{selected_folder}_translated.html"
                html_path = os.path.join(HTML_DIR, html_filename)
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                # 번역된 HTML 미리보기
                st.subheader("번역된 HTML 미리보기")
                st.components.v1.html(html_content, height=400, scrolling=True)
                
                # PDF 변환 버튼
                if st.button("PDF로 변환하기"):
                    with st.spinner("PDF 변환 중입니다..."):
                        # PDF 파일 경로 설정
                        output_pdf = os.path.join(HTML_DIR, f"{os.path.splitext(html_filename)[0]}.pdf")
                        
                        # HTML을 PDF로 변환
                        convert_html_to_pdf_with_math_images(html_content, output_pdf, base_dir=os.path.join(OUTPUTS_DIR, selected_folder, "images"))
                        
                        # PDF 파일 다운로드 버튼
                        with open(output_pdf, "rb") as f:
                            pdf_bytes = f.read()
                        st.download_button(
                            "번역된 PDF 다운로드",
                            pdf_bytes,
                            file_name=f"{os.path.splitext(html_filename)[0]}.pdf",
                            mime="application/pdf"
                        )

# 새로운 PDF 파일 업로드 섹션
st.subheader("새로운 PDF 파일 업로드")
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")

# 세션 상태 초기화
if 'pdf_bytes' not in st.session_state:
    st.session_state.pdf_bytes = None
if 'pdf_file_name' not in st.session_state:
    st.session_state.pdf_file_name = None

# 파일이 업로드되면 세션 상태에 저장
if uploaded_file:
    st.session_state.pdf_bytes = uploaded_file.read()
    st.session_state.pdf_file_name = uploaded_file.name
    st.success(f"파일 '{uploaded_file.name}'이(가) 업로드되었습니다.")

# OCR 처리 버튼
if st.session_state.pdf_bytes is not None:
    if st.button("OCR 처리 시작"):
        # 파일명에서 확장자 제거
        base_filename = os.path.splitext(st.session_state.pdf_file_name)[0]
        # 현재 날짜와 시간으로 폴더명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(OUTPUTS_DIR, f"{base_filename}_{timestamp}")
        
        # 출력 디렉토리 생성
        output_img_dir = os.path.join(output_dir, "images")
        output_md_dir = os.path.join(output_dir, "markdown")
        os.makedirs(output_img_dir, exist_ok=True)
        os.makedirs(output_md_dir, exist_ok=True)

        with st.spinner("OCR 처리 중입니다..."):
            md_path = ocr_pdf(
                st.session_state.pdf_bytes,
                st.session_state.pdf_file_name,
                output_img_dir,
                output_md_dir,
                md_filename="output.md"
            )
        st.success("OCR 및 변환 완료!")

        # 변환된 md 파일 다운로드 버튼
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        st.download_button("변환된 마크다운 다운로드", md_content, file_name="output.md")

        # 변환된 md 일부 미리보기
        st.subheader("마크다운 일부 미리보기")
        st.markdown(md_content[:2000])  # 앞 2000글자만 보여줌

        # 번역 버튼
        if st.button("새 파일 번역하기"):
            with st.spinner("번역 중입니다..."):
                # HTML로 변환
                html_content = md_translate_to_html(md_path, model, tokenizer, device=DEVICE)
                st.success("번역 완료!")
                
                # HTML 파일 저장
                html_filename = f"{base_filename}_{timestamp}_translated.html"
                html_path = os.path.join(HTML_DIR, html_filename)
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                # 번역된 HTML 미리보기
                st.subheader("번역된 HTML 미리보기")
                st.components.v1.html(html_content, height=400, scrolling=True)
                
                # PDF 변환 버튼
                if st.button("새 파일 PDF로 변환하기"):
                    with st.spinner("PDF 변환 중입니다..."):
                        # PDF 파일 경로 설정
                        output_pdf = os.path.join(HTML_DIR, f"{os.path.splitext(html_filename)[0]}.pdf")
                        
                        # HTML을 PDF로 변환
                        convert_html_to_pdf_with_math_images(html_content, output_pdf, base_dir=output_img_dir)
                        
                        # PDF 파일 다운로드 버튼
                        with open(output_pdf, "rb") as f:
                            pdf_bytes = f.read()
                        st.download_button(
                            "번역된 PDF 다운로드",
                            pdf_bytes,
                            file_name=f"{os.path.splitext(html_filename)[0]}.pdf",
                            mime="application/pdf"
                        )
