# LogCleaner

[![Python Version](https://img.shields.io/badge/Python-2%20%7C%203-blue.svg)](https://www.python.org/)

# Table of Contents

1. [Project Overview](#1-project-overview)
2. [Features](#2-features)
3. [Dependencies](#3-dependencies)
4. [Installation](#4-installation)
5. [Usage](#5-usage)
   - 5.1. [Archiving Process](#51-archiving-process)
   - 5.2. [Deletion Process](#52-deletion-process)
   - 5.3. [Logging Process](#53-logging-process)
6. [JSON Configuration](#6-json-configuration)
7. [Scheduling with Crontab](#7-scheduling-with-crontab)

## 1. Project Overview
**Project Name**: LogCleaner  
**Objective**: Efficiently manage, archive, and clean log files across various software environments.  
**Scope**: LogCleaner automates the monitoring, archiving, and deletion of log files to optimize system storage and performance. It supports both Python 2 and Python 3 and offers flexible configurations for various file management strategies.

## 2. Features
- **Log File Archiving**: Automatically archives log files into `.zip` format after a specified retention period.
- 
- **Compression Algorithm**: The logs are compressed using the **DEFLATE** algorithm, which is the default compression method for ZIP archives in Python.
- **Log Cleanup**: Removes outdated log files and archives based on configurable time intervals.
- **Python Compatibility**: Supports both Python 2 and Python 3 environments.
- **Dynamic Configuration**: Easily customizable via a `config.json` file for directory paths, file types, and retention policies.

## 3. Dependencies
LogCleaner is a Python-based project compatible with **[Python 2.x](https://www.python.org/downloads/release/python-2718/)** and **[Python 3.x](https://www.python.org/downloads/)**.

- **os, shutil**: Core Python libraries for managing file operations like deletion and directory navigation.
- **zipfile**: Built-in Python module for creating `.zip` archives of log files.
- **collections.defaultdict**: Part of the collections module, which provides specialized container types.
- **difflib.SequenceMatcher**: Provides tools to compare sequences, often used for string comparison.

## 4. Installation

### Step 1: Download the Release
- Go to the [releases](https://github.com/pylonump-test/LogCleaner/releases/latest) page of the GitHub repository.
- Download the latest release: `LogCleaner-v1.1.zip`.

### Step 2: Extract Files
- Extract `LogCleaner-v1.1.zip` to a directory of your choice, e.g., `/usr/local/LogCleaner`.

      LogCleaner/
      ├── log-cleaner.py
      ├── config.json
      ├── README.md

### Step 3: Configure the Application
- Modify the `config.json` file to suit your environment:

      {
          "archiving_interval": 7,
          "deletion_interval": 21,
          "working_dir": "/path/to/LogCleaner/dir",
          "archives_dir": "/path/to/archives/dir",
          "log_dirs": [
              "/path/to/log/dir",
              "/path/to/another/log/dir"
          ],
          "file_types": [
              "applog",
              "errorlog"
          ]
      }

> **Note:** The `archiving_interval` and `deletion_interval` are defined in days.

### Step 4: Run the Application
Navigate to the LogCleaner directory and run the script:

For Python 2.x:

    python log-cleaner.py

For Python 3.x:

    python3 log-cleaner.py

## 5. Usage

- **Archiving**: LogCleaner compresses log files that exceed the `archiving_interval` (in days) into `.zip` files in the designated `archives_dir`.
- **Deletion**: Archived files exceeding the `deletion_interval` are automatically deleted to free up space.
- **Logging**: Real-time feedback is provided during the archiving and deletion process.

### 5.1. Archiving Process

- **File Format:** .zip
- **Compression Algorithm:** DEFLATE (via `zipfile.ZIP_DEFLATED`)
- **Grouping by Date:** Log files are grouped together based on their modification date. Files with the same date are archived into a single ZIP file.
- **Example Archive Names:**
  - `logs-08-10-2024.zip` (for logs modified on October 8, 2024)
  - `logs-09-10-2024.zip` (for logs modified on October 9, 2024)

This ensures that logs from the same day are efficiently bundled into one archive file, making it easier to manage and retrieve logs based on dates.

### 5.2. Deletion Process

- **Retention Policy**: LogCleaner automatically deletes archived files that exceed the `deletion_interval`. This interval is defined in days, and older archives are removed to maintain disk space efficiency.
- **Example Deletion:** If the `deletion_interval` is set to 30 days, any archive older than 30 days will be automatically deleted.

### 5.3. Logging Process

- **Real-Time Feedback**: LogCleaner offers real-time feedback during both archiving and deletion operations, ensuring transparency throughout the process.
  - **Archived Files**: Each file that is archived is logged with its name and the date of archiving.
  - **Deleted Files**: Files that are deleted are recorded along with their deletion date.
  - **Errors**: Any errors encountered during the process are documented with detailed descriptions to facilitate troubleshooting.

- **Report Generation**: Upon completion of the log cleaning process, LogCleaner generates a comprehensive report detailing:
  - **Archived Logs**: A list of all log files that were archived, including their names and sizes.
  - **Deleted Logs**: A list of all log files that were deleted, including their names and deletion dates.
  - **Resource Savings**: An overview of the total disk space reclaimed through archiving and deletion, helping users understand the efficiency gains.
  - **Processing Time**: The total time taken to complete the archiving and deletion operations, providing insights into the performance of the LogCleaner tool.

These reports are saved in the` working_dir`, providing a historical record of all operations for future reference and auditing purposes.

## 6. JSON Configuration

LogCleaner uses a `config.json` file to manage settings for log directories, file types, and archiving/deletion policies. Here’s a breakdown of the configuration options:

| Configuration      | Description                                                     |
| ------------------ | --------------------------------------------------------------- |
| `archiving_interval` | Number of days allowed for log files before archiving.           |
| `deletion_interval`  | Number of days allowed for log archives before deletion.         |
| `working_dir`        | Path to the working directory where LogCleaner operates.         |
| `archives_dir`       | Path to the directory where archives are stored.                |
| `log_dirs`           | A list of directories containing the log files to be managed.   |
| `file_types`         | A list of allowed file-name extensions for log files (e.g., `.txt`). |

## 7. Scheduling with Crontab

To run LogCleaner automatically, you can set up a cron job. For example, to schedule LogCleaner to run daily at 3:00 AM, follow these steps:

1. Open crontab:

       crontab -e

2. Add the following line to schedule LogCleaner:

       0 3 * * * /usr/bin/python3 /path/to/log-cleaner.py
