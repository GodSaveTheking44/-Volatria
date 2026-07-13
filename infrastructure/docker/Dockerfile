FROM python:3.12-slim

# Install system build dependencies for C++ matching engine compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy python dependencies definitions
COPY pyproject.toml CMakeLists.txt ./
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Compile C++ shared libraries and install Python package in production mode
RUN pip install --no-cache-dir -e ".[dev]"

EXPOSE 8000

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
