# Use an official Python runtime as a parent image
FROM python:3.10.12

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Poetry and project dependencies
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install