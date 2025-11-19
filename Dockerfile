# Use lightweight Python image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose the port Flask will run on
EXPOSE 5000

# Run flask app (adjust app.py or wsgi.py if needed)
CMD ["flask", "run", "--host=0.0.0.0"]
