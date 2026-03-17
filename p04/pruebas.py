import spacy
nlp = spacy.load("es_core_news_sm")
doc = nlp("This is a sentence.")
print([(w.text, w.pos_) for w in doc])