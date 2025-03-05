#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2025  Yogesh Rajashekharaiah
# All Rights Reserved

""" Document search single-page Django app """

import os
import time
import requests
from datetime import datetime
from collections import OrderedDict
import markdown
from humanize import precisedelta
from urllib.parse import quote

from django.conf import settings
from django.urls import path
from django.shortcuts import render

from coreutils import getlgr, RequestsOps, LMOps, VectorEmbeddings

# Allow Django to run in async environments
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# Configure logger
_lgrdj = getlgr("searchdocsUI")

# Solr configurations (ensure no trailing '/')
_FTBASE = ["https://solr.ml-dbfc64d1-783.go01-dem.ylcu-atmi.cloudera.site/solr"]
_FTINDEX = "searchdocuments"
_FTGET = "select"

def fmt_ftresults(results: dict, fltr_inp: str) -> (list[tuple], int):
    """ Formats BM25 search results for HTML display """
    doclst = []
    doccntr = None

    for doccntr, item in enumerate(results["response"]["docs"], 1):
        # ✅ Convert list to string (if necessary)
        doctext = item["doctext"]
        if isinstance(doctext, list):
            doctext = " ".join(doctext)  # Convert list to string

        # ✅ Now apply `.replace()` safely
        txtlst = doctext.replace('?', '').replace(',', '').replace('.', '').split()

        # NOT, AND, OR has special meaning in Solr search, remove them for the filtered text
        inpl = fltr_inp.replace("AND", '').replace("OR", '').replace("NOT", '')

        inpl = inpl.replace('?', '').replace(',', '').replace('.', '').replace('"', '').lower().split('~')[0].split()
        indxs = [i for i, x in enumerate(txtlst) if x.lower() in inpl]

        maxind = len(txtlst) - 1
        txt = ""

        for cntr, ind in enumerate(indxs):
            lft = max(0, ind - 5)
            rgt = min(maxind, ind + 5)
            txt = f"{txt} {' '.join(txtlst[lft:rgt])} &emsp;"

            if cntr > 9:
                txt = f"{txt} ..."
                break

        txt = txt or doctext[:500]  # Show part of the document if no match
        txtlst = txt.split()

        for term in inpl:
            for cntr, each in enumerate(txtlst):
                if each.lower() == term.lstrip('+').lstrip('-'):
                    txtlst[cntr] = f'<span class="srchterm">{each}</span>'

        mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item["docts"][0]))
        doclst.append((item["docpath"][0], mtime, ' '.join(txtlst)))

    return doclst, doccntr


def req_docs(inp: str) -> (list[tuple], str, str, str):
    """Queries Solr/OpenSearch for full-text search results."""
    stp_words = {'i', 'me', 'my', 'myself', 'we', 'our', 'ours',
    'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 
    'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 
    'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
     'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'did', 'doing',
     'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
     'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at',
    'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above',
    'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then',
    'here', 'there',  'all', 'any', 'both', 'each', 'few', 'more', 'most',  'by', 'for', 'once',
    'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 
    's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'below', 'to',
     'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 
    'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn',
     "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
    'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"}
    
    q_words = {'what', 'which', 'who', 'whom', 'when', 'where', 'whose', 'why', 'how'}
    addl_q_words = {'explain', 'describe', 'elaborate', 'summarize', 'examine', 'evaluate',
                    'analyze', 'clarify', 'diagnose', 'assess' }

    
    err, descr, ft_result = None, None, None

    # ✅ Strip spaces before checking if it's a question
    inp = inp.strip()
    ai_summary = inp.endswith('?')  # ✅ Ensure LLM trigger works

    linp = " ".join(inp.split())  # ✅ Normalize input

    if linp:
        solr_url = f"{_FTBASE[0].rstrip('/')}/{_FTINDEX}/{_FTGET}"
        params = {'q': linp, "df": "doctext", "fl": "doctext,docpath,docts"}

        _lgrdj.info(f"Solr request: {solr_url} with params {params}")

        try:
            resp = requests.get(solr_url, params=params, timeout=5)

            if resp.ok:
                results = resp.json()
                _lgrdj.info(f"Solr response: {results}")

                if "response" in results and "docs" in results["response"]:
                    docs = results["response"]["docs"]

                    if docs:
                        ft_result, doccnt = fmt_ftresults(results, linp)
                        descr = f"Documents found: {doccnt}"
                    else:
                        descr = "No document found"

                else:
                    _lgrdj.error(f"Unexpected Solr response: {results}")
                    err = "Solr returned an unexpected format."

            else:
                _lgrdj.error(f"Solr Error: {resp.text}")
                err = f"Solr Error: {resp.status_code}"

        except requests.exceptions.RequestException as exc:
            _lgrdj.error(f"Solr request failed: {exc}")
            err = "Unable to query Solr."

    else:
        err = "Enter valid search terms"

    # ✅ Ensure AI summary is triggered only if search results exist
    if ai_summary and ft_result:
        ai_summary = generate_llm_summary(linp, ft_result)
    else:
        ai_summary = None

    return ft_result, ai_summary, descr, err


def generate_llm_summary(query: str, ft_result: list) -> str:
    """ Calls LLM to summarize search results """
    try:
        context = " ".join([doc[2] for doc in ft_result])  # Extract relevant text
        query_context = f"Summarize: {query}. Context: {context}"
        _lgrdj.info(f"Sending to LLM: {query_context[:500]}")  # ✅ Log only first 500 chars
        return markdown.markdown(lmdl.mdl_response(query_context))  # ✅ Ensure markdown output
    except Exception as exc:
        _lgrdj.error(f"LLM summary failed: {exc}")
        return None  # Return None if LLM fails


ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
BASE_DIR = os.getcwd()

settings.configure(
    DEBUG=False,
    SECRET_KEY="AB123xyz$#@!",
    ALLOWED_HOSTS=ALLOWED_HOSTS,
    ROOT_URLCONF=__name__,
    MIDDLEWARE_CLASSES=(
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ),
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    }],
    INSTALLED_APPS=('django.contrib.staticfiles', 'django.contrib.contenttypes'),
    STATICFILES_DIRS=(os.path.join(BASE_DIR, 'static'),),
    STATIC_URL='/static/',
    LOGGING={
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': 'debug.log',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }
)

def index(request):
    """Handles search page requests."""
    inp_txt = request.GET.get('inp_txt', '')
    result, ai_summary, descr, err = req_docs(inp_txt) if inp_txt else (None, None, None, None)
    context = {"inp_txt": inp_txt, "result": result, "ai_summary": ai_summary, "descr": descr, "err": err}
    return render(request, 'home.html', context)

urlpatterns = (path('', index),)

if __name__ == "__main__":
    requestsession = RequestsOps()
    lmdl = LMOps()
    emdb = VectorEmbeddings()
    from django.core.management import execute_from_command_line
    SERVER_ADDR = "127.0.0.1:" + os.getenv("CDSW_APP_PORT")
    args = ['searchdocuments', 'runserver', SERVER_ADDR, '--noreload', '--skip-checks', '--nothreading', '--insecure']
    execute_from_command_line(args)
