# Use a lightweight base image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy the requirements and install dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy the application code
COPY . .

# Expose the port your application runs on
EXPOSE 8000

# Define the command to start your app
CMD ["python", "app.py"]
