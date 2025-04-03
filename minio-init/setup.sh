#!/bin/sh

# Wait for MinIO to be ready
echo "Waiting for MinIO to be ready..."
until mc alias set myminio http://minio:9000 minioadmin minioadmin; do
  echo "MinIO not ready yet, waiting..."
  sleep 1
done

echo "MinIO is ready! Creating bucket..."

# Create the bucket if it doesn't exist already
mc mb --ignore-existing myminio/temp-charts

# Set bucket policy to public (if needed)
# mc policy set public myminio/temp-charts

echo "MinIO initialization completed successfully!" 