import os
from dotenv import load_dotenv

load_dotenv()

DART_API_KEY = os.getenv("DART_API_KEY")

if not DART_API_KEY:
    raise ValueError("DART_API_KEY가 없습니다. .env 파일에 DART_API_KEY를 설정하세요.")