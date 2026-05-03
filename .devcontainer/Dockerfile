FROM mcr.microsoft.com/devcontainers/python:3.12

# Install Java (required by saspy for IOM connections to SAS 9.4)
RUN apt-get update && apt-get install -y default-jdk && rm -rf /var/lib/apt/lists/*
