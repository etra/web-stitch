# Use a lightweight Python image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install system libraries required by OpenCV and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .

# Use Gunicorn to run the app
# 'app:app' means look for a file named app.py with a variable named app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "stitch:create_app('production')"]