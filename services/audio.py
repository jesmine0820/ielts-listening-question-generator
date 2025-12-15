# Import necessary libraries
import os
import re
import json
import pandas as pd
import google.generativeai as genai
import textstat

from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configuration
QUESTION_TYPE_CSV = "model_training/processed_data/questionType.csv"
WORD_CSV = "model_training/processed_data/ielts_vocab.csv"
TRAINING_CSV = "model_training/processed_data/training_set.csv"
GENERATED_JSON = "model_training/generated_questions/generated_questions.json"
TEMP_CSV = "model_training/generated_questions/temp_generated_questions.json"

MAX_ATTEMPT = 5
REWARD_GOAL = 4

