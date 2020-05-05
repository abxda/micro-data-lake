import os
import uvicorn
import logging

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from minio import Minio
from tempfile import NamedTemporaryFile
from sklearn.externals import joblib
from datetime import datetime, timedelta

app = FastAPI()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)