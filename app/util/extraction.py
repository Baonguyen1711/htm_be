from functools import lru_cache
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT
from underthesea import word_tokenize, pos_tag

# ----------------------------
# POS-based candidate extraction
# ----------------------------
def extract_noun_phrases(text):
    """
    Extract multi-word noun phrases (N+N or N+N+N) from Vietnamese text
    """
    words_tags = pos_tag(text)
    phrases = []
    i = 0
    while i < len(words_tags):
        w, t = words_tags[i]
        if t.startswith("N"):  # Noun
            phrase = [w]
            j = i + 1
            while j < len(words_tags) and words_tags[j][1].startswith("N"):
                phrase.append(words_tags[j][0])
                j += 1
            if len(phrase) > 1:  # only multi-word phrases
                phrases.append(" ".join(phrase))
            i = j
        else:
            i += 1
    return phrases

# ----------------------------
# Filter nested/overlapping phrases
# ----------------------------
def filter_nested_phrases(phrases):
    phrases = sorted(phrases, key=lambda x: len(x.split()), reverse=True)
    filtered = []
    for p in phrases:
        if not any(p in other for other in filtered):
            filtered.append(p)
    return filtered

# ----------------------------
# KeyBERT setup
# ----------------------------
@lru_cache(maxsize=1)
def get_kw_model(model_name="paraphrase-multilingual-MiniLM-L12-v2"):
    model = SentenceTransformer(model_name)
    return KeyBERT(model=model)

# ----------------------------
# Main idea extraction
# ----------------------------
def extract_main_ideas_vi(text, top_n=5, use_ranking=True):
    # Step 1: Segment text
    segmented = word_tokenize(text, format="text")

    # Step 2: Extract candidate noun phrases
    candidates = extract_noun_phrases(segmented)

    if not candidates:
        # fallback to single nouns if no multi-word noun phrases
        candidates = [w for w, t in pos_tag(segmented) if t.startswith("N")]

    # Step 3: Lowercase for KeyBERT / sklearn
    segmented_lower = segmented.lower()
    candidates_lower = [c.lower() for c in candidates]

    # Step 4: Optionally rank candidates with KeyBERT
    if use_ranking:
        kw_model = get_kw_model()
        ranked = kw_model.extract_keywords(
            segmented_lower,
            keyphrase_ngram_range=(1, 3),
            stop_words=None,
            top_n=top_n,
            use_mmr=True,
            candidates=candidates_lower
        )
        keywords = [kw.replace("_", " ") for kw, score in ranked]
    else:
        keywords = candidates[:top_n]

    # Step 5: Filter nested phrases
    main_ideas = filter_nested_phrases(keywords)

    return main_ideas[:top_n]

# ----------------------------
# Example usage
# ----------------------------
question = "Nhà toán học nào được coi là người sáng lập nên lí thuyết tập hợp?"
print(extract_main_ideas_vi(question))

