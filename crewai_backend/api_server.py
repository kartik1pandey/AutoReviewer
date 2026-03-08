"""
Flask API Server for CrewAI AutoReviewer
Provides REST endpoints for paper review
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
from datetime import datetime
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crew_system import CrewAIReviewerSystem

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
CORS(app)  # Enable CORS for frontend

# Configuration
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Initialize reviewer system (lazy loading)
reviewer_system = None

def get_reviewer_system():
    """Get or initialize reviewer system"""
    global reviewer_system
    if reviewer_system is None:
        print("🤖 Initializing CrewAI AutoReviewer System...")
        reviewer_system = CrewAIReviewerSystem()
    return reviewer_system

@app.route('/')
def index():
    """Serve frontend"""
    from flask import send_from_directory
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/app.js')
def serve_js():
    """Serve JavaScript"""
    from flask import send_from_directory
    return send_from_directory(app.static_folder, 'app.js')

@app.route('/api/info')
def api_info():
    """API info"""
    return jsonify({
        "name": "CrewAI AutoReviewer API",
        "version": "2.0",
        "status": "running",
        "endpoints": {
            "/api/review": "POST - Upload and review a paper",
            "/api/status": "GET - Check API status",
            "/api/results/<filename>": "GET - Download review result"
        }
    })

@app.route('/api/status')
def status():
    """Check API status"""
    return jsonify({
        "status": "ok",
        "backend": "CrewAI + Groq",
        "model": "llama-3.1-8b-instant",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/review', methods=['POST'])
def review_paper():
    """
    Review a research paper
    
    Request:
        - file: PDF file (multipart/form-data)
        
    Response:
        - review: Complete review report
        - filename: Result filename
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400
        
        if not file.filename.endswith('.pdf'):
            return jsonify({"error": "Only PDF files are supported"}), 400
        
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        print(f"\n📄 Received file: {filename}")
        print("="*70)
        
        # Get reviewer system
        system = get_reviewer_system()
        
        # Review paper
        print(f"🔍 Starting review...")
        report = system.review_paper(filepath)
        
        # Save report
        result_filename = f"review_{timestamp}.json"
        result_path = os.path.join(RESULTS_FOLDER, result_filename)
        system.save_report(report, result_path)
        
        print(f"✅ Review complete!")
        print("="*70)
        
        # Return report
        return jsonify({
            "success": True,
            "report": report,
            "result_file": result_filename,
            "timestamp": timestamp
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error during review: {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "error": error_msg,
            "traceback": traceback.format_exc()
        }), 500

@app.route('/api/results/<filename>')
def get_result(filename):
    """Download a review result file"""
    try:
        return send_from_directory(RESULTS_FOLDER, filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/health')
def health():
    """Health check endpoint"""
    try:
        # Check if Groq API key is set
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            return jsonify({
                "status": "error",
                "message": "GROQ_API_KEY not set"
            }), 500
        
        return jsonify({
            "status": "healthy",
            "backend": "CrewAI + Groq",
            "api_key_set": True
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 CrewAI AutoReviewer API Server")
    print("="*70)
    print("\nEndpoints:")
    print("  • http://localhost:5001/")
    print("  • http://localhost:5001/api/status")
    print("  • http://localhost:5001/api/review (POST)")
    print("  • http://localhost:5001/api/health")
    print("\n" + "="*70)
    
    # Run server
    app.run(host='0.0.0.0', port=5001, debug=False)
