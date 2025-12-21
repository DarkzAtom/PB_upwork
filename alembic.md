# Packages

List of things to install (also present in `requirements_alembic.txt`).

```
pip install python-dotenv sqlalchemy psycopg2
pip install alembic
```

# Alembic commands

Create revision after changing models

```
alembic revision --autogenerate -m "Description of revision"
```

Apply the most recent revision

```
alembic upgrade head
```

Print current revision

```
alembic current
```

Downgrade to previous revision

```
alembic downgrade -1
```

Upgrade to next revision

```
alembic upgrade +1
```

Downgrade to initial state

```
alembic downgrade base
```