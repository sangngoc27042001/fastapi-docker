# Use the python:slim image as the base (replace version if needed)
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy all application files and requirements.txt
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Expose the port used by your FastAPI app (usually 8000)
EXPOSE 8000

# Run the Uvicorn server using CMD
CMD [ "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
