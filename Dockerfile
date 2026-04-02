FROM registry.access.redhat.com/ubi9/python-311:latest

USER 0

RUN dnf install -y https://packages.microsoft.com/config/rhel/9/packages-microsoft-prod.rpm && \
    ACCEPT_EULA=Y dnf install -y msodbcsql18 unixODBC-devel gcc python3-devel && \
    dnf clean all

USER 1001

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "app:app"]
