import re
from pathlib import Path
from weasyprint import HTML, CSS
from bs4 import BeautifulSoup
import base64
import requests
from urllib.parse import quote
import tempfile
import os

def html_to_pdf_with_weasyprint(html_content, output_pdf, base_dir=None, render_math=True):
    """
    WeasyPrint를 사용해 HTML을 LaTeX 수식과 이미지 포함하여 PDF로 변환
    
    Args:
        html_content (str): 변환할 HTML 내용
        output_pdf (str): 출력 PDF 파일 경로
        base_dir (str): 이미지 파일의 기본 디렉토리
        render_math (bool): LaTeX 수식을 이미지로 렌더링할지 여부
    """
    
    # BeautifulSoup으로 HTML 파싱
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # LaTeX 수식을 이미지로 변환 (선택사항)
    if render_math:
        soup = convert_latex_to_images_in_soup(soup)
    
    # 이미지 경로 수정
    if base_dir:
        soup = fix_image_paths_in_soup(soup, Path(base_dir))
    
    # 완전한 HTML 생성
    full_html = create_complete_html(str(soup))
    
    # CSS 스타일 정의
    css = create_pdf_css()
    
    # WeasyPrint로 PDF 생성
    try:
        HTML(string=full_html).write_pdf(output_pdf, stylesheets=[css])
        print(f"PDF 생성 완료: {output_pdf}")
    except Exception as e:
        print(f"PDF 생성 중 오류 발생: {e}")
        # 디버그용 HTML 파일 저장
        with open(output_pdf.replace('.pdf', '_debug.html'), 'w', encoding='utf-8') as f:
            f.write(full_html)
        raise

def convert_latex_to_images_in_soup(soup):
    """HTML soup에서 LaTeX 수식을 이미지로 변환"""
    
    # 텍스트 노드에서 LaTeX 패턴 찾기
    def process_text_node(text):
        # 블록 수식 처리: $$...$$
        text = re.sub(r'\$\$([^$]+?)\$\$', lambda m: create_math_image_tag(m.group(1), display=True), text, flags=re.DOTALL)
        
        # 인라인 수식 처리: $...$
        text = re.sub(r'\$([^$\n]+?)\$', lambda m: create_math_image_tag(m.group(1), display=False), text)
        
        return text
    
    # 모든 텍스트 노드 처리
    for element in soup.find_all(text=True):
        if element.parent.name not in ['script', 'style', 'code', 'pre']:
            new_text = process_text_node(str(element))
            if new_text != str(element):
                # 새로운 HTML로 교체
                new_soup = BeautifulSoup(new_text, 'html.parser')
                element.replace_with(new_soup)
    
    return soup

def create_math_image_tag(latex_code, display=False):
    """LaTeX 코드를 이미지 태그로 변환"""
    try:
        # CodeCogs API 사용 (무료)
        encoded_latex = quote(latex_code.strip())
        
        if display:
            # 블록 수식
            url = f"https://latex.codecogs.com/svg.latex?\\Large&space;{encoded_latex}"
            style = "display: block; margin: 20px auto; text-align: center;"
        else:
            # 인라인 수식
            url = f"https://latex.codecogs.com/svg.latex?{encoded_latex}"
            style = "display: inline; vertical-align: middle; margin: 0 2px;"
        
        return f'<img src="{url}" alt="{latex_code}" style="{style}" class="math-formula">'
    
    except Exception as e:
        print(f"LaTeX 수식 변환 실패: {latex_code} - {e}")
        # 실패시 코드 블록으로 표시
        return f'<code class="math-fallback">{latex_code}</code>'

