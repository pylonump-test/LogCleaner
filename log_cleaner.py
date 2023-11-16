import os, json, time, zipfile;
from datetime import datetime;

def prepare_files(log_dir, archive_dir):
    # Get all archived files for current log directory
    archived_files = [];
    files_date = [];
    os.chdir(log_dir);
    for file_name in os.listdir('.'):
        file_path = os.path.join(os.getcwd(), file_name);
        if os.path.isfile(file_path):
            file_time = round(os.stat(file_path).st_mtime);
            # If file is past archiving window
            if file_time < (current_time - archiving_window):
                file_date = datetime.fromtimestamp(file_time).date()
                if file_date not in files_date:
                    files_date.append(file_date)
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
    data = {
        "files_date": files_date,
        "archived_files": archived_files,
        "deleted_files": deleted_files
    }
    return data

def archive_files(archived_files, files_date):
    print(" Found " + str(len(archived_files)) + " log file(s) ready for archiving");
    print(" ------------------------------------------------------------------------")
    fail_counter = 0;
    for file_date in files_date:
        archive_file_path = os.path.join(archive_dir, file_date.strftime('%d%m%Y') + '.zip');
        with zipfile.ZipFile(archive_file_path, 'w') as archive:
            for archived_file in archived_files:
                if os.path.isfile(archived_file):
                    archived_file_time = round(os.stat(archived_file).st_mtime);
                    archived_file_date = datetime.fromtimestamp(archived_file_time).date()
                    if archived_file_date == file_date:
                        try:
                            archive.write(archived_file);
                            os.remove(archived_file);
                        except:
                            fail_counter += 1;
    print(" Archiving status: succeeded: " + str(len(archived_files) - fail_counter) + ", failures: " + str(fail_counter) + ", total: " + str(len(archived_files)));
    print("========================================================================")

def delete_files(deleted_files):
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

if __name__ == "__main__":
    
    with open('config.json', 'r') as config_file:
        config_params = json.load(config_file);
    
    current_time = time.time();
    archiving_window = config_params['archiving_window'] * 86400;           # 7 Days
    deletion_window = config_params['deletion_window'] * 86400;             # 21 Days

    print("\nlog-cleaner running ...")
    for log_dir in config_params['log_directories']:
        print("\nCurrent working directory: " + str(log_dir))
        archive_dir = os.path.join(log_dir, 'archives');
        if not os.path.exists(archive_dir):
            os.mkdir(archive_dir);
        # Prepare files data
        data = prepare_files(log_dir, archive_dir)
        # Archiving Process
        if data["archived_files"]:
            print("\nStarting archiving process ...")
            archive_files(data["archived_files"], data["files_date"])
        else:
            print("\n-- No log files were found for archiving process!");
        # Deletion Process
        if data["deleted_files"]:
            print("\nStarting deletion process ...")
            delete_files(data["deleted_files"])
        else:
            print("\n-- No expired archives were found for deletion process!");

