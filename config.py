import os
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY", "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")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")