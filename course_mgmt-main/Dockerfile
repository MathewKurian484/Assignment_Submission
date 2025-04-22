FROM python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY course_mgmt-main/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY course_mgmt-main/app.py .
COPY course_mgmt-main/templates/ templates/

# Expose port
EXPOSE 8002

# Start the application
CMD ["python", "app.py"] 