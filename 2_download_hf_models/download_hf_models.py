# Download Docling models
import os

from sentence_transformers import SentenceTransformer
from huggingface_hub import snapshot_download
download_path = snapshot_download(
	repo_id="ds4sd/docling-models",
	force_download=True,
	local_dir="/home/cdsw/models",
	revision="v2.1.0",
)

# Download Language models, _CHUNKTOKENIZER, _LM_MDL
from sentence_transformers import SentenceTransformer
mdl = SentenceTransformer("HuggingFaceTB/SmolLM2-1.7B-Instruct")
print(mdl.tokenizer.model_max_length)