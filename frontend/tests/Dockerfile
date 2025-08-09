# Dockerfile for running Playwright tests
FROM mcr.microsoft.com/playwright:v1.32.1-jammy as base

FROM node:18-slim

COPY --from=base / /

USER root

RUN apt-get update && \
    apt-get install -y nodejs

USER pwuser

WORKDIR /app

# Copy source code
COPY . .

# Install dependencies
RUN npm install

# Run tests
CMD ["npx", "playwright", "test"]
