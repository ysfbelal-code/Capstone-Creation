import os
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY", "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")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
