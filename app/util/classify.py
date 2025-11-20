from transformers import pipeline, XLMRobertaTokenizer

from functools import lru_cache

MODEL_NAME = "joeddav/xlm-roberta-large-xnli"

@lru_cache(maxsize=1)
def get_classifier():
    # explicitly load slow tokenizer
    tokenizer = XLMRobertaTokenizer.from_pretrained(MODEL_NAME, use_fast=False)

    return pipeline(
        "zero-shot-classification",
        model=MODEL_NAME,
        tokenizer=tokenizer
    )


# Candidate subject labels
candidate_labels = [
    "Câu hỏi về Toán học",
    "Câu hỏi về Vật lý",
    "Câu hỏi về Hóa học",
    "Câu hỏi về Sinh học, động vật và thực vật",
    "Câu hỏi về Lịch sử",
    "Câu hỏi về Nghệ thuật, văn hóa",
    "Câu hỏi về Địa lý",
    "Câu hỏi về Văn học",
    "Câu hỏi về Tiếng Anh"
]

# Confidence threshold for fallback
CONFIDENCE_THRESHOLD = 0.5
FALLBACK_LABEL = "Kiến thức chung"

def classify_question(question):
    classifier = get_classifier()
    r = classifier(question, candidate_labels, multi_label=False)
    best_label, best_score = r['labels'][0], r['scores'][0]

    # Apply fallback if confidence too low
    # if best_score < CONFIDENCE_THRESHOLD:
    #     final_label = FALLBACK_LABEL
    #     final_score = best_score
    # else:
    #     final_label = best_label
    #     final_score = best_score

    print(f"\nCâu hỏi: {question}")
    print(f"-> Chủ đề ban đầu: {best_label} (độ tin cậy: {best_score:.2f})")
    # print(f"-> Chủ đề dự đoán: {final_label} (độ tin cậy: {final_score:.2f})")

    # ✅ FIX HERE
    return best_label 


