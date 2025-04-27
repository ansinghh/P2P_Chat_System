# Use official Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy entire project into the image
COPY . .

# Install wheel package from dist/
RUN pip install --upgrade pip
RUN pip install ./dist/p2pchat-0.1.0-py3-none-any.whl

# Optional: Set env variables for unbuffered output
ENV PYTHONUNBUFFERED=1

# Command to run (you can change to client.py if needed)
CMD ["python", "-m", "p2pchat.discovery_server"]
