# Hybrid Search with BM25 and RAG with vector database


## Overview

Tool to interact with language models for document search and summarization, enabled by BM25 and Retrieval-Augmented Generation(RAG). Context embeddings are stored and retrieved from a vector database (OpenSearch). Term search (BM25) uses Solr.

![](/static/screenshot-hybridsearch.png)

## Features
- Extracts texts from files. Supported file formats : pdf, docx, xlsx, pptx, html, md, asciidoc, images: jpg, png, tiff, bmp, gif
- Indexes full texts in Solr for BM25 search
- Creates context-enriched text chunks, generates embeddings using custom model. Saves the text chunks and embeddings in vectorDB, OpenSearch
- UI for search. Generates AI summary.


## Installation
### Prerequisites

- [Python](https://www.python.org/downloads/) 3.10 or greater
- check requirements.txt for required python libraries
- requires nvidia-gpu

### Solr and OpenSearch
Installed via AMP and configured as applications. IMPORTANT! Make sure to set up "Unauthenticated App Access" for Solr after AMP install and before you run the first job.

## Application

- storedocs.py: Script to read files from a folder(and all subfolders), saves full text to Solr, generate embeddings on context-enriched text chunks and saves to OpenSearch
- djapp.py: Single page Django application, UI, for document search and summarization