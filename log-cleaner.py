import os, shutil, json, time, zipfile, subprocess
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

def log_archiving(configs, current_dir, parent_dir=None, subdir=False):

    # Record the start time
    start_time = time.time()

    # Record disk usage before archiving
    disk_usage_before = subprocess.check_output("du -sh", shell=True).decode().split()[0]

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
    
    # Get log file types
    file_types = configs['file_types']

    # Filter logs by archiving interval
    total_count = 0
    for file_name in os.listdir(current_dir):
        file_path = os.path.join(current_dir, file_name)
        if os.path.isfile(file_path):
            for file_type in file_types:
                if file_type in file_path:
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
    archive_count = 0
    print('   --- Logs detected: ' + str(total_count) + ' log(s)')
    for (current_dir, modification_date), files in log_files.items():
        zip_file_path = os.path.join(archives_dir, os.path.basename(current_dir), modification_date + ".zip")
        if not os.path.exists(zip_file_path):
            archive_count += 1
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

    print(colors.YELLOW + '   --- Archives created: ' + colors.END + str(archive_count)) 
    print('   ======================================================================================================')
    print(colors.BOLD + '   --- Archiving status: ' + colors.END + 'succeeded: ' + str(success_count) + ', failed: ' + str(fail_count) + ', total: ' + str(total_count))
    print('   ======================================================================================================\n')
    
    # Record the end time
    end_time = time.time()
    
    # Record disk usage after archiving
    disk_usage_after = subprocess.check_output("du -sh", shell=True).decode().split()[0]
    
    # Calculate elapsed time
    elapsed_time = calculate_elapsed_time(start_time, end_time)
    
    # Calculate disk usage difference
    disk_usage = calculate_disk_usage(disk_usage_before, disk_usage_after)
    
    # Report
    dir_status = {
        'dir': current_dir,
        'total_count': total_count,
        'fail_count': fail_count,
        'success_count': success_count,
        'archive_count': archive_count,
        'elapsed_time': elapsed_time,
        'disk_usage': disk_usage
    }

    return dir_status

def log_deletion(configs, current_dir, parent_dir=None, subdir=False):
    
    # Record the start time
    start_time = time.time()
    
    # Record disk usage before archiving
    disk_usage_before = subprocess.check_output("du -sh", shell=True).decode().split()[0]
    
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
    archive_count = 0
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

    # Record the end time
    end_time = time.time()
    
    # Record disk usage after archiving
    disk_usage_after = subprocess.check_output("du -sh", shell=True).decode().split()[0]
    
    # Calculate elapsed time
    elapsed_time = calculate_elapsed_time(start_time, end_time)
    
    # Calculate disk usage difference
    disk_usage = calculate_disk_usage(disk_usage_before, disk_usage_after)
    
    # Report
    dir_status = {
        'dir': current_dir,
        'total_count': total_count,
        'fail_count': fail_count,
        'success_count': success_count,
        'archive_count': archive_count,
        'elapsed_time': elapsed_time,
        'disk_usage': disk_usage
    }

    return dir_status

def calculate_elapsed_time(start_time, end_time):
    elapsed_time_diff = end_time - start_time
    # Convert elapsed time to a human-readable format
    elapsed_time = '{:.2f} seconds'.format(elapsed_time_diff)
    return elapsed_time

def calculate_disk_usage(disk_usage_before, disk_usage_after):
    disk_usage_diff = float(disk_usage_before[:-1]) - float(disk_usage_after[:-1])
    disk_usage_unit = disk_usage_after[-1]
    disk_usage = str(disk_usage_diff) + str(disk_usage_unit)
    return disk_usage

def calculate_status(status):
    total = 0
    fail = 0
    success = 0
    archive_count = 0
    for dir_status in status:
        total += dir_status['total_count']
        fail += dir_status['fail_count']
        success += dir_status['success_count']
        archive_count += dir_status['archive_count']
    all_status = {'total': total, 'fail': fail, 'success': success, 'archive_count': archive_count}
    return all_status

