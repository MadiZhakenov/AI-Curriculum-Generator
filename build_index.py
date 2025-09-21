import os
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from tqdm import tqdm

SOURCE_DATA_FOLDER = "final_docs/"
FAISS_INDEX_PATH = "faiss_index.bin"
DOCS_PKL_PATH = "docs.pkl"

def read_all_text_files(folder_path):

    all_texts = []
    print(f"Чтение текстовых файлов из папки '{folder_path}'...")
    filenames = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    
    for filename in tqdm(filenames, desc="Чтение файлов"):
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                doc = Document(page_content=text, metadata={"source": filename})
                all_texts.append(doc)
        except Exception as e:
            print(f"Не удалось прочитать файл {filename}: {e}")
            
    print(f"Успешно прочитано {len(all_texts)} документов.")
    return all_texts

def main():

    raw_documents = read_all_text_files(SOURCE_DATA_FOLDER)
    if not raw_documents:
        print("Не найдено текстовых файлов для индексации. Завершение работы.")
        return

    print("\nРазбиваю документы на чанки...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500, 
        chunk_overlap=150,
        length_function=len,
    )
    chunked_documents = text_splitter.split_documents(raw_documents)
    print(f"Документы разбиты на {len(chunked_documents)} чанков.")

    print("\nСоздаю эмбеддинги для каждого чанка...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    chunk_texts = [doc.page_content for doc in chunked_documents]
    embeddings = model.encode(chunk_texts, show_progress_bar=True)
    
    print(f"Создано {len(embeddings)} эмбеддингов.")
    print("\nСоздаю и наполняю индекс FAISS...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype('float32'))
    
    print(f"Индекс FAISS создан. В нем {index.ntotal} векторов.")

    print("\nСохраняю результаты...")
    try:
        faiss.write_index(index, FAISS_INDEX_PATH)
        print(f"- Индекс успешно сохранен в '{FAISS_INDEX_PATH}'")
        
        with open(DOCS_PKL_PATH, "wb") as f:
            pickle.dump(chunked_documents, f)
        print(f"- Чанки успешно сохранены в '{DOCS_PKL_PATH}'")
            
        print("\nПРОЦЕСС ИНДЕКСАЦИИ УСПЕШНО ЗАВЕРШЕН!")
        print("Теперь ваша база знаний готова к работе с main_generator.py")

    except Exception as e:
        print(f"Произошла ошибка при сохранении файлов: {e}")


if __name__ == "__main__":
    main()