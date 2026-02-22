# Use a lightweight Python image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install system libraries required by OpenCV and Pillow,
# plus Unicode fonts for PDF generation (Cyrillic, CJK, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    fonts-dejavu-core \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .

# Create uploads directory for user-uploaded images (reference images, wizard temp files)
RUN mkdir -p /app/uploads

# Use Gunicorn to run the app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "stitch:create_app('production')"]