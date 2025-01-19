#import docker
import os
import shutil
import time
import datetime
import threading
import boto3
from botocore.exceptions import NoCredentialsError

# Initialize an S3 client
s3_client = boto3.client('s3')
local_last_updated = 0

'''
DOCKER_CONTAINER_ID = "affectionate_ride"
client = docker.from_env()
container = client.containers.get(DOCKER_CONTAINER_ID)
'''

UPLOAD_FOLDER = 'uploads'
ASSET_FOLDER = 'assets'
DOWNLOAD_FOLDER = 'downloads'

file_name = DOWNLOAD_FOLDER + '/images.jarvis'  # Local file path for the download
bucket_name = 'jarvis-zipped-images'
object_name = 'jarviszips'  # The object name in S3

# Set the allowed file extensions (you can add more if needed)
ALLOWED_EXTENSIONS = {'jarvis'}

# Function to check if the file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def download_file_from_s3(bucket_name, object_name, file_name=None):
    # If the file name is not specified, use the object name as the file name
    if file_name is None:
        file_name = object_name

    try:
        # Download the file from S3
        s3_client.download_file(bucket_name, object_name, file_name)
        print(f"File {object_name} downloaded successfully to {file_name}")
    except FileNotFoundError:
        print(f"The local file path {file_name} was not found.")
    except NoCredentialsError:
        print("Credentials not available.")
    except Exception as e:
        print(f"An error occurred: {e}")

def download_file():
    # Clear the download folder
    if os.path.exists(DOWNLOAD_FOLDER):
        shutil.rmtree(DOWNLOAD_FOLDER)
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

    try:
        download_file_from_s3(bucket_name, object_name, file_name)
        print("Download success")
    except:
        print("Download failed :(")

def check_metadata():
    global local_last_updated
    try:
        # Fetch the file metadata from S3
        response = s3_client.head_object(Bucket=bucket_name, Key=object_name)
        last_modified = response['LastModified']
        print(last_modified)

        # Compare the last modified time with the local timestamp
        if local_last_updated != last_modified:
            local_last_updated = last_modified
            # Trigger download if metadata has changed
            download_file()
            print(f"File updated. Last updated: {last_modified}. Download initiated.")
        else:
            print(f"File not updated. Last checked at: {datetime.datetime.now()}")

    except Exception as e:
        print(f"Error: {e}")

# Background thread to periodically check for file metadata
def metadata_check_thread():
    while True:
        check_metadata()
        time.sleep(1)  # Wait for 1 second before checking again

# Start the metadata check in the background
thread = threading.Thread(target=metadata_check_thread, daemon=True)
thread.start()

def process_upload(filepath):
    if os.path.exists(ASSET_FOLDER):
        shutil.rmtree(ASSET_FOLDER)
    os.makedirs(ASSET_FOLDER, exist_ok=True)

    try:
        shutil.unpack_archive(filepath, ASSET_FOLDER, "zip")
        print(f"Successfully unzipped {filepath} to {ASSET_FOLDER}")
    except shutil.ReadError:
        print(f"Failed to unzip {filepath}. The file is not a valid ZIP archive.")

'''def stream_docker_exec(container, command):
    # Create an exec instance
    exec_instance = container.exec_run(command, stream=True)
    
    # Iterate through the output stream
    for line in exec_instance.output:
        yield line.decode().strip()

def stream():
    # Command to run in the Docker container
    command = "stdbuf -oL ns-process-data video --data /workspace/assets/sign.mov --output-dir /workspace/processed"
    
    # Start timer
    start_time = time.time()
    
    # Stream output and monitor for stream completion
    for line in stream_docker_exec(container, command):
        # Send elapsed time update
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        elapsed_str = f"{minutes}:{seconds:02}"
        print(f"TIMER: {elapsed_str}")
        
        # Send the output line
        print(line)

    # After the stream completes, redirect to /stream2
    print("data: STREAM_COMPLETE")
    print("data: Redirecting to the next stage...")
    stream2()

def stream2():
    # Command to run in the Docker container
    command = "stdbuf -oL ns-train splatfacto --data /workspace/processed"
    
    # Start timer for the second process
    start_time = time.time()
    
    # Stream output for the second command
    for line in stream_docker_exec(container, command):
        # Send elapsed time update
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(int(elapsed_time), 60)
        elapsed_str = f"{minutes}:{seconds:02}"
        print(f"TIMER: {elapsed_str}")
        
        # Send the output line
        print(line)
'''

# Keep the script running
while True:
    time.sleep(1)
