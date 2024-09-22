# Docker files used by docker-compose files to build docker images.
DOCKER_FILES = {
    'python': """
    FROM python:3.9-slim
    WORKDIR /app
    COPY . /app
    RUN pip install --no-cache-dir -r requirements.txt
    CMD ["python", "app.py"]
    """,
    'golang': """
    FROM golang:1.16-alpine
    WORKDIR /app
    COPY . /app
    RUN go mod tidy
    CMD ["go", "run", "main.go"]
    """,
    'javascript': """
    FROM node:14-alpine
    WORKDIR /app
    COPY . /app
    RUN npm install
    CMD ["node", "app.js"]
    """,
    'c++': """
    FROM gcc:10
    WORKDIR /app
    COPY . /app
    RUN g++ -o app app.cpp
    CMD ["./app"]
    """,
    'c': """
    FROM gcc:10
    WORKDIR /app
    COPY . /app
    RUN gcc -o app app.c
    CMD ["./app"]
    """,
    'c#': """
    FROM mcr.microsoft.com/dotnet/sdk:5.0 AS build
    WORKDIR /app
    COPY . /app
    RUN dotnet publish -c Release -o out

    FROM mcr.microsoft.com/dotnet/aspnet:5.0
    WORKDIR /app
    COPY --from=build /app/out .
    ENTRYPOINT ["dotnet", "app.dll"]
    """,
    'rust': """
    FROM rust:1.51
    WORKDIR /app
    COPY . /app
    RUN cargo build --release
    CMD ["./target/release/app"]
    """,
    'ruby': """
    FROM ruby:2.7-slim
    WORKDIR /app
    COPY . /app
    RUN bundle install
    CMD ["ruby", "app.rb"]
    """
}
from typing import Optional # noqa: F401