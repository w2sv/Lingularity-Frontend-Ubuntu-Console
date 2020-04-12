import nltk
from nltk.stem.snowball import SnowballStemmer
from nltk.stem import WordNetLemmatizer

stemmer = SnowballStemmer('french')
print(stemmer.stem('éveiller'))

wnl = WordNetLemmatizer()
print(wnl.lemmatize('éveillées'))