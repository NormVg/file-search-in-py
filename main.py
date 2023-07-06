import os, subprocess, jellyfish, psutil, threading, time

start = time.time()

def get_available_drives():
    drives = []
    for drive in psutil.disk_partitions():
        if drive.opts and 'rw' in drive.opts:
            drives.append(drive.mountpoint)
    return drives

def cache_drives(drives):
    drive_cache = {}
    for drive in drives:
        drive_cache[drive] = set(os.listdir(drive))
    return drive_cache

def search_drive(drive, target_name, threshold, results, drive_cache, lock):
    similar_files = []
    cached_files = drive_cache.get(drive, set())

    for root, dirs, files in os.walk(drive):
        for file in files:
            file_path = os.path.join(root, file)
            if file in cached_files:
                similarity = jellyfish.jaro_winkler(target_name, file)
                if similarity >= threshold:
                    similar_files.append((file, similarity, file_path))
            else:
                similarity = jellyfish.jaro_winkler(target_name, file)
                if similarity >= threshold:
                    similar_files.append((file, similarity, file_path))
                    cached_files.add(file)

    with lock:
        results.extend(similar_files)

drives = get_available_drives()

target_name = "Charles V1 png"
threshold = 0.9

results = []
lock = threading.Lock()

# Cache the drives
drive_cache = cache_drives(drives)

threads = []
for idx, drive in enumerate(drives):
    thread = threading.Thread(target=search_drive, args=(drive, target_name, threshold, results, drive_cache, lock))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()

similar_files = sorted(results, key=lambda x: x[1], reverse=True)
if similar_files:
    file, similarity, file_path = similar_files[0]
    folder_path = os.path.dirname(file_path)
    print(f"File: {file}, Similarity: {similarity:.2f}, Path: {file_path}")
    subprocess.Popen(f'explorer /select,"{file_path}"')

end = time.time()
print(f"Entire process took: {end - start}")
