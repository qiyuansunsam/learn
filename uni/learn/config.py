# config.py
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from a .env file if it exists

# --- Gemini API Key ---
# It's highly recommended to use environment variables for API keys
# Create a .env file in the project root with: GOOGLE_API_KEY="your_actual_key"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "YOUR_DEFAULT_API_KEY_HERE") # Replace default if not using .env

# --- File Paths ---
# Base directory where all topic folders will reside
TOPICS_BASE_DIR = "topics"

# --- Gemini Model ---
GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-04-17" # Or your preferred model

# --- Other Settings ---
DEFAULT_NUM_QUESTIONS_TO_GENERATE = 5 # Default number for generation requests
