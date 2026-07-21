FROM python:3.11-slim

LABEL org.scandium-labs.dataset.version="v0.0.0"
LABEL org.scandium-labs.dataset.description="Scandium-Dataset — Curated computational materials dataset for SSB discovery"

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python3 -c "import ase, pymatgen, numpy, scipy; print('Dependencies OK')"

ENTRYPOINT ["python3"]
CMD ["--help"]
