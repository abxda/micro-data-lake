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

class Email(BaseModel):
    body: str
    subject: str
    emailSender: List[str]
    emailReceiver: List[str]

class Emails(BaseModel):
    emails: List[Email]

class Prediction(dict):
    def __init__(self, value, prediction):
        dict.__init__(self, value=value, prediction=prediction)

def get_previous_sunday():
    d = datetime.strptime(datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d')
    t = timedelta((d.weekday() + 1) % 7)
    return (d - t).strftime('%Y-%m-%d')

def get_obj_from_minio(minio_client, butket_name, object_name, default_object_name):
    with NamedTemporaryFile() as tmp:
        if any(obj.object_name == object_name for obj in minio_client.list_objects(butket_name)):
            minio_client.fget_object(butket_name, object_name, tmp.name)
        else:
            minio_client.fget_object(butket_name, default_object_name, tmp.name)
        return joblib.load(tmp.name)

@app.post("/predict")
def predict(*, emailsList: Emails):
    logging.info("Prediction has been called")
    texts = []
    returnPredictions = []

    #  create minio connection
    minio_client = Minio(
        endpoint="minio:9000",
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        secure=False
    )

    previous_sunday = get_previous_sunday()

    # read model, tfidf, categories from minio
    model = get_obj_from_minio(minio_client, "models", "linearSVC-{previous_sunday}.pkl".format(**locals()), "linearSVC.pkl")
    tfidf = get_obj_from_minio(minio_client, "features", "tfidf-{previous_sunday}.pkl".format(**locals()), "tfidf.pkl")
    category_id_df = get_obj_from_minio(minio_client, "categories", "categories-map-{previous_sunday}.pkl".format(**locals()), "categories-map.pkl")

    # util func to get category name based on id
    id_to_category = dict(category_id_df[['category_id', 'category']].values)

    # form texts array
    for email in emailsList.emails:
        texts.append(email.subject + " " + email.body)

    # create tf-idf values
    features = tfidf.transform(texts)

    # make predictions
    predictions = model.predict(features)

    #generate response object
    for text, predicted in zip(texts, predictions):
        returnPredictions.append(Prediction(text, id_to_category[predicted]))

    return returnPredictions

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)