from setuptools import setup, find_packages

setup(
    name="prediction_app",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "python-dotenv>=0.19.0",
        "sqlalchemy>=1.4.23",
        "pydantic>=1.8.2",
        "schedule>=1.1.0",
        "requests>=2.26.0",
        "spacy>=3.0.0",
        "psycopg2-binary>=2.9.1",
        "beautifulsoup4>=4.9.3",
    ],
) 