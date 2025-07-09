from flask import Flask, render_template, request, jsonify, send_file
import os
import uuid
import time
import threading

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = os.path.join("data", "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Clean files older than N hours
def cleanup_old_files(folder_path, hours=1):
    now = time.time()
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        if os.path.isfile(filepath):
            file_age = now - os.path.getmtime(filepath)
            if file_age > hours * 3600:
                try:
                    os.remove(filepath)
                    print(f"🧹 Deleted: {filepath}")
                except Exception as e:
                    print(f"⚠️ Failed to delete {filepath}: {e}")

# Periodic cleaner thread
def run_cleanup_periodically(folder_path, hours=1, interval_minutes=30):
    def cleanup_loop():
        while True:
            cleanup_old_files(folder_path, hours)
            time.sleep(interval_minutes * 60)
    t = threading.Thread(target=cleanup_loop, daemon=True)
    t.start()

@app.route('/')
def home():
    return render_template('index.html', error=None, download_links=[])

@app.route('/run_shapefile', methods=['POST'])
def run_shapefile():
    try:
        data = request.get_json()
        region_type = data.get("region_type", "").strip()
        region_names = data.get("region_names", "").strip()
        years = data.get("years", "").strip()

        from clime_easy_updated_fixed import use_shapefile_workflow
        use_shapefile_workflow(region_type, region_names, years)

        from data.rainfall_input_from_shapefile_updated import analyze_excel_report
        excel_path = max(
            [os.path.join(OUTPUT_FOLDER, f) for f in os.listdir(OUTPUT_FOLDER) if f.endswith(".xlsx")],
            key=os.path.getmtime
        )
        analyze_excel_report(excel_path)

        return jsonify(success=True, message="Shapefile analysis completed",
                       download_links=get_latest_outputs(OUTPUT_FOLDER))
    except Exception as e:
        return jsonify(success=False, message=f"❌ Shapefile error: {str(e)}")

@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify(success=False, message="No file uploaded.")
    
    file = request.files['file']
    if file.filename == '':
        return jsonify(success=False, message="File name is empty.")

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        os.environ["UPLOADED_EXCEL_PATH"] = filepath
        from clime_easy_updated_fixed import use_file_upload_workflow
        use_file_upload_workflow()

        from data.rainfall_input_from_shapefile_updated import analyze_excel_report
        analyze_excel_report(filepath)

        return jsonify(success=True, message="Upload & analysis complete",
                       download_links=get_latest_outputs(OUTPUT_FOLDER))
    except Exception as e:
        return jsonify(success=False, message=f"❌ Upload analysis error: {str(e)}")

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

def get_latest_outputs(folder):
    pdfs = [f for f in os.listdir(folder) if f.endswith('.pdf')]
    excels = [f for f in os.listdir(folder) if f.endswith('.xlsx')]
    files = []

    if excels:
        latest_excel = max(excels, key=lambda x: os.path.getmtime(os.path.join(folder, x)))
        files.append(f"/download/{latest_excel}")
    if pdfs:
        latest_pdf = max(pdfs, key=lambda x: os.path.getmtime(os.path.join(folder, x)))
        files.append(f"/download/{latest_pdf}")

    return files

# 👇 This part runs only when app is started (not imported)
if __name__ == '__main__':
    cleanup_old_files(OUTPUT_FOLDER, hours=1)
    cleanup_old_files(UPLOAD_FOLDER, hours=1)
    run_cleanup_periodically(OUTPUT_FOLDER, hours=1)
    run_cleanup_periodically(UPLOAD_FOLDER, hours=1)

    # 🌐 Get port from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)



