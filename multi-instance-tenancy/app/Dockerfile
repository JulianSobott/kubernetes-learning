FROM python:3.10

ENV POETRY_VERSION=1.1.13
ENV PYTHONBUFFERED=0
RUN pip install poetry==$POETRY_VERSION
RUN poetry config virtualenvs.in-project true --local

WORKDIR /code
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-dev
COPY example_app /code/app

EXPOSE 80
CMD ["poetry", "run", "python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
