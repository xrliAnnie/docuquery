FROM chromadb/chroma:0.4.22

# Force reinstall the specific versions, ensuring they override any upgrades
RUN pip install --no-cache-dir --force-reinstall numpy==1.24.3 chroma-hnswlib==0.7.3

CMD ["python", "-m", "chromadb.serve"]