if __name__ == "__main__":
    
    report = {}

    # Record the start time
    start_time = time.time()
    report['start_time'] = time.strftime("%A, %B %d, %Y %I:%M:%S %p", time.localtime(start_time))

    # Record disk usage before LogCleaner
    disk_usage_before = subprocess.check_output("du -sh", shell=True).decode().split()[0]
    report['disk_usage_before'] = disk_usage_before

    # >---BEGIN--->>>

    print(colors.BOLD + '\n LogCleaner\n' + colors.END)
    print(colors.CYAN + ' - Execution started at: ' + colors.END + time.strftime("%A, %B %d, %Y %I:%M:%S %p", time.localtime(time.time())) + '\n')
    
    config_file= 'config.json'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, config_file)
    configs = load_configs(config_path)
    temp_dir = configs['archives_dir']

    report['archiving_interval'] = configs['archiving_interval']
    report['deletion_interval'] = configs['deletion_interval']
    
    print(colors.YELLOW + ' - Running archiving process ...\n' + colors.END)
    time.sleep(1)
    
    archiving_status = []
    for log_dir in configs['log_dirs']:
        configs['archives_dir'] = os.path.join(temp_dir, os.path.basename(os.path.dirname(log_dir)))
        if not os.path.exists(log_dir):
            print(colors.RED + '   --- Error: log directory does not exist: ' + log_dir + colors.END)
            continue
        log_subdirs = get_subdirs(log_dir)
        print(colors.MAGENTA + '   --- Current log directroy: ' + colors.END + log_dir + ' | ' + str(len(log_subdirs)) + ' subdir(s) detected!')
        print('   ======================================================================================================')
        dir_status = log_archiving(configs, log_dir)
        archiving_status.append(dir_status)
        count = 0
        for log_subdir in log_subdirs:
            count += 1
            print(colors.MAGENTA + '   --- [' + str(count) + '] Current log sub-directroy: ' + colors.END + log_subdir)
            print('   ======================================================================================================')
            dir_status = log_archiving(configs, log_subdir, log_dir, True)
            archiving_status.append(dir_status)

    print(colors.YELLOW + ' - Running deletion process ...\n' + colors.END)
    time.sleep(1)
    
    deletion_status = []
    archive_dirs = [os.path.join(temp_dir, archive_dir) for archive_dir in os.listdir(temp_dir)]
    for archive_dir in archive_dirs :
        configs['archives_dir'] = os.path.join(temp_dir, os.path.basename(os.path.dirname(archive_dir)))
        archive_subdirs = get_subdirs(archive_dir)
        print(colors.MAGENTA + '   --- Current archive directroy: ' + colors.END + archive_dir + ' | ' + str(len(archive_subdirs)) + ' subdir(s) detected!')
        print('   ======================================================================================================')
        dir_status = log_deletion(configs, archive_dir)
        deletion_status.append(dir_status)
        count = 0
        for archive_subdir in archive_subdirs:
            count += 1
            print(colors.MAGENTA + '   --- [' + str(count) + '] Current archive sub-directroy: ' + colors.END + archive_subdir)
            print('   ======================================================================================================')
            dir_status = log_deletion(configs, archive_subdir, archive_dir, True)
            deletion_status.append(dir_status)

    # <<<---END---<

    report['archiving_status'] = archiving_status
    report['deletion_status'] = deletion_status

    all_archiving_status = calculate_status(archiving_status)
    all_deletion_status = calculate_status(deletion_status)

    report['all_archiving_status'] = all_archiving_status
    report['all_deletion_status'] = all_deletion_status

    print(colors.CYAN + ' - LogCleaner Summary' + colors.END)
    print(' ======================================================================================================')
    print(colors.YELLOW + ' --- Archives created: ' + colors.END + str(all_archiving_status['archive_count'])) 
    print(colors.BOLD + ' --- Archving status: ' + colors.END + 'succeeded: ' + str(all_archiving_status['success']) + ', failed: ' + str(all_archiving_status['fail']) + ', total: ' + str(all_archiving_status['total']))
    print(' ======================================================================================================')
    print(colors.BOLD + ' --- Deletion status: ' + colors.END + 'succeeded: ' + str(all_deletion_status['success']) + ', failed: ' + str(all_deletion_status['fail']) + ', total: ' + str(all_deletion_status['total']))
    print(' ======================================================================================================\n')

    # Record the end time
    end_time = time.time()
    report['end_time'] = time.strftime("%A, %B %d, %Y %I:%M:%S %p", time.localtime(end_time))

    # Record disk usage after running the script
    disk_usage_after = subprocess.check_output("du -sh", shell=True).decode().split()[0]
    report['disk_usage_after'] = disk_usage_after
    
    # Calculate the elapsed time
    elapsed_time = calculate_elapsed_time(start_time, end_time)
    report['elapsed_time'] = elapsed_time
    print(colors.CYAN + ' - LogClenaer execution time: ' + colors.END + colors.BOLD + elapsed_time + colors.END + '\n')
    
    # Calculate disk usage difference
    disk_usage = calculate_disk_usage(disk_usage_before, disk_usage_after)
    report['disk_usage'] = disk_usage
    
    # Generate report
    report_filename = 'report-' + datetime.now().strftime('%d-%m-%Y') + '.json'
    report_file = os.path.join(configs['report_dir'], report_filename)
    with open(report_file, "w") as file:
        json.dump(report, file, indent=4)
    print(colors.CYAN + ' - Report generated' + colors.END + '\n')

