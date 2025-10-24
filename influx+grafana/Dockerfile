# Use official Python image (multi-arch friendly)
FROM python:3.10-slim
# Set working directory inside container
WORKDIR /app
# Copy the Python script into the container
COPY dummystream.py .
COPY sensors.py .
COPY requirements.txt .
COPY max6675.py .
COPY ds18b20.py .
# Install curl for health checking
RUN apt-get update && apt-get install -y curl build-essential && rm -rf /var/lib/apt/lists/*
# Install required Python packages
RUN pip install -r requirements.txt
# Wait for InfluxDB to be ready, then run the script
CMD ["/bin/bash", "-c", "while ! curl -s http://influxdb:8086/health | grep -q '\"status\":\"pass\"'; do echo 'Waiting for InfluxDB to be ready...'; sleep 2; done && echo 'InfluxDB is ready! Starting data streamer...' && python dummystream.py"]
