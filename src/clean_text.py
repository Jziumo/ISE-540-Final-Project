from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import re
import nltk
from nltk.stem.porter import PorterStemmer


class CleanText: 
    """
    Regular text cleaning process. 
    """

    def __init__(self, df, do_stemming, stopwords=[]):
        self.ps = PorterStemmer()
        self.df = df
        self.do_stemming = do_stemming
        self.stopwords = stopwords
        self.clean_df()
    
    def clean_df(self): 
        for index, text, _, _ in self.df.itertuples():
            self.df['text'][index] = self.clean_text(text)
        
    def clean_text(self, text): 
        # Convert all text to lowercase
        text = text.lower()

        # eplace all characters except letters, digits, and '?''!', with a blank space.
        text = re.sub('[^a-z0-9?!]', ' ', text)

        text = re.sub(r'\s+', ' ', text).strip()

        if self.do_stemming or len(self.stopwords) > 0: 
            parts = text.split()
            if self.do_stemming:
                parts = [self.ps.stem(part) for part in parts if part not in self.stopwords]
            else:
                parts = [part for part in parts if part not in self.stopwords]
            text = ' '.join(parts)
        
        return text
    
    def get_df(self):
        return self.df


class RemoveNonEnglish: 
    """
    Remove the entries with non-English content. 
    """

    def __init__(self, df): 
        # To enforce consistent results
        DetectorFactory.seed = 0
        self.exception_entries = []
        self.other_language_entries = []
        self.df = df
        self.original_size = len(self.df)
        self.collect_non_english_content()
        self.remove()
        
    def get_language(self, text): 
        """
        Return the most possible language of the given text.
        """
        return detect(text)

    def collect_non_english_content(self): 
        """
        Collect Non-English entries into list. 
        """
        for index, text, _, _ in self.df.itertuples():
            try: 
                language = self.get_language(text)
                if language != 'en':
                    # If the language is not English
                    self.other_language_entries.append([index, text, language])
            except LangDetectException:
                # If the text cannot be recognized into any language
                self.exception_entries.append([index, text])

        print(f'The number of non-language entries: {len(self.exception_entries)}')
        print(f'The number of entries with other languages: {len(self.other_language_entries)}')

    def remove(self): 
        """
        Remove the non-English entries. 
        """
        self.df.drop(labels=[entry[0] for entry in self.exception_entries], inplace=True)
        self.df.drop(labels=[entry[0] for entry in self.other_language_entries], inplace=True)

        remove_num = self.original_size - len(self.df)
        print(f'The size reduces to {len(self.df)} from {self.original_size}. {remove_num} entries removed.')

    def get_df(self): 
        """
        Return the dataframe after processing. 
        """
        return self.df

class Stopwords: 
    def __init__(self, stopwords_type): 
        self.stopwords = set()
        if stopwords_type == 'specified': 
            self.stopwords = set(['i', 'the', 'and', 'for', 'a', 'of', 'to', 'this', 'that', 'in', 'on', 'at', 'so', 'with', 'as', 'was', 'is', 'are', 'be', 'it', 'have', 'has', 'you', 'your'])
        elif stopwords_type == 'nltk': 
            nltk.download('stopwords')
            from nltk.corpus import stopwords
            # Turn the stopwords list into a set. 
            self.stopwords = set(stopwords.words('english'))
            
            reserve = ['not', 'no', 'never', 'but', 'only', 'just', 'very', 'really', 'too', 'don\'t', 'wasn\'t', 'didn\'t', 'can\'t', 'won\'t']

            for word in reserve: 
                if word in self.stopwords:
                    self.stopwords.remove(word)

    def get_stopwords(self): 
        return self.stopwords
            

