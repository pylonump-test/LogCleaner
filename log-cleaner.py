import os, json, time, zipfile
from datetime import datetime

def prepare_files(log_dir, archive_dir):
    # Get all archived files for current log directory
    archived_files = []
    files_date = []

    # Traverse all directories and subdirectories recursively
    for root, dirs, files in os.walk(log_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_time = round(os.stat(file_path).st_mtime)
            # If file is past archiving window
            if file_time < (current_time - archiving_window):
                file_date = datetime.fromtimestamp(file_time).strftime('%d%m%Y')
                if file_date not in files_date:
                    files_date.append(file_date)
                archived_files.append(file_path)

    # Get all deleted archives for current log directory
    deleted_files = []
    for archive_file in os.listdir(archive_dir):
        archive_path = os.path.join(archive_dir, archive_file)
        if os.path.isfile(archive_path):
            archive_time = round(os.stat(archive_path).st_mtime)
            # If archive is past deletion window
            if archive_time < (current_time - deletion_window):
                deleted_files.append(archive_path)

    data = {
        "files_date": files_date,
        "archived_files": archived_files,
        "deleted_files": deleted_files
    }
    return data

def archive_files(archived_files, log_dir, archive_dir):
    print(" Found " + str(len(archived_files)) + " log file(s) ready for archiving")
    print(" ------------------------------------------------------------------------")
    fail_counter = 0

    for file_path in archived_files:
        try:
            # Get the relative path of the file based on the log directory
            relative_path = os.path.relpath(file_path, log_dir)
            # Create the directory structure within the archive directory
            archive_subdir = os.path.join(archive_dir, os.path.dirname(relative_path))
            os.makedirs(archive_subdir, exist_ok=True)

            # Format the zip file name with the date
            file_date = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%d%m%Y')
            zip_file_path = os.path.join(archive_subdir, file_date + ".zip")

            # Write the file to the zip, preserving the directory structure
            with zipfile.ZipFile(zip_file_path, 'a', zipfile.ZIP_DEFLATED) as archive:
                archive.write(file_path, relative_path)
                os.remove(file_path)
        except Exception as e:
            print("Error archiving file " + file_path + ":" + e)
            fail_counter += 1

    print(" Archiving status: succeeded: " + str(len(archived_files) - fail_counter) + ", failures: " + str(fail_counter) + ", total: " + str(len(archived_files)));
    print("========================================================================")

def delete_files(deleted_files):
    print(" Found " + str(len(deleted_files)) + "archive(s) ready for deletion")
    print(" ------------------------------------------------------------------------")
    fail_counter = 0
    for deleted_file in deleted_files:
        try:
            os.remove(deleted_file);
        except Exception as e:
            print("Error deleting file " + deleted_file + ":" + e)
            fail_counter += 1
    print(" Deletion status: succeeded: " + str(len(deleted_files) - fail_counter) + ", failures: " + str(fail_counter) + ", total: " + str(len(deleted_files)))
    print("========================================================================")

if __name__ == "__main__":

    with open('config.json', 'r') as config_file:
        config_params = json.load(config_file)

    current_time = time.time()
    archiving_window = config_params['archiving_interval'] * 86400  # 7 Days
    deletion_window = config_params['deletion_interval'] * 86400  # 21 Days
    archives_dir = config_params['archives_dir']

    print("\nlog-cleaner running ...")
    for log_dir in config_params['log_dirs']:
        print("\nCurrent working directory: " + str(log_dir))
        archive_dir = os.path.join(archives_dir, os.path.basename(log_dir))
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)  # Ensure archive directory exists
        # Prepare files data
        data = prepare_files(log_dir, archive_dir)
        # Archiving Process
        if data["archived_files"]:
            print("\nStarting archiving process ...")
            archive_files(data["archived_files"], log_dir, archive_dir)
        else:
            print("\n-- No log files were found for archiving process!")
        # Deletion Process
        if data["deleted_files"]:
            print("\nStarting deletion process ...")
            delete_files(data["deleted_files"])
        else:
            print("\n-- No expired archives were found for deletion process!")
