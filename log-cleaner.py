import os, shutil, json, time, zipfile
from collections import defaultdict
from difflib import SequenceMatcher
from datetime import datetime

# ANSI color codes
class colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def load_configs(config_path):
    print(colors.YELLOW + ' - Checking config file ' + config_path + ' ...' + colors.END)
    time.sleep(1)
    if not os.path.exists(config_path):
        print(colors.RED + '   --- Error: No such file or directory\n' + colors.END)
        exit()
    else:
        with open(config_path, 'r') as file:
            try:
                configs = json.load(file)
            except ValueError as err:
                print(colors.RED + '   --- Error: Invalid JSON: ' + colors.END + str(err) + '\n')
                exit()
            else:
                print(colors.GREEN + '   --- Success: Configs loaded' + colors.END)
                print('   --- Config: archiving_interval is set to: ' + str(configs['archiving_interval']) + ' day(s)')
                print('   --- Config: deletion_interval is set to: ' + str(configs['deletion_interval']) + ' day(s)')
                print('   --- Config: archives_dir is set to: ' + str(configs['archives_dir']))
                print('   --- Config: log_dirs targeted ...')
                for log_dir in configs['log_dirs']:
                    print('               - log_dir: ' + str(log_dir))
                print('')
                return configs

def get_subdirs(parent_dir):
    subdirs = []
    for root, dirs, files in os.walk(parent_dir):
        for dir_name in dirs:
            subdir_path = os.path.join(root, dir_name)
            rel_path = os.path.relpath(subdir_path, parent_dir)
            subdirs.append(subdir_path)
    return subdirs

def get_dir_diff(dir1, dir2):
    # Initialize SequenceMatcher with the two directories
    matcher = SequenceMatcher(None, dir1, dir2)
    # Get the differences between the two directories
    diffs = list(matcher.get_opcodes())
    # Extract the differing parts
    diff_parts = []
    for tag, i1, i2, j1, j2 in diffs:
        if tag != 'equal':
            diff_parts.append((tag, dir1[i1:i2], dir2[j1:j2]))
    # Get the 2nd directory path difference
    for tag, d1, d2 in diff_parts:
        diff = os.path.join(os.path.basename(dir1), d2[1:])
    return diff

