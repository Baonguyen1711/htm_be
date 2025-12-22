EXTRACT_IDEA_PROMPT = """
Bạn là một hệ thống xử lý dữ liệu câu hỏi.

Đầu vào: danh sách các câu hỏi, mỗi câu gồm:
- questionId (id câu hỏi)
- question (câu hỏi)
- answer (câu trả lời)

Nhiệm vụ: với từng câu, tạo object mới gồm:
- questionId: giữ nguyên
- keyIdea: mảng 1–5 ý chính/nguyên lý cốt lõi (3–6 từ mỗi ý)
- referenceLink: mảng tối đa 5 link tài liệu đáng tin cậy (ưu tiên Wikipedia tiếng Việt, nếu không có thì Wikipedia tiếng Anh, báo chính thống, website học thuật)

Yêu cầu quan trọng:
- Chỉ trả về **một mảng JSON**.
- Không thêm text, giải thích, markdown hoặc ký tự ngoài JSON.
- JSON phải hợp lệ, sẵn sàng parse bằng Python `json.loads`.
- Mỗi object trong mảng JSON phải có đúng các key: "questionId", "keyIdea", "referenceLink".

Dữ liệu đầu vào:
{questions}
"""

IS_ACCEPTED_ANSWER_PROMPT = """
Bạn là một hệ thống xử lý dữ liệu câu hỏi.
Với câu hỏi sau đây {question}
Và câu trả lời từ thí sinh như sau: {answer}
Hãy kiểm tra xem liệu câu trả lời này có thể được chấp nhận là đúng hay không.
Nếu đúng, hãy trả về "True", ngược lại trả về "False". Không thêm bất kỳ giải thích hay ký tự nào khác ngoài "True" hoặc "False".
"""