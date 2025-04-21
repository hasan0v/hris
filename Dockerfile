# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by Python packages
# (e.g., build tools, libraries for Pillow if image processing was needed)
# Add any required packages here, e.g., RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy only requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Make port 5000 available to the world outside this container
# (The actual port mapping happens in docker-compose.yml)
EXPOSE 5000

# Define environment variable for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
# Set FLASK_ENV=production in docker-compose for production builds

# Create the upload directory if it doesn't exist
# Note: This assumes UPLOAD_PATH in config.py points relative to the app directory
RUN mkdir -p uploads

# Run the application using Flask's built-in server (for development)
# For production, use a proper WSGI server like Waitress
# Use waitress-serve to run the app (including SocketIO)
# The host and port are typically managed by Docker/docker-compose
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "app:app"]
