from flask import Flask, jsonify, render_template, request
import docker, os, shutil
DOCKER_CONTAINER_ID = "busy_matsumoto"
# Define the folder to store uploaded images
UPLOAD_FOLDER = 'uploads'
ASSET_FOLDER = 'assets'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)

# Route for the homepage
@app.route('/')
def home():
    # Connect to Docker
    client = docker.from_env()

    # Get a container by its name or ID
    container = client.containers.get(DOCKER_CONTAINER_ID)

    # Create an exec instance with the command you want to run
    output = container.exec_run('pwd')

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
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)  # Delete the file
            else:
                shutil.rmtree(file_path)  # Delete the directory (if any)
        except Exception as e:
            print(f"Error clearing file {file_path}: {e}")
    
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
        return jsonify({"message": f"File uploaded successfully to {filepath}"}), 200

    return jsonify({"error": "Invalid file type"}), 400

def process_upload(filename):
    inputfilepath = os.path.join(UPLOAD_FOLDER, filename)
    outputfilepath = os.path.join(ASSET_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)