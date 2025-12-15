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

