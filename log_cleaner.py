import os, json, time, zipfile;
from datetime import datetime;

with open('config.json', 'r') as config_file:
    config_params = json.load(config_file);

current_time = time.time();
archiving_window = config_params['archiving_window'] * 86400;           # 7 Days
deletion_window = config_params['deletion_window'] * 86400;             # 21 Days

print("\nlog-cleaner running ...")
for log_directory in config_params['log_directories']:
    print("\nCurrent working directory: " + str(log_directory))
    # Define archive directory for current log directory
    archive_dir = os.path.join(log_directory, 'archives');
    if not os.path.exists(archive_dir):
        os.mkdir(archive_dir);
    # Get all archived files for current log directory
    archived_files = [];
    os.chdir(log_directory);
    for file_name in os.listdir('.'):
        file_path = os.path.join(os.getcwd(), file_name);
        if os.path.isfile(file_path):
            file_time = round(os.stat(file_path).st_mtime);
            # If file is past archiving window
            if file_time < (current_time - archiving_window):
                archived_files.append(os.path.join('./', file_path));
    # Get all deleted archives for current log directory
    deleted_files = [];
    os.chdir(archive_dir);
    for archive_file in os.listdir('.'):
        archive_path = os.path.join(os.getcwd(), archive_file);
        if os.path.isfile(archive_path):
            archive_time = round(os.stat(archive_path).st_mtime);
            # If archive is past deletion window
            if archive_time < (current_time - deletion_window):
                deleted_files.append(os.path.join('./', archive_path));
    # Archiving Process
    if archived_files:
        print("\nStarting archiving process ...")
        print(" Found " + str(len(archived_files)) + " log file(s) ready for archiving");
        print(" ------------------------------------------------------------------------")
        fail_counter = 0;
        archive_file_path = os.path.join(archive_dir, datetime.now().strftime('%d%m%Y%H%M') + '.zip');
        with zipfile.ZipFile(archive_file_path, 'w') as archive:
            for archived_file in archived_files:
                try:
                    archive.write(archived_file);
                    os.remove(archived_file);
                except:
                    fail_counter += 1;
        print(" Archiving status: succeeded: " + str(len(archived_files) - fail_counter) + ", failures: " + str(fail_counter) + ", total: " + str(len(archived_files)));
        print("========================================================================")
    else:
        print("\n-- No log files were found for archiving process!");
    # Deletion Process
    if deleted_files:
        print("\nStarting deletion process ...")
        print(" Found " + str(len(deleted_files)) + " archive(s) ready for deletion");
        print(" ------------------------------------------------------------------------")
        fail_counter = 0;
        for deleted_file in deleted_files:
            try:
                os.remove(deleted_file);
            except:
                fail_counter += 1;
        print(" Deletion status: succeeded: " + str(len(deleted_files) - fail_counter) + ", failures: " + str(fail_counter) + ", total: " + str(len(deleted_files)));
        print("========================================================================")
    else:
        print("\n-- No expired archives were found for deletion process!");
print('')
