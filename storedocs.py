#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import argparse
from humanize import precisedelta
import requests

from coreconfigs import (
    _VECINDEX, _MODEL_PATH, _MAXCHNKLEN, _CHUNKTOKENIZER, _CUDA_ARCHTYPE,
    _NUM_THREADS, _DO_OCR, _OCR_LANG, _PAGE_IMAGES, _PICTURE_IMAGES,
    _TABLE_STRUCTURE, _CELL_MATCHING, _PDF_BACKEND,
    _FTBASE, _FTINDEX, _FTPOST, _FTTLSVERIFY,  # Solr Configs
    _VECBASE, _VECPOST, _VECTLSVERIFY  # OpenSearch Configs
)

# Ensure the environment variables are set for correct model paths
os.environ["TORCH_CUDA_ARCH_LIST"] = _CUDA_ARCHTYPE
os.environ["HF_HUB_CACHE"] = _MODEL_PATH
os.environ["CUDA_VISIBLE_DEVICES"] = ""

from docling.datamodel.base_models import InputFormat, DocumentStream
from docling.backend.docling_parse_v2_backend import DoclingParseV2DocumentBackend
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions, AcceleratorOptions, AcceleratorDevice, TableFormerMode
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.chunking import HybridChunker
from coreutils import VectorEmbeddings, good_text

class DoclingOps(VectorEmbeddings):
    """Handles document processing, extraction, and embedding generation."""
    def __init__(self):
        super().__init__()
        self._chunker = HybridChunker(tokenizer=_CHUNKTOKENIZER, max_tokens=_MAXCHNKLEN)
        self.doc = None
        self.fulltext = None
        self._chunk_iter = None

        self._ploptions = PdfPipelineOptions()
        self._ploptions.artifacts_path = _MODEL_PATH
        self._ploptions.do_ocr = _DO_OCR
        self._ploptions.ocr_options.lang = _OCR_LANG
        self._ploptions.generate_page_images = _PAGE_IMAGES
        self._ploptions.generate_picture_images = _PICTURE_IMAGES
        self._ploptions.do_table_structure = _TABLE_STRUCTURE
        self._ploptions.table_structure_options.do_cell_matching = _CELL_MATCHING
        self._ploptions.table_structure_options.mode = TableFormerMode.ACCURATE
        self._ploptions.accelerator_options = AcceleratorOptions(device=AcceleratorDevice.CUDA, num_threads=_NUM_THREADS)

        backend = PyPdfiumDocumentBackend if _PDF_BACKEND == "pypdfium" else DoclingParseV2DocumentBackend

        self._docconv = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=self._ploptions, backend=backend),
            },
        )

    def convert_doc(self, docpath):
        """Extracts text and chunks from a document."""
        self.doc = self._docconv.convert(docpath).document
        self.fulltext = good_text(self.doc.export_to_text())
        self._chunk_iter = (good_text(self._chunker.serialize(chunk=chunk).replace('\n', ' '))
                            for chunk in self._chunker.chunk(self.doc))

    def get_embeddings_for_vdb(self, docpath):
        """Yields document chunks along with embeddings."""
        for txtchunk in self._chunk_iter:
            if len(txtchunk.split()) > 5:
                embeddings = self.emb_mdl.encode(txtchunk.lower()).tolist()
                yield {"chunkvec": embeddings, "docchunk": txtchunk.lower(), "docpath": docpath.as_posix()}

def index_fulltext(flname):
    """Indexes full text into Solr."""
    solr_url = f"{_FTBASE[0]}{_FTINDEX}/{_FTPOST}"
    headers = {"Content-Type": "application/json"}
    doc_data = {
        "id": dlgdoc.doc.origin.binary_hash,
        "docts": flname.stat().st_mtime,
        "docpath": flname.as_posix(),
        "doctext": dlgdoc.fulltext
    }

    try:
        response = requests.post(solr_url, json=doc_data, headers=headers, verify=_FTTLSVERIFY)
        response.raise_for_status()
        print(f"Indexed: {flname} - Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Solr Indexing Error: {flname} - {e}")
        sys.exit(1)

def index_embeddings(flname):
    """Indexes document chunks with embeddings into OpenSearch."""
    os_url = f"{_VECBASE[0]}{_VECINDEX}/{_VECPOST}"
    headers = {"Content-Type": "application/x-ndjson"}

    data = ""
    for idx, chunk in enumerate(dlgdoc.get_embeddings_for_vdb(flname)):
        index_meta = {"index": {"_index": _VECINDEX, "_id": f"{dlgdoc.doc.origin.binary_hash}{idx}"}}
        data += f"{json.dumps(index_meta)}\n{json.dumps(chunk)}\n"

    try:
        response = requests.post(os_url, data=data, headers=headers, verify=_VECTLSVERIFY)
        response.raise_for_status()
        print(f"Indexed Embeddings: {flname} - Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"OpenSearch Indexing Error: {flname} - {e}")
        sys.exit(1)

def process_files(argsdct):
    """Iterates over files and processes them for indexing."""
    fl_or_fldr = Path(argsdct["fl_or_fldr"])
    prevrun_dt = argsdct.get("prevrun_dt", None)

    if prevrun_dt:
        prevrun_dt = int(time.mktime(time.strptime(prevrun_dt, '%Y-%m-%d %H:%M:%S')))

    def process_file(fname):
        try:
            dlgdoc.convert_doc(fname)
            index_fulltext(fname)
            index_embeddings(fname)
        except Exception as e:
            print(f"Processing Error: {fname} - {e}")

    if fl_or_fldr.is_dir():
        for fname in fl_or_fldr.iterdir():
            if fname.is_file() and not fname.is_symlink() and (not prevrun_dt or fname.stat().st_mtime > prevrun_dt):
                process_file(fname)
    elif fl_or_fldr.is_file():
        process_file(fl_or_fldr)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Index documents into Solr (full-text) and OpenSearch (embeddings).")
    parser.add_argument('fl_or_fldr', help='File or directory to process.')
    parser.add_argument('-r', '--prevrun_dt', default=None, help='Process files after timestamp "YYYY-MM-DD HH:MM:SS".')
    args = parser.parse_args()

    dlgdoc = DoclingOps()
    process_files(vars(args))
