def paper_writer_instruction(term, arxiv_summary):
    instruction = f"""As an AI paper writer, create three sentences about {term} that form a coherent paragraph, based on this reference.

[TERM]={term}

<reference>
{arxiv_summary}
</reference>

Instructions:
1. Directly cite content from the reference in each sentence.
2. Use an academic tone appropriate for research.
3. Include specific methodologies, results, or key concepts from the reference.
4. Be sure to include at least one sentence that contains a mathematical expression written in LaTeX syntax.
5. Highlight the research's importance or innovation.
6. Ensure the three sentences flow logically and form a cohesive paragraph.
7. Avoid starting sentences with "The study", "Ultimately", "This study explores", or "In this field."
8. Write in English only.

Output Format:
english: Three sentences using term {term} that form a coherent paragraph.
    """
    return instruction


def translator_instruction(term):
    instruction = f"""You are a professor specializing in Physics, proficient in both Korean and English. Your task is to translate English physics content into Korean, adhering to specific guidelines.

[TERM]={term}

<translation guideline>
1. CRITICAL: All technical terms, including [TERM], MUST be translated using the format: Korean term(English term). Example: 적대적 훈련(adversarial training).
2. For acronyms, use the following format: Korean full term(English full term, acronym). Example: 계층적으로 조직된 경량 다중 탐지 시스템(hierarchically organized light-weight multiple detector system, HOLMES).
3. Maintain an academic tone and ensure technical accuracy in your translation.
4. Produce natural-sounding Korean translation while accurately conveying the original meaning.
5. Do not use the '*' symbol in your response.
6. Change all letters within parentheses in Korean sentences to lowercase.
7. Ensure consistency in terminology and parenthetical translation throughout the text.
8. When translating equations or mathematical expressions, maintain the standard notation used in Korean academic physics papers.
9. Mathematical expressions written in LaTeX syntax must be displayed exactly as they are, without any modifications.
</translation guideline>

## Example Output
korean: 앙상블 학습(context of ensemble learning)에서 적응형 신경 프레임워크(adaptive neural frameworks)의 개발은 다양한 벤치마크 데이터셋(benchmark datasets)에서 광범위한 실험 결과로 입증된 바와 같이 심층 신경망(deep neural networks)의 성능을 크게 향상시킵니다. 이러한 적응형 신경 프레임워크(adaptive neural frameworks)를 활용함으로써 연구자들은 특징을 지능적으로 융합하여 더 차별화되고 효과적인 표현을 생성할 수 있으며, 이에 따라 모델의 일반화 능력을 향상시킬 수 있습니다. 결과적으로, 적응형 신경 프레임워크(adaptive neural frameworks)는 전통적인 특징 융합 기법(traditional feature fusion techniques)을 능가할 뿐만 아니라 이미지 분류(image classification), 객체 탐지(object detection), 자연어 처리(natural language processing, NLP), 그래프 기반 학습(graph-based learning) 작업을 포함한 여러 도메인에서 광범위한 적용 가능성을 보여줍니다.

## Output Format
korean: Sentences using {term} with proper parenthetical translation.

Note: Provide only the Korean translation as output. Do not include the original English sentence.
    """
    return instruction


def evaluator_instruction(term):
    instruction = f"""You are an expert evaluating English to Korean translations of Physics research papers, with a specific focus on proper parenthetical translations of technical terms.

<criteria>
1. The format for parenthetical translations must be: Korean term(English term).
2. The specific term {term} MUST ALWAYS be enclosed in parentheses.
3. Parentheses should be properly placed, ensuring consistency in parenthesizing across the entire sentence.
4. The translation should convey the original meaning precisely and read naturally and smoothly in Korean.
</criteria>

<instructions>
1. Change all letters within parentheses in Korean sentences to lowercase.
2. Evaluate the Korean translation of the provided English sentences.
3. Check the consistency and correctness of parenthesization.
4. Provide a score (0-10) based on the correctness and consistency of parenthesization as Korean term(English term).
5. Offer specific improvement suggestions if the score is less than 10.
6. Do not use the '*' symbol in your response.
7. Do not include any supplementary explanations.
8. Adhere strictly to the output format provided.
</instructions>

## Output Format
english: [English sentences using term "{term}"]
korean: [Korean translation sentences using parentheses]
score: [X/10]
terms_check: [{term}: Yes/No]
parentheses_count: [Number of parentheses pairs in the Korean translation sentences]
suggestions: [Suggest capturing the original meaning and nuances in the translation sentences while adjusting the structure for natural flow and grammar]
    """
    return instruction
