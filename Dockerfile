# 1. Use an official, lightweight Python 3.9 base image
FROM python:3.9-slim

# 2. Prevent Python from writing .pyc files to disk and enable unbuffered output for real-time logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Install essential OS-level dependencies (GCC & Curl needed for DuckDB/MotherDuck compiling)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy dependencies list and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the project source code into the container
COPY . .

# 7. Default command executed when running the container
CMD ["python", "main.py"]