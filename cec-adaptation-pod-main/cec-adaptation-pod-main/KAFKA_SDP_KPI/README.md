# KAFKA_SDP_KPI Module

## Overview
The KAFKA_SDP_KPI module is responsible for processing SDP KPI (Key Performance Indicator) data and publishing it to Kafka topics for both Polaris and Titan environments.

## Features
- **KPI Data Processing**: Reads KPI data from text files and converts to JSON format
- **Dual Environment Support**: Publishes to both Polaris and Titan Kafka clusters
- **Data Archiving**: Automatically archives processed files with timestamps
- **Error Handling**: Comprehensive error handling for Kafka connections and message publishing
- **Status Tracking**: Tracks success/failure status for each KPI message

## Configuration
The module uses the following configuration:
- **Kafka IPs**: Configurable IP addresses for Polaris and Titan environments
- **Port**: Kafka broker port (default: 9092)
- **Topic**: Kafka topic for publishing messages
- **Paths**: Source and archive directory paths

## Usage
```bash
python kafka_sdpkpi.py -d <kafka_ip> -p <kafka_port>
```

## Input Format
Expects KPI data in CSV format with the following fields:
- Field 1: (unused)
- Field 2: KPI name
- Field 3: KPI value
- Field 4: (unused)
- Field 5: KPI last updated date
- Field 6: Source modification date
- Field 7: Local modification date

## Output
- **JSON Messages**: Publishes formatted KPI data to Kafka topics
- **Status Files**: Creates archive files with processing status
- **Logs**: Console output showing processing progress and results

## Dependencies
- kafka-python
- Standard Python libraries (json, subprocess, socket, datetime)

## Integration
This module is integrated into the cec-adaptation-pod codebase and can be selected for modernization through the frontend interface. 