def log_archiving(current_dir, parent_dir=None, subdir=False):
    # Define archiving interval and archiving directory
    print('   --- Fetching archive info ...')
    archiving_interval = configs['archiving_interval']
    archives_dir = configs['archives_dir']
    if subdir:
        dir_diff = get_dir_diff(parent_dir, current_dir)
        archives_dir = os.path.join(archives_dir, os.path.dirname(dir_diff))
    # Dictionary to store logs grouped by their modification date
    log_files = defaultdict(list)
    # Create the corresponding directory in the archives directory
    archive_dir = os.path.join(archives_dir, os.path.basename(current_dir))
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    # Filter logs by archiving interval
    total_count = 0
    for file_name in os.listdir(current_dir):
        file_path = os.path.join(current_dir, file_name)
        if os.path.isfile(file_path):
            # Get the log's modification time in seconds since the epoch
            file_mtime = os.path.getmtime(file_path)
            # Calculate the age of the logs in days
            age_in_days = (time.time() - file_mtime) / (24 * 3600)
            if age_in_days > archiving_interval:
                # Get the modification date of the logs (DD-MM-YYYY format)
                modification_date = time.strftime("%d-%m-%Y", time.localtime(file_mtime))
                log_files[(current_dir, modification_date)].append(file_path)
                total_count += 1
    # Archive logs
    fail_count = 0
    success_count = 0
    print('   --- Logs detected: ' + str(total_count) + ' log(s)')
    for (current_dir, modification_date), files in log_files.items():
        zip_file_path = os.path.join(archives_dir, os.path.basename(current_dir), modification_date + ".zip")
        with zipfile.ZipFile(zip_file_path, "a", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files:
                rel_path = os.path.join(modification_date, os.path.basename(file_path))
                try:
                    print('   --- Archiving log: ' + file_path)
                    zipf.write(file_path, rel_path)
                except (IOError, zipfile.BadZipfile) as err:
                    fail_count += 1
                    print(colors.RED + '   --- Error: Failed to write zip file: ' + colors.END + str(err))
                else:
                    os.remove(file_path)
                    success_count += 1
                    print(colors.GREEN + '   --- Success: Log archived: ' + colors.END + zip_file_path)

    print('   ======================================================================================================')
    print(colors.BOLD + '   --- Archiving status: ' + colors.END + 'succeeded: ' + str(success_count) + ', failed: ' + str(fail_count) + ', total: ' + str(total_count))
    print('   ======================================================================================================\n')

def log_deletion(current_dir, parent_dir=None, subdir=False):
    # Define deletion interval and archiving directory
    print('   --- Fetching archive info ...')
    deletion_interval = configs['deletion_interval']
    archives_dir = configs['archives_dir']
    if subdir:
        dir_diff = get_dir_diff(parent_dir, current_dir)
        archives_dir = os.path.join(archives_dir, os.path.dirname(dir_diff))
    # List to store archives
    archives = []
    # Filter archives by deletion interval
    total_count = 0
    for file_name in os.listdir(current_dir):
        file_path = os.path.join(current_dir, file_name)
        if os.path.isfile(file_path):
            # Get the archive's modification time in seconds since the epoch
            file_mtime = os.path.getmtime(file_path)
            # Calculate the age of the archive in days
            age_in_days = (time.time() - file_mtime) / (24 * 3600)
            if age_in_days > deletion_interval:
                # Get the modification date of the archive (DD-MM-YYYY format)
                archives.append(file_path)
                total_count += 1
    # Delete archives
    fail_count = 0
    success_count = 0
    print('   --- Archives detected: ' + str(total_count) + ' archives(s)')
    for archive in archives:
        try:
            print('   --- Deleting archive: ' + file_path)
            os.remove(archive)
        except OSError as err:
            fail_count += 1
            print(colors.RED + '   --- Error: Failed to delete archive: ' + colors.END + str(err))
        else:
            success_count += 1
            print(colors.GREEN + '   --- Success: archive deleted: ' + colors.END)

    print('   ======================================================================================================')
    print(colors.BOLD + '   --- Deletion status: ' + colors.END + 'succeeded: ' + str(success_count) + ', failed: ' + str(fail_count) + ', total: ' + str(total_count))
    print('   ======================================================================================================\n')

if __name__ == "__main__":
    # Record the start time
    start_time = time.time()

    print(colors.BOLD + '\n LogCleaner\n' + colors.END)
    print(colors.CYAN + ' - Execution started at: ' + colors.END + time.strftime("%A, %B %d, %Y %I:%M:%S %p", time.localtime(time.time())) + '\n')
    
    config_file= 'config.json'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, config_file)
    configs = load_configs(config_path)
    
    print(colors.YELLOW + ' - Running archiving process ...\n' + colors.END)
    time.sleep(1)

    for log_dir in configs['log_dirs']:
        if not os.path.exists(log_dir):
            print(colors.RED + '   --- Error: log directory does not exist: ' + log_dir + colors.END)
            continue
        log_subdirs = get_subdirs(log_dir)
        print(colors.MAGENTA + '   --- Current log directroy: ' + colors.END + log_dir + ' | ' + str(len(log_subdirs)) + ' subdir(s) detected!')
        print('   ======================================================================================================')
        log_archiving(log_dir)
        count = 0
        for log_subdir in log_subdirs:
            count += 1
            print(colors.MAGENTA + '   --- [' + str(count) + '] Current log sub-directroy: ' + colors.END + log_subdir)
            print('   ======================================================================================================')
            log_archiving(log_subdir, log_dir, True)
    
    print(colors.YELLOW + ' - Running deletion process ...\n' + colors.END)
    time.sleep(1)
    
    archive_dirs = [os.path.join(configs['archives_dir'], archive_dir) for archive_dir in os.listdir(configs['archives_dir'])]
    for archive_dir in archive_dirs :
        archive_subdirs = get_subdirs(archive_dir)
        print(colors.MAGENTA + '   --- Current archive directroy: ' + colors.END + archive_dir + ' | ' + str(len(archive_subdirs)) + ' subdir(s) detected!')
        print('   ======================================================================================================')
        log_deletion(archive_dir)
        count = 0
        for archive_subdir in archive_subdirs:
            count += 1
            print(colors.MAGENTA + '   --- [' + str(count) + '] Current archive sub-directroy: ' + colors.END + archive_subdir)
            print('   ======================================================================================================')
            log_deletion(archive_subdir, archive_dir, True)

    # Record the end time
    end_time = time.time()

    # Calculate the elapsed time
    elapsed_time = end_time - start_time
    # Convert elapsed time to a human-readable format
    elapsed_time_str = '{:.2f} seconds'.format(elapsed_time)
    
    # Display the elapsed time
    print(colors.CYAN + ' - LogClenaer execution time: ' + colors.END + colors.BOLD + elapsed_time_str + colors.END + '\n')
