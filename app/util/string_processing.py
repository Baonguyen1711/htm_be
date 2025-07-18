import re

def normalize_string(text: str) -> str:
    # Lowercase
    text = text.lower()
    # Remove leading/trailing spaces
    text = text.strip()
    # Replace multiple spaces/tabs/newlines with a single space
    text = re.sub(r'\s+', ' ', text)
    return text