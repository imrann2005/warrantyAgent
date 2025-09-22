import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Database configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "warranty_system"