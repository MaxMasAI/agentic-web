FROM python:3.12-slim

# Install system dependencies required for PySide6 / Qt to run in Docker
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libegl1 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-keysyms1 \
    libxcb-shape0 \
    libxcb-xinerama0 \
    libx11-xcb1 \
    libxcb-util1 \
    libxcb-render-util0 \
    libxcb-image0 \
    libfontconfig1 \
    libfreetype6 \
    libxrender1 \
    libxext6 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Default command to start the PySide6 app
CMD ["python", "app.py"]
