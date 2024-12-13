import spacy
from spacy.matcher import PhraseMatcher

nlp = spacy.load('en_core_web_sm')

def rewrite_content(text, keywords):
    doc = nlp(text)
    matcher = PhraseMatcher(nlp.vocab)

    keyword_docs = [nlp(keyword_obj['keyword']) for keyword_obj in keywords]
    matcher.add("KeywordMatcher", keyword_docs)

    optimized_text = text
    matches = matcher(doc)

    inserted_keywords = set()

    for match_id, start, end in matches:
        keyword = doc[start:end].text
        sentence = doc[start:end].sent
        if keyword not in inserted_keywords:
            optimized_text = optimized_text.replace(sentence.text, f"<b>{sentence.text.replace(keyword, f'<span style=\"color:red;\">{keyword}</span>')}</b>")
            inserted_keywords.add(keyword)

    remaining_keywords = [kw['keyword'] for kw in keywords if kw['keyword'] not in inserted_keywords]
    if remaining_keywords:
        optimized_text += "\n\nUnused Keywords: " + ", ".join(remaining_keywords)

    return optimized_text

text = """
Across all walks of life, individuals are required to perform well in challenging circumstances. This experience can be stressful and may sometimes have a negative influence on wellbeing.
"""
keywords = [
    {"keyword": "degree apprenticeships"},
    {"keyword": "apprenticeships in staffordshire"},
    {"keyword": "university apprenticeships uk"}
]

print(rewrite_content(text, keywords))
