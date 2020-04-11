import nltk
from nltk.stem.snowball import SnowballStemmer

stemmer = SnowballStemmer('english')
print(stemmer.stem('mice'))

from nltk.stem import WordNetLemmatizer


wnl = WordNetLemmatizer()
print(wnl.lemmatize('mice'))