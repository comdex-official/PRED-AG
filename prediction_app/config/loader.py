from dotenv import load_dotenv
import os

def load_config():
    """Load environment variables before config is imported"""
    load_dotenv() 