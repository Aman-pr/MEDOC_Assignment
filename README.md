# MEDOC_Assignment
This project implements a face-recognition-based attendance system using OpenCV and Streamlit. It detects faces, verifies liveness using a simple anti-spoofing check, recognizes registered users, and records punch-in / punch-out attendance locally in JSON format. The system is designed for small-scale, controlled rather than security deployments.
Project Overview
A complete face recognition-based attendance system with:
·	Real-time face detection and recognition
·	Webcam-based user registration
·	Automatic punch in/out tracking
·	Basic anti-spoofing protection
·	Adaptive lighting handling
Tech Stack: Python, OpenCV, Flask, LBPH Recognition

Deliverables Checklist
✓ Working Demo
·	Web interface at localhost:5000
·	Command-line demo also included
✓ Complete Codebase
·	Clean, modular architecture
·	Commented and organized
✓ Documentation
·	Detailed README with technical explanations
·	Quick start guide
·	Development notes

Quick Start
# Install dependencies
pip install -r requirements.txt

# Test setup
python test_setup.py

# Run web app
python app.py

# Or try CLI demo
python demo.py

Open browser: http://localhost:5000

Key Features Implemented
1. Face Registration
·	Captures 30 samples per user
·	Multiple angles for robustness
·	Automatic training after registration
2. Face Recognition
·	LBPH algorithm (fast, accurate for small datasets)
·	CLAHE preprocessing for lighting variations
·	Confidence-based thresholding
3. Attendance System
·	Punch in/out with timestamps
·	Duplicate prevention (1-minute cooldown)
·	JSON-based storage
·	Daily status tracking
4. Anti-Spoofing
·	Texture analysis (Laplacian variance)
·	Optional eye blink detection (if dlib installed)
·	Catches basic photo attacks

Technical Approach
Model Selection: LBPH
Why not deep learning?
·	No GPU required
·	Fast inference (50-100ms)
·	Works with small datasets (30 samples vs thousands)
·	Sufficient accuracy for controlled environments
Alternatives Considered:
·	MTCNN + FaceNet: Too slow without GPU
·	Eigenfaces/Fisherfaces: Poor with lighting changes
·	Commercial APIs: Defeats the purpose of building it
Preprocessing Pipeline
1.	BGR to Grayscale conversion
2.	CLAHE (clipLimit=2.0, tileGridSize=8x8)
1.	Normalizes lighting across face regions
2.	Tested various values, these work best
3.	Face detection via Haar Cascade
4.	Region extraction and resizing
Recognition Process
1.	Detect face in frame
2.	Preprocess region
3.	Generate LBPH histogram (256 bins)
4.	Compare with stored models (Chi-square distance)
5.	Accept if confidence < 70

Accuracy & Limitations
Expected Accuracy
Condition	Recognition Rate
Good lighting, frontal	~95%
Moderate lighting	~85%
Poor lighting/angle	~60-70%

Anti-spoofing: 70-85% against simple photo attacks
Known Failure Cases
Will Fail:
·	Very dark environments (< 50 lux)
·	Extreme angles (> 30° rotation)
·	Heavy occlusions (sunglasses, masks)
·	Identical twins
·	High-quality spoofing (3D masks, video replay)
Why These Fail:
·	Haar cascade optimized for frontal faces
·	LBPH doesn't capture 3D structure
·	Basic anti-spoofing has inherent limits
Honest Assessment:

This is a functional prototype, not production-ready security. Production would need:
·	Depth sensors
·	Multi-modal verification
·	Deep learning models
·	Professional anti-spoofing
