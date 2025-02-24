FROM ghcr.io/chroma-core/chroma:0.4.18

# Downgrade NumPy to a compatible version
RUN pip uninstall -y numpy && \
    pip install numpy==1.24.3

# Keep the original CMD
CMD ["uvicorn", "chromadb.app:app", "--reload", "--workers", "1", "--host", "0.0.0.0", "--port", "8000"]
