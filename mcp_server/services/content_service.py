"""
Content Service Module

This module provides services for content processing operations.
It handles text summarization, information extraction, and content analysis.
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any, Union
import re
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter

# Add the parent directory to the path to import from mcp_server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class ContentService:
    """Service for content processing operations."""
    
    def __init__(self):
        """Initialize the Content service."""
        self.stop_words = set(stopwords.words('english'))
    
    def summarize_text(self, text: str, max_sentences: int = 3) -> str:
        """Summarize text by extracting the most important sentences.
        
        Args:
            text: The text to summarize.
            max_sentences: The maximum number of sentences to include in the summary.
            
        Returns:
            The summarized text.
        """
        try:
            # Tokenize the text into sentences
            sentences = sent_tokenize(text)
            
            if len(sentences) <= max_sentences:
                return text
            
            # Tokenize words and remove stopwords
            word_tokens = word_tokenize(text.lower())
            filtered_words = [word for word in word_tokens if word.isalnum() and word not in self.stop_words]
            
            # Count word frequencies
            word_frequencies = Counter(filtered_words)
            
            # Calculate sentence scores based on word frequencies
            sentence_scores = {}
            for i, sentence in enumerate(sentences):
                for word in word_tokenize(sentence.lower()):
                    if word in word_frequencies:
                        if i not in sentence_scores:
                            sentence_scores[i] = word_frequencies[word]
                        else:
                            sentence_scores[i] += word_frequencies[word]
            
            # Get the top sentences
            top_sentence_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:max_sentences]
            top_sentence_indices = sorted(top_sentence_indices)  # Sort by original position
            
            # Create the summary
            summary = ' '.join([sentences[i] for i in top_sentence_indices])
            
            return summary
            
        except Exception as e:
            logger.error(f'An error occurred during text summarization: {e}')
            return text
    
    def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extract keywords from text.
        
        Args:
            text: The text to extract keywords from.
            max_keywords: The maximum number of keywords to extract.
            
        Returns:
            A list of keywords.
        """
        try:
            # Tokenize words and remove stopwords
            word_tokens = word_tokenize(text.lower())
            filtered_words = [word for word in word_tokens if word.isalnum() and word not in self.stop_words]
            
            # Count word frequencies
            word_frequencies = Counter(filtered_words)
            
            # Get the top keywords
            keywords = [word for word, _ in word_frequencies.most_common(max_keywords)]
            
            return keywords
            
        except Exception as e:
            logger.error(f'An error occurred during keyword extraction: {e}')
            return []
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text.
        
        Args:
            text: The text to extract entities from.
            
        Returns:
            A dictionary of entity types and their values.
        """
        try:
            # This is a simplified implementation
            # In a real application, you would use a proper NER model
            
            # Extract email addresses
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, text)
            
            # Extract URLs
            url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
            urls = re.findall(url_pattern, text)
            
            # Extract phone numbers
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            phones = re.findall(phone_pattern, text)
            
            # Extract dates (simple pattern)
            date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
            dates = re.findall(date_pattern, text)
            
            return {
                'emails': emails,
                'urls': urls,
                'phones': phones,
                'dates': dates
            }
            
        except Exception as e:
            logger.error(f'An error occurred during entity extraction: {e}')
            return {}
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze the sentiment of text.
        
        Args:
            text: The text to analyze.
            
        Returns:
            A dictionary with sentiment scores.
        """
        try:
            # This is a simplified implementation
            # In a real application, you would use a proper sentiment analysis model
            
            # Simple positive/negative word lists
            positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'happy', 'love', 'like'}
            negative_words = {'bad', 'terrible', 'awful', 'horrible', 'poor', 'disappointing', 'sad', 'hate', 'dislike'}
            
            # Tokenize words
            word_tokens = word_tokenize(text.lower())
            
            # Count positive and negative words
            positive_count = sum(1 for word in word_tokens if word in positive_words)
            negative_count = sum(1 for word in word_tokens if word in negative_words)
            
            # Calculate sentiment scores
            total_words = len(word_tokens)
            if total_words == 0:
                return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
                
            positive_score = positive_count / total_words
            negative_score = negative_count / total_words
            neutral_score = 1.0 - positive_score - negative_score
            
            return {
                'positive': positive_score,
                'negative': negative_score,
                'neutral': neutral_score
            }
            
        except Exception as e:
            logger.error(f'An error occurred during sentiment analysis: {e}')
            return {'positive': 0.0, 'negative': 0.0, 'neutral': 1.0}
    
    def summarize_email_list(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize a list of emails.
        
        Args:
            emails: A list of email metadata.
            
        Returns:
            A summary of the email list.
        """
        try:
            if not emails:
                return {
                    'total_emails': 0,
                    'senders': [],
                    'subjects': [],
                    'date_range': {'start': None, 'end': None}
                }
            
            # Extract senders
            senders = [email.get('sender', 'Unknown') for email in emails]
            sender_counts = Counter(senders)
            top_senders = [sender for sender, _ in sender_counts.most_common(3)]
            
            # Extract subjects
            subjects = [email.get('subject', 'No Subject') for email in emails]
            
            # Extract dates
            dates = []
            for email in emails:
                date_str = email.get('date', '')
                if date_str:
                    try:
                        # Try to parse the date (simplified)
                        date_match = re.search(r'\d{1,2}\s+[A-Za-z]{3}\s+\d{4}', date_str)
                        if date_match:
                            dates.append(date_match.group(0))
                    except:
                        pass
            
            # Calculate date range
            date_range = {'start': None, 'end': None}
            if dates:
                date_range['start'] = min(dates)
                date_range['end'] = max(dates)
            
            return {
                'total_emails': len(emails),
                'senders': top_senders,
                'subjects': subjects,
                'date_range': date_range
            }
            
        except Exception as e:
            logger.error(f'An error occurred during email list summarization: {e}')
            return {
                'total_emails': len(emails),
                'senders': [],
                'subjects': [],
                'date_range': {'start': None, 'end': None}
            } 