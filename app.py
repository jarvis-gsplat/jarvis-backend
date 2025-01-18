from flask import Flask, jsonify, request, Response, url_for
import docker, os, shutil, time

DOCKER_CONTAINER_ID = "serene_shaw"
client = docker.from_env()
container = client.containers.get(DOCKER_CONTAINER_ID)

UPLOAD_FOLDER = 'uploads'
ASSET_FOLDER = 'assets'

app = Flask(__name__)

# Route for the homepage
@app.route('/')
def home():
    # Create an exec instance with the command you want to run
    output = container.exec_run('echo "HELLO VRO"')

    # Start the exec instance and capture the output
    return output.output.decode()

# Set the allowed file extensions (you can add more if needed)
ALLOWED_EXTENSIONS = {'jarvis'}

# Function to check if the file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    # Clear the uploads folder
    if os.path.exists(UPLOAD_FOLDER):
        shutil.rmtree(UPLOAD_FOLDER)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Check if the request contains the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    
    # If no file is selected
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # If the file is allowed, save it
    if file and allowed_file(file.filename):
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        process_upload(filepath)
        return jsonify({"message": f"File uploaded successfully to {filepath}"}), 200

    return jsonify({"error": "Invalid file type"}), 400

def process_upload(filepath):
    if os.path.exists(ASSET_FOLDER):
        shutil.rmtree(ASSET_FOLDER)
    os.makedirs(ASSET_FOLDER, exist_ok=True)

    try:
        shutil.unpack_archive(filepath, ASSET_FOLDER, "zip")
        print(f"Successfully unzipped {filepath} to {ASSET_FOLDER}")
    except shutil.ReadError:
        print(f"Failed to unzip {filepath}. The file is not a valid ZIP archive.")

import subprocess

def stream_docker_exec(container, command):
    # Create an exec instance
    exec_instance = container.exec_run(command, stream=True)
    
    # Iterate through the output stream
    for line in exec_instance.output:
        yield line.decode().strip()

@app.route("/stream")
def stream():
    def generate():
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
            yield f"TIMER:{elapsed_str}\n\n"
            
            # Send the output line
            yield f"{line}\n\n"
        
        # After the stream completes, redirect to /stream2
        yield "data: STREAM_COMPLETE\n\n"
        yield "data: Redirecting to the next stage...\n\n"
        yield f"data: {url_for('stream2')}\n\n"  # Send redirect URL

    return Response(generate(), mimetype="text/event-stream")

@app.route("/stream2")
def stream2():
    def generate():
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
            yield f"TIMER:{elapsed_str}\n\n"
            
            # Send the output line
            yield f"{line}\n\n"

    return Response(generate(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(debug=True, threaded=True)