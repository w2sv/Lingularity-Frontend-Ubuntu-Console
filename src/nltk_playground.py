import nltk
from nltk.stem.snowball import SnowballStemmer
from nltk.stem import WordNetLemmatizer

stemmer = SnowballStemmer('french')
print(stemmer.stem('Neigera-t-il'))

wnl = WordNetLemmatizer()
print(wnl.lemmatize('Neigera-t-il'))

# nltk.download('averaged_perceptron_tagger')  # punkt, averaged_perceptron_tagger

tokens = nltk.word_tokenize('Someone hit on Jessica and Martin and Peters and Claude in Paris, France the tables in the city were actually standing in forests.')  # NNP
print(tokens)
pos_tags = nltk.pos_tag(tokens)
print(pos_tags)
