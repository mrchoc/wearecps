#!/bin/bash

# Protects script from continuing with an error
set -eu -o pipefail

# Ensures environment variables are set
export DOCKER_INFLUXDB_INIT_MODE=$DOCKER_INFLUXDB_INIT_MODE
export DOCKER_INFLUXDB_INIT_USERNAME=$DOCKER_INFLUXDB_INIT_USERNAME
export DOCKER_INFLUXDB_INIT_PASSWORD=$DOCKER_INFLUXDB_INIT_PASSWORD
export DOCKER_INFLUXDB_INIT_ORG=$DOCKER_INFLUXDB_INIT_ORG
export DOCKER_INFLUXDB_INIT_BUCKET=$DOCKER_INFLUXDB_INIT_BUCKET
export DOCKER_INFLUXDB_INIT_RETENTION=$DOCKER_INFLUXDB_INIT_RETENTION
export DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=$DOCKER_INFLUXDB_INIT_ADMIN_TOKEN
export DOCKER_INFLUXDB_INIT_PORT=$DOCKER_INFLUXDB_INIT_PORT
export DOCKER_INFLUXDB_INIT_HOST=$DOCKER_INFLUXDB_INIT_HOST

# Start InfluxDB in the background
influxd &

# Wait for InfluxDB to be ready
echo "Waiting for InfluxDB to start..."
until curl -s http://${DOCKER_INFLUXDB_INIT_HOST}:8086/health | grep -q '"status":"pass"'; do
  echo "InfluxDB not ready yet, waiting..."
  sleep 2
done

echo "InfluxDB is ready! Running setup..."

# Check if InfluxDB is already set up
#if influx ping --host http://${DOCKER_INFLUXDB_INIT_HOST}:8086 &>/dev/null; then
  #echo "✅ InfluxDB instance detected. Skipping setup..."
#else
#  echo "🚀 Running initial InfluxDB setup..."
  influx setup --skip-verify \
    --bucket ${DOCKER_INFLUXDB_INIT_BUCKET} \
    --retention ${DOCKER_INFLUXDB_INIT_RETENTION} \
    --token ${DOCKER_INFLUXDB_INIT_ADMIN_TOKEN} \
    --org ${DOCKER_INFLUXDB_INIT_ORG} \
    --username ${DOCKER_INFLUXDB_INIT_USERNAME} \
    --password ${DOCKER_INFLUXDB_INIT_PASSWORD} \
    --host http://${DOCKER_INFLUXDB_INIT_HOST}:8086 \
    --force
#fi
# Conducts initial InfluxDB setup using the CLI
#influx setup --skip-verify \
  #--bucket ${DOCKER_INFLUXDB_INIT_BUCKET} \
  #--retention ${DOCKER_INFLUXDB_INIT_RETENTION} \
  #--token ${DOCKER_INFLUXDB_INIT_ADMIN_TOKEN} \
  #--org ${DOCKER_INFLUXDB_INIT_ORG} \
  #--username ${DOCKER_INFLUXDB_INIT_USERNAME} \
  #--password ${DOCKER_INFLUXDB_INIT_PASSWORD} \
  #--host http://${DOCKER_INFLUXDB_INIT_HOST}:8086 \
  #--force

echo "Setup complete! InfluxDB is running."

# Keep the container running by bringing influxd to foreground
wait
