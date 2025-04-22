FROM node:18-alpine

WORKDIR /app

# Copy package files for backend
COPY package*.json ./

# Install backend dependencies
RUN npm install

# Copy backend code
COPY server.js ./

# Set up frontend
WORKDIR /app/frontend/pdf-uploader

# Copy frontend package files
COPY frontend/pdf-uploader/package*.json ./

# Install frontend dependencies
RUN npm install

# Copy frontend code
COPY frontend/pdf-uploader/ .

# Build frontend
RUN npm run build

# Go back to main directory
WORKDIR /app

# Expose port
EXPOSE 8001

# Start the application
CMD ["node", "server.js"] 