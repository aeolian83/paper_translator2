import os
from tqdm import tqdm
import torch
from transformers import MBartForConditionalGeneration, MBart50Tokenizer

from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.footnote import footnote_plugin

# 환경변수 세팅 함수 (옵션)
def setup_env(env_path=None):
    if env_path:
        from dotenv import load_dotenv
        load_dotenv(env_path)

# 모델 및 토크나이저 로드 함수
def load_mbart_model(model_name, device='cuda'):
    tokenizer = MBart50Tokenizer.from_pretrained(model_name, src_lang="en_XX", tgt_lang="ko_KR")
    model = MBartForConditionalGeneration.from_pretrained(model_name, device_map="auto")
    model = model.to(device)
    return model, tokenizer

# 마크다운 파서 생성 함수
def get_md_parser():
    md = (
        MarkdownIt('commonmark', {'breaks':True,'html':True})
        .use(front_matter_plugin)
        .use(footnote_plugin)
        .enable('table')
    )
    return md

# 배치 번역 함수
def translate_batch(text_list, model, tokenizer, device="cuda", max_length=512):
    if not text_list:
        return []
    inputs = tokenizer(text_list, return_tensors="pt", padding=True, truncation=True, max_length=max_length).to(device)
    with torch.no_grad():
        generated_tokens = model.generate(
            **inputs,
            forced_bos_token_id=tokenizer.lang_code_to_id["ko_KR"],
            max_length=max_length,
            num_beams=5,
        )
    translated = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
    return translated

# 토큰의 text만 번역해서 교체하는 함수
def replace_text_tokens(tokens, model, tokenizer, device="cuda", batch_size=10):
    text_tokens = []

    def collect_text_tokens(tokens):
        for token in tokens:
            if token.type == "text":
                text_tokens.append(token)
            if hasattr(token, 'children') and token.children:
                collect_text_tokens(token.children)
    collect_text_tokens(tokens)

    all_texts = [t.content for t in text_tokens]
    translated_texts = []
    for i in tqdm(range(0, len(all_texts), batch_size), desc="Translating"):
        batch = all_texts[i:i+batch_size]
        translated_batch = translate_batch(batch, model, tokenizer, device=device)
        translated_texts.extend(translated_batch)

    for token, new_text in zip(text_tokens, translated_texts):
        token.content = new_text

# 메인 파이프라인 함수 (md 경로 → html 변환까지)
def md_translate_to_html(md_path, model, tokenizer, device="cuda", batch_size=10):
    md = get_md_parser()
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    tokens = md.parse(md_text)
    replace_text_tokens(tokens, model, tokenizer, device=device, batch_size=batch_size)
    html = md.renderer.render(tokens, md.options, {})
    return html
