@echo off
REM Run this from inside the backend folder

set DATA_PATH=../data/papers.csv
set MLFLOW_TRACKING_URI=./mlruns
set JWT_SECRET=research_plus_super_secret_key_2024

uvicorn main:app --reload --port 8000