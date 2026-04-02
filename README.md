# mssql-crud-app

A minimal Flask CRUD application connected to SQL Server 2022, designed to run on OpenShift.

## Features

- **Create** / **Read** / **Update** / **Delete** items stored in SQL Server
- Auto-creates the database and table on first run
- Health endpoint at `/health`
- OpenShift-ready with UBI 9 container image, Route, and readiness/liveness probes

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MSSQL_HOST` | `mssql-deployment` | SQL Server service hostname |
| `MSSQL_PORT` | `1433` | SQL Server port |
| `MSSQL_USER` | `sa` | Database user |
| `MSSQL_SA_PASSWORD` | *(required)* | SA password (from Secret) |
| `MSSQL_DATABASE` | `cruddb` | Database name to use |
| `PORT` | `8080` | Application listen port |

## Run Locally

```bash
export MSSQL_HOST=localhost
export MSSQL_SA_PASSWORD=YourPassword123
pip install -r requirements.txt
python app.py
```

## Deploy on OpenShift

```bash
# Build the image (from the same namespace as your SQL Server)
oc new-build --name mssql-crud-app --binary --strategy docker
oc start-build mssql-crud-app --from-dir=. --follow

# Deploy (edit NAMESPACE in the YAML or use envsubst)
export NAMESPACE=$(oc project -q)
envsubst < openshift/deployment.yaml | oc apply -f -
```
