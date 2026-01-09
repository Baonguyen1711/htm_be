import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .gemini import prompting
import json
import re
CANDIDATE_LABELS = [
    "Toán học",
    "Vật lý",
    "Hóa học",
    "Sinh học, động vật và thực vật",
    "Lịch sử",
    "Nghệ thuật, văn hóa",
    "Địa lý",
    "Văn học",
    "Tiếng Anh"
]
def classify_questions_batch(questions: list[str]) -> list[str]:
    """
    Nhận vào list câu hỏi
    Trả về list category cùng thứ tự
    """

    if not questions:
        return []

    # 1️⃣ Build prompt
    prompt = f"""
- Với mỗi câu hỏi dưới đây, hãy gán CHÍNH XÁC 1 chủ đề
- Chỉ được chọn từ danh sách sau:
{json.dumps(CANDIDATE_LABELS, ensure_ascii=False)}

output:
- Trả về JSON array
- Mỗi phần tử tương ứng với 1 câu hỏi
- KHÔNG giải thích
- KHÔNG markdown

Ví dụ:
["Toán học", "Vật lý"]

Danh sách câu hỏi:
"""

    for i, q in enumerate(questions, start=1):
        prompt += f"{i}. {q}\n"
    logger.info(f"prompt{prompt}")

    # 2️⃣ Gọi Gemini
    raw = prompting(prompt)
    logger.info(f"raw {raw}")
    # 3️⃣ Parse kết quả
    try:
        clean = re.sub(r"```json|```", "", raw).strip()
        labels = json.loads(clean)
        logger.info(f"labels{labels}")

        # fallback nếu length không khớp
        if len(labels) != len(questions):
            raise ValueError("Length mismatch")

        return labels

    except Exception as e:
        print("Parse error:", e)
        # fallback toàn bộ
        return ["Kiến thức chung"] * len(questions)
