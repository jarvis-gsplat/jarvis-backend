from flask import Flask, jsonify, request, Response, url_for, send_from_directory
import os, shutil


UPLOAD_FOLDER = 'uploads'
ASSET_FOLDER = 'assets'
DOWNLOAD_FOLDER = 'downloads'
# Clear the uploads folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
# Set the allowed file extensions (you can add more if needed)
ALLOWED_EXTENSIONS = {'jarvis', 'jpg', "jpeg", "png"}

# Function to check if the file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for the homepage
@app.route('/')
def home():
    return send_from_directory('static', 'jarvis.png')

@app.route('/upload', methods=['POST'])
def upload_file():  
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

if __name__ == "__main__":
    app.run(debug=True)