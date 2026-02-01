import cv2
import numpy as np
import pickle
import os
from datetime import datetime

class FaceSystem:
    """Simple face recognition system"""
    
    def __init__(self):
        # face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # face recognition
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        # data
        self.users = {}
        self.trained = False
        
        # paths
        self.data_dir = 'data/faces'
        self.model_path = 'models/face_model.yml'
        
        # load existing model if available
        self.load_model()
    
    def preprocess(self, img):
        """improve image quality"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # improve contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        return enhanced
    
    def detect_face(self, frame):
        """detect face in frame"""
        gray = self.preprocess(frame)
        
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.3, 
            minNeighbors=5,
            minSize=(50, 50)
        )
        
        if len(faces) == 0:
            return None, None
        
        # get largest face
        (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
        face_region = gray[y:y+h, x:x+w]
        
        return face_region, (x, y, w, h)
    
    def register_user(self, name, frames):
        """register a new user with their face samples"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        samples = []
        for frame in frames:
            face, _ = self.detect_face(frame)
            if face is not None:
                samples.append(face)
        
        if len(samples) < 10:
            return False, f"Only captured {len(samples)} samples. Need at least 10."
        
        # save user data
        user_data = {
            'name': name,
            'samples': samples,
            'registered_at': datetime.now().isoformat()
        }
        
        filepath = os.path.join(self.data_dir, f'{name}.pkl')
        with open(filepath, 'wb') as f:
            pickle.dump(user_data, f)
        
        # retrain
        success = self.train()
        
        if success:
            return True, f"Registered {name} with {len(samples)} samples"
        else:
            return False, "Training failed"
    
    def train(self):
        """train the recognizer on all registered users"""
        faces = []
        labels = []
        self.users = {}
        
        if not os.path.exists(self.data_dir):
            return False
        
        user_files = [f for f in os.listdir(self.data_dir) if f.endswith('.pkl')]
        
        if len(user_files) == 0:
            return False
        
        for idx, user_file in enumerate(user_files):
            filepath = os.path.join(self.data_dir, user_file)
            with open(filepath, 'rb') as f:
                user_data = pickle.load(f)
            
            name = user_data['name']
            self.users[idx] = name
            
            for sample in user_data['samples']:
                faces.append(sample)
                labels.append(idx)
        
        if len(faces) == 0:
            return False
        
        self.recognizer.train(faces, np.array(labels))
        
        # save model
        os.makedirs('models', exist_ok=True)
        self.recognizer.save(self.model_path)
        
        with open('models/users.pkl', 'wb') as f:
            pickle.dump(self.users, f)
        
        self.trained = True
        return True
    
    def load_model(self):
        """load trained model"""
        if os.path.exists(self.model_path):
            self.recognizer.read(self.model_path)
            
            with open('models/users.pkl', 'rb') as f:
                self.users = pickle.load(f)
            
            self.trained = True
            return True
        return False
    
    def recognize(self, frame):
        """recognize face in frame"""
        if not self.trained:
            return None, 0
        
        face, rect = self.detect_face(frame)
        
        if face is None:
            return None, 0
        
        label, confidence = self.recognizer.predict(face)
        
        # lower confidence = better match
        if confidence < 70:
            name = self.users.get(label, "Unknown")
            return name, confidence
        
        return "Unknown", confidence
    
    def get_all_users(self):
        """get list of registered users"""
        if not os.path.exists(self.data_dir):
            return []
        
        users = []
        for f in os.listdir(self.data_dir):
            if f.endswith('.pkl'):
                users.append(f.replace('.pkl', ''))
        
        return users
    
    def anti_spoof_check(self, frame):
        """basic anti-spoofing using texture analysis"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # calculate laplacian variance
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        # real faces usually have variance > 100
        # photos are blurrier
        return variance > 100, variance