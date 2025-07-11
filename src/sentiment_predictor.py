from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from typing import Dict, Any
import re
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

class SentimentPredictor:
    """
    A class to predict sentiment for both product and video comments
    using pre-trained BERT models.
    """
    def __init__(self, model_name: str = "bert-base-uncased"):
        """
        Initializes the SentimentPredictor by loading the tokenizer and two sentiment models.

        Args:
            model_product_path (str): Path to the directory containing the fine-tuned
                                      model for product sentiment (e.g., "./models/sentiment_for_product/").
            model_video_path (str): Path to the directory containing the fine-tuned
                                    model for video sentiment (e.g., "./models/sentiment_for_video/").
            model_name (str): The base pre-trained model name for the tokenizer
                              (default: "bert-base-uncased").
        """
        self.labels = ["negative", "neutral", "positive"]

        # Load the tokenizer once for both models
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Load both fine-tuned models
        model_product_path = './models/sentiment_for_product_current'
        model_video_path = './models/sentiment_for_video_current'
        self.model_product = AutoModelForSequenceClassification.from_pretrained(model_product_path)
        self.model_video = AutoModelForSequenceClassification.from_pretrained(model_video_path)

        # Set models to evaluation mode
        self.model_product.eval()
        self.model_video.eval()

        # Check for CUDA availability and move models to GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_product.to(self.device)
        self.model_video.to(self.device)
        print(f"Models loaded and moved to {self.device} device.")

    def predict(self, comment: str) -> Dict[str, str]:
        """
        Predicts the sentiment for a given comment text for both product and video.

        Args:
            comment (str): The comment text. 

        Returns:
            Dict[str, str]: A dictionary containing predicted sentiments:
                            {"sentiment_for_product": "sentiment_label",
                             "sentiment_for_video": "sentiment_label"}
        """
        if not isinstance(comment, str):
            raise TypeError("Input comment must be a string.")
        if not comment.strip():
            return None

        try: 
            language = self.get_language(comment)
            if language != 'en':
                # If the language is not English
                return None
        except LangDetectException:
            # If the text cannot be recognized into any language
            return None

        comment = self.clean_text(comment)

        # Tokenize input and move to the appropriate device
        inputs = self.tokenizer(comment, return_tensors="pt", truncation=True, padding=True, max_length=128)
        inputs = {key: val.to(self.device) for key, val in inputs.items()}

        # Predict for product sentiment
        with torch.no_grad():
            outputs_product = self.model_product(**inputs)
            # Apply softmax to get probabilities if needed for confidence scores, otherwise argmax on logits is fine
            # probabilities_product = torch.softmax(outputs_product.logits, dim=1)
            pred_product_id = torch.argmax(outputs_product.logits, dim=1).item()
            sentiment_product = self.labels[pred_product_id]

        # Predict for video sentiment
        with torch.no_grad():
            outputs_video = self.model_video(**inputs)
            # probabilities_video = torch.softmax(outputs_video.logits, dim=1)
            pred_video_id = torch.argmax(outputs_video.logits, dim=1).item()
            sentiment_video = self.labels[pred_video_id]

        return {
            "sentiment_for_product": sentiment_product,
            "sentiment_for_video": sentiment_video
        }
    
    def get_language(self, text): 
        """
        Return the most possible language of the given text.
        """
        return detect(text)


    def clean_text(self, text, do_stemming=False): 
        # Convert all text to lowercase
        text = text.lower()

        # eplace all characters except letters, digits, and '?''!', with a blank space.
        text = re.sub('[^a-z0-9?!]', ' ', text)

        text = re.sub(r'\s+', ' ', text).strip()

        if do_stemming: 
            parts = text.split()
            parts = [self.ps.stem(part) for part in parts]
            text = ' '.join(parts)
        
        return text

if __name__ == "__main__":
    predictor = SentimentPredictor()

    # Test comments
    comment1 = "This product is amazing, completely changed my life!"
    comment2 = "The video was so boring and unhelpful, what a waste of time."
    comment3 = "The product is okay, but the video was pretty good."
    comment4 = "This comment is irrelevant to both product and video."
    comment5 = "" # Empty comment test

    print(f"Comment: '{comment1}'")
    print(f"Prediction: {predictor.predict(comment1)}\n")

    print(f"Comment: '{comment2}'")
    print(f"Prediction: {predictor.predict(comment2)}\n")

    print(f"Comment: '{comment3}'")
    print(f"Prediction: {predictor.predict(comment3)}\n")

    print(f"Comment: '{comment4}'")
    print(f"Prediction: {predictor.predict(comment4)}\n")
    
    print(f"Comment: '{comment5}'")
    print(f"Prediction: {predictor.predict(comment5)}\n")
