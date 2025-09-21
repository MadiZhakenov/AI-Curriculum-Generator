import fitz
import os
import google.generativeai as genai
from dotenv import load_dotenv
from tqdm import tqdm

SOURCE_PDF_DIR = "pdfs/"
DISTILLED_TXT_DIR = "final_docs/"
CHUNK_SIZE = 7000

def setup_distiller():
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("Ошибка: API ключ GEMINI не найден.")
        return None
    genai.configure(api_key=gemini_api_key)
    return genai.GenerativeModel("gemini-1.5-flash") 

def extract_text_from_pdf(pdf_path):
    try:
        with fitz.open(pdf_path) as doc:
            full_text = "".join(page.get_text() for page in doc)
        return full_text
    except Exception as e:
        print(f"Не удалось прочитать {pdf_path}: {e}")
        return ""

def distill_chunk(model, chunk):
    """Отправляет кусок текста в Gemini для очистки и структурирования."""
    
    prompt = f"""
ТЫ — ЭКСПЕРТ-МЕТОДИСТ, который конспектирует объемный педагогический документ.

ТВОЯ ЗАДАЧА: Прочитай предоставленный фрагмент текста. Выдели и оставь ТОЛЬКО самую важную, конкретную и практическую информацию. Удали всю "воду", общие рассуждения, приветствия, вступления и повторяющиеся фразы.

ТРЕБОВАНИЯ К РЕЗУЛЬТАТУ:
1.  **КОНКРЕТИКА:** Сохраняй только конкретные названия тем, игр, упражнений, целей, навыков, методических приемов и требований.
2.  **СТРУКТУРА:** Если в исходном тексте есть заголовки, списки или таблицы, постарайся сохранить эту структуру.
3.  **КРАТКОСТЬ:** Переформулируй длинные предложения в более короткие и емкие тезисы.
4.  **НИЧЕГО ЛИШНЕГО:** Не добавляй никаких собственных комментариев. Твоя задача — только "выжать" суть из исходного текста.

ИСХОДНЫЙ ФРАГМЕНТ ТЕКСТА:
---
{chunk}
---

ПРЕДОСТАВЬ СЖАТЫЙ КОНСПЕКТ ЭТОГО ФРАГМЕНТА:
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Ошибка при обращении к Gemini: {e}")
        return ""

if __name__ == "__main__":
    generative_model = setup_distiller()
    if generative_model:
        if not os.path.exists(DISTILLED_TXT_DIR):
            os.makedirs(DISTILLED_TXT_DIR)

        pdf_files = [f for f in os.listdir(SOURCE_PDF_DIR) if f.endswith(".pdf")]
        
        print(f"Начинаю дистилляцию {len(pdf_files)} PDF документов...")

        for filename in tqdm(pdf_files, desc="Обработка PDF"):
            pdf_path = os.path.join(SOURCE_PDF_DIR, filename)
            
            full_text = extract_text_from_pdf(pdf_path)
            if not full_text:
                continue

            chunks = [full_text[i:i+CHUNK_SIZE] for i in range(0, len(full_text), CHUNK_SIZE)]
            
            distilled_content = []
            
            for chunk in tqdm(chunks, desc=f"Дистилляция '{filename}'", leave=False):
                distilled_chunk = distill_chunk(generative_model, chunk)
                distilled_content.append(distilled_chunk)
            
            output_txt_path = os.path.join(DISTILLED_TXT_DIR, f"{os.path.splitext(filename)[0]}.txt")
            with open(output_txt_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(distilled_content))

        print(f"\nГОТОВО! Все документы дистиллированы и сохранены в папку: '{DISTILLED_TXT_DIR}'")