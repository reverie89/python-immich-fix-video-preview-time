# pip install psycopg2 (postgres connector)

import os, sys, subprocess, psycopg2
from datetime import timedelta

ffprobe_path = "D:\\ffmpeg-2023-06-19-git-1617d1a752-essentials_build\\bin\\ffprobe.exe"
# Connect to PostgreSQL
conn = psycopg2.connect(
    database="immich",
    user="postgres",
    password="password",
    host="hostname or ip",
    port="5432"
)

root_directory = sys.argv[1]

def get_last_directory(path):
    # Split the path into individual directory components
    directories = path.split(os.sep)
    
    # Filter out empty directory names
    directories = [directory for directory in directories if directory]

    # Return the last directory name
    return directories[-1]

if len(root_directory) == 0:
    print("argument required for path to immich library")
    sys.exit()

print(root_directory)

def is_video_file(filename):
    video_extensions = ['mp4', 'mkv', 'avi', 'wmv', 'flv', 'mov']  # Add more video extensions if needed
    file_extension = filename.split('.')[-1].lower()
    return file_extension in video_extensions

def get_video_duration(filename):
    duration_result = subprocess.run(
        [ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
         filename],
        capture_output=True, text=True, shell=True)
    if duration_result.returncode == 0:
        try:
            duration = float(duration_result.stdout)
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = round(duration % 60, 3)

            duration_str = "{:02d}:{:02d}:{:06.3f}".format(hours, minutes, seconds)
            return duration_str

        except ValueError:
            print(f"Error: Unable to parse video duration for: {filename}")
            return None

    else:
        print("Error: ", duration_result.stderr)
        return None

# Create a cursor
cursor = conn.cursor()

i = 0
# Find all video files from the root directory
for root, dirs, files in os.walk(root_directory):
    for file in files:
        # Update the video file's length in postgres if a video file was found
        if is_video_file(file):
            # windows path to file
            pathtofile = os.path.join(root, file)
            # search for the record in postgres
            searchitem = get_last_directory(root) + '/' + file
            try:
                cursor.execute("SELECT * FROM \"assets\" WHERE \"originalPath\" LIKE %s", ("%" + searchitem,))
                results = cursor.fetchall()

                if len(results) > 1:
                    raise Exception(f"Found more than one {searchitem}")
                
                # update the video's duration recorded in postgres
                for row in results:
                    cursor.execute("UPDATE \"assets\" SET \"duration\" = %s WHERE id = %s", (get_video_duration(pathtofile), results[0][0],))
                    conn.commit()
                    i += 1
                    print(f"Updated {searchitem}")

            except Exception as e:
                print("Error: ", e)

print(f"Updated {i} records")