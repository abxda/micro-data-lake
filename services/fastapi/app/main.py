import os
import uvicorn
import logging

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from tempfile import NamedTemporaryFile
from sklearn.externals import joblib
from datetime import datetime, timedelta
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import sqlalchemy
from sqlalchemy import create_engine
import pandas as pd
import altair as alt
from altair import Chart, X, Y, Axis, SortField
import altair
alt.data_transformers.disable_max_rows()

app = FastAPI()
app.mount("/static", StaticFiles(directory="/html"), name="static")
def get_chart(keyword):
    db_string = "postgres://shared:changeme1234@postgres:5432/shared"
    if keyword == "*":
        query = "select article_id,string_date,site,palabra,n_w from tb_news_covid_mexico_palabras_top_tfidf"
    else:
        query = "select article_id,string_date,site,palabra,n_w from tb_news_covid_mexico_palabras_top_tfidf where article_id in (select article_id from tb_news_covid_mexico_date_text where clean_text LIKE '%"+keyword+"%' )"
    db = create_engine(db_string)
    df = pd.read_sql_query(sqlalchemy.text(query), db)
    chart3 = alt.Chart(df).mark_point().encode(
        y='count()',
        x='string_date:T'
    ).properties(width=900).interactive()
    
    chart1 = alt.Chart(df).mark_bar().encode(
    x=alt.X('count(article_id):Q'),
    y=alt.Y("site:N",sort=alt.EncodingSortField(field="site",op="count", order="descending")) 
    ).transform_aggregate(
        groupby=["article_id","site"]
    ).properties(height=800)
    
    chart2 = alt.Chart(df).mark_bar().encode(
    x=alt.X('freq_palabras:Q',aggregate="sum"),
    y=alt.Y("palabra",sort=alt.EncodingSortField(field="freq_palabras",op="sum", order="descending") )   
    ).transform_aggregate(
        freq_palabras='sum(n_w)',
        groupby=["palabra"],
    ).transform_window(
        rank='row_number()',
        sort=[alt.SortField("freq_palabras", order="descending")],
    ).transform_filter(
        (alt.datum.rank < 25)
    ).properties(height=800)
    
    return alt.vconcat(chart3, alt.hconcat(chart1, chart2)).to_json()

@app.get("/altair-chart")
async def root():
    data = get_chart("*")
    return Response(content=data, media_type="application/json")

@app.get("/keyword/{keyword}")
def query_keyword(keyword: str):
    data = get_chart(keyword)
    return Response(content=data, media_type="application/json")