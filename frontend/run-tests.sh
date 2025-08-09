#!/bin/bash

# Start services
../docker-dev.sh start

# Run tests
docker-compose run --rm tests

# Stop services
../docker-dev.sh stop
