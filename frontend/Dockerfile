# Development Dockerfile for AITM Frontend
FROM node:18-alpine

WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 41241

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:41241/ || exit 1

# Start the development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "41241"]
