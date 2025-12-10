FROM node:18-alpine

WORKDIR /app

# Copy package files first (for better Docker layer caching)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Set environment variable for API URL (can be overridden)
ENV VITE_API_URL=http://backend:8000

# Run development server with host binding for Docker
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