def render_latex_to_svg_local(latex_code):
    """로컬에서 LaTeX을 SVG로 렌더링 (matplotlib 사용)"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # GUI 백엔드 사용 안함
        
        fig, ax = plt.subplots(figsize=(1, 0.5))
        ax.text(0.5, 0.5, f'${latex_code}$', 
                transform=ax.transAxes, 
                fontsize=14, 
                ha='center', va='center')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # SVG로 저장
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as tmp:
            plt.savefig(tmp.name, format='svg', bbox_inches='tight', 
                       transparent=True, pad_inches=0.02)
            plt.close()
            
            # SVG 파일을 base64로 인코딩
            with open(tmp.name, 'rb') as f:
                svg_data = base64.b64encode(f.read()).decode()
            
            os.unlink(tmp.name)  # 임시 파일 삭제
            
            return f"data:image/svg+xml;base64,{svg_data}"
    
    except ImportError:
        print("matplotlib이 설치되지 않음. 온라인 렌더링을 사용합니다.")
        return None
    except Exception as e:
        print(f"로컬 LaTeX 렌더링 실패: {e}")
        return None

def fix_image_paths_in_soup(soup, base_dir):
    """HTML soup에서 이미지 경로를 수정"""
    for img in soup.find_all('img'):
        src = img.get('src')
        if not src:
            continue
            
        # 이미 절대 URL인 경우 스킵
        if src.startswith(('http://', 'https://', 'data:', 'file://')):
            continue
            
        # 상대 경로를 절대 경로로 변환
        img_path = (base_dir / src).resolve()
        if img_path.exists():
            img['src'] = img_path.as_uri()
        else:
            print(f"이미지 파일을 찾을 수 없음: {img_path}")
            # 대체 이미지 또는 경고 표시
            img['src'] = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuydtOuvuOyngCDsl4Toy6HquLg8L3RleHQ+PC9zdmc+'
            img['alt'] = f"이미지 없음: {src}"
    
    return soup

def create_complete_html(body_content):
    """완전한 HTML 문서 생성"""
    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="utf-8">
        <title>문서</title>
    </head>
    <body>
        {body_content}
    </body>
    </html>
    """

def create_pdf_css():
    """PDF용 CSS 스타일 생성"""
    return CSS(string="""
        @page {
            size: A4;
            margin: 2cm;
        }
        
        body {
            font-family: 'Times New Roman', 'DejaVu Serif', serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #333;
        }
        
        h1 {
            font-size: 18pt;
            font-weight: bold;
            margin: 24pt 0 12pt 0;
            color: #000;
            page-break-after: avoid;
        }
        
        h2 {
            font-size: 16pt;
            font-weight: bold;
            margin: 20pt 0 10pt 0;
            color: #000;
            page-break-after: avoid;
        }
        
        h3 {
            font-size: 14pt;
            font-weight: bold;
            margin: 16pt 0 8pt 0;
            color: #000;
            page-break-after: avoid;
        }
        
        p {
            margin: 12pt 0;
            text-align: justify;
            orphans: 2;
            widows: 2;
        }
        
        img {
            max-width: 100%;
            height: auto;
            page-break-inside: avoid;
        }
        
        .math-formula {
            vertical-align: middle;
        }
        
        .math-fallback {
            font-family: 'Courier New', monospace;
            background-color: #f4f4f4;
            padding: 2pt 4pt;
            border-radius: 3pt;
            color: #d00;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 12pt 0;
            page-break-inside: avoid;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8pt;
            text-align: left;
        }
        
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        
        code {
            font-family: 'Courier New', monospace;
            font-size: 10pt;
            background-color: #f4f4f4;
            padding: 2pt 4pt;
            border-radius: 3pt;
        }
        
        pre {
            font-family: 'Courier New', monospace;
            font-size: 10pt;
            background-color: #f4f4f4;
            padding: 12pt;
            border-radius: 6pt;
            overflow-x: auto;
            margin: 12pt 0;
            page-break-inside: avoid;
        }
    """)

def simple_latex_to_text(latex_code):
    """간단한 LaTeX을 일반 텍스트로 변환 (fallback)"""
    # 기본적인 LaTeX 명령어 처리
    replacements = {
        r'\\frac\{([^}]*)\}\{([^}]*)\}': r'(\1)/(\2)',
        r'\\sqrt\{([^}]*)\}': r'√(\1)',
        r'\\int': '∫',
        r'\\sum': '∑',
        r'\\prod': '∏',
        r'\\alpha': 'α',
        r'\\beta': 'β',
        r'\\gamma': 'γ',
        r'\\delta': 'δ',
        r'\\epsilon': 'ε',
        r'\\pi': 'π',
        r'\\sigma': 'σ',
        r'\\theta': 'θ',
        r'\\lambda': 'λ',
        r'\\mu': 'μ',
        r'\\infty': '∞',
        r'\^(\w)': r'^\1',
        r'_(\w)': r'_\1',
    }
    
    result = latex_code
    for pattern, replacement in replacements.items():
        result = re.sub(pattern, replacement, result)
    
    return result

# 메인 함수들
def convert_html_to_pdf_simple(html_content, output_pdf, base_dir=None):
    """간단한 변환 (수식을 텍스트로)"""
    html_to_pdf_with_weasyprint(html_content, output_pdf, base_dir, render_math=False)

def convert_html_to_pdf_with_math_images(html_content, output_pdf, base_dir=None):
    """수식을 이미지로 렌더링하여 변환"""
    html_to_pdf_with_weasyprint(html_content, output_pdf, base_dir, render_math=True)

    
