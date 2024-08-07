# Use an official Python runtime as a parent image
FROM python:3.10.14

# Install PostgreSQL client and other dependencies
RUN apt-get update && apt-get install -y postgresql-client

# Set the working directory in the container
ENV PYTHONPATH=/app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install poetry
RUN pip install poetry

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Make port 5000 available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches
CMD ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "-w", "1", "-b", "0.0.0.0:8000", "main:app"]