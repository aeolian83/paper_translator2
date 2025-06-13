# ocr_pdf.py

import os
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod

def ocr_pdf(
    pdf_bytes: bytes,
    pdf_file_name: str,
    output_img_dir: str,
    output_md_dir: str,
    md_filename: str = "mdcontent_1.md"
) -> str:
    """
    PDF 파일 바이트와 파일명, 저장경로를 받아 OCR 수행 후 md 파일을 저장하고 경로를 반환
    """
    # 환경 준비
    if not os.path.exists(output_img_dir):
        os.makedirs(output_img_dir, exist_ok=True)
    if not os.path.exists(output_md_dir):
        os.makedirs(output_md_dir, exist_ok=True)

    image_writer = FileBasedDataWriter(output_img_dir)
    md_writer = FileBasedDataWriter(output_md_dir)

    # 데이터셋 생성 및 분류
    ds = PymuDocDataset(pdf_bytes)
    if ds.classify() == SupportedPdfParseMethod.OCR:
        infer_result = ds.apply(doc_analyze, ocr=True)
        pipe_result = infer_result.pipe_ocr_mode(image_writer)
    else:
        infer_result = ds.apply(doc_analyze, ocr=False)
        pipe_result = infer_result.pipe_txt_mode(image_writer)

    # 마크다운 저장
    md_save_path = os.path.join(output_md_dir, md_filename)
    pipe_result.dump_md(md_writer, md_save_path, output_img_dir)
    return md_save_path
