FROM python:3.6

RUN pip -q install requests rdflib tqdm

WORKDIR /pgxlod-reconciliation-rules

COPY src /pgxlod-reconciliation-rules/

ENTRYPOINT ["python", "/pgxlod-reconciliation-rules/main.py"]
