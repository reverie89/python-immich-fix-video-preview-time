import os, sys, subprocess
from datetime import timedelta

ffprobe_path = "D:\\ffmpeg-6.1.1-essentials_build\\bin\\ffprobe.exe"

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

print(f"Searching recursively from: {root_directory}")

def is_video_file(filename):
    video_extensions = ['mp4', 'mkv', 'avi', 'wmv', 'flv', 'mov']  # Add more video extensions if needed
    file_extension = filename.split('.')[-1].lower()
    return file_extension in video_extensions

def get_video_duration(file_path):
    duration_result = subprocess.run(
        [ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
         file_path],
        capture_output=True, text=True, shell=True)
    if duration_result.returncode == 0:
        try:
            return int(float(duration_result.stdout))

        except ValueError:
            print(f"Error: Unable to parse video duration for: {file_path}")
            return None

    else:
        print("Error: ", duration_result.stderr)
        return None

def edit_xmp_file(file_path, duration_seconds):
    replacements = {"   video:duration=" : f"   video:duration=\"{duration_seconds}\"",
                    "  <video:duration>" : f"  <video:duration>{duration_seconds}</video:duration>",
                    "   xmpDM:duration=" : f"   xmpDM:duration=\"{duration_seconds}\"",
                    "  <xmpDM:duration>" : f"  <xmpDM:duration>{duration_seconds}</xmpDM:duration>",
                    }
    with open(file_path, "r+") as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            for search_string, new_content in replacements.items():
                if search_string in line:
                    lines[i] = new_content + "\n"
                    break
        file.seek(0)
        file.writelines(lines)

i = 0
# Find all video files from the root directory
for root, dirs, files in os.walk(root_directory):
    for file in files:
        # Update the video file's length in postgres if a video file was found
        if is_video_file(file):
            # windows path to file
            pathtofile = os.path.join(root, file)
            if os.path.isfile(pathtofile + ".xmp"):
                edit_xmp_file(file_path=pathtofile + ".xmp",
                            duration_seconds=get_video_duration(pathtofile)
                            )
                print(f"Updated: {pathtofile}.xmp")
                i += 1

print(f"Updated {i} records")