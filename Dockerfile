FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy all files from the current directory to the container's /app directory
COPY . /app

# Upgrade pip
RUN pip install --upgrade pip

# Install dependencies from requirements.txt
RUN pip install -r requirements.txt

# Expose port 80
EXPOSE 80

# Run the FastAPI app using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]