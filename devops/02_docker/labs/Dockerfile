# Use an official Python runtime as a parent image
# We use 'alpine' or 'slim' variants in DevOps to keep image sizes small and reduce security attack surface.
FROM python:3.9-slim

# Set the working directory to /app inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY app.py /app/

# Make port 8000 available to the world outside this container
# Note: EXPOSE is mostly for documentation. You still have to map the port when running.
EXPOSE 8000

# Run app.py when the container launches
CMD ["python", "app.py"]
