import os
import sys
import pickle
import numpy as np

# 1. FIX: Suppress TensorFlow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

import tensorflow as tf
from flask import Flask, request, jsonify
from flask_cors import CORS

# 2. FIX: Add parent directory to path so 'scripts' can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now this import will work!
try:
    from scripts.preprocess_utils import clean_tigrigna_text
except ModuleNotFoundError:
    # Fallback for different execution environments
    from scripts.preprocess_utils import clean_tigrigna_text

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})



# Use BASE_DIR to find the absolute path of the web_service folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Corrected paths based on your VS Code file explorer
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'Tigrigna_Sentiment_Final_Model.h5')
TOKENIZER_PATH = os.path.join(BASE_DIR, 'model', 'tigrigna_tokenizer.pkl')

print(f"--- SERVER STARTING ---")
print(f"Loading Model from: {MODEL_PATH}")
print(f"Loading Tokenizer from: {TOKENIZER_PATH}")

MAX_SEQUENCE_LENGTH = 32  
CLASS_LABELS = {0: "negative", 1: "neutral", 2: "positive"}

model = None
tokenizer = None

def load_assets():
    global model, tokenizer
    if model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
        model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    if tokenizer is None:
        if not os.path.exists(TOKENIZER_PATH):
            raise FileNotFoundError(f"Tokenizer not found at {TOKENIZER_PATH}")
        with open(TOKENIZER_PATH, 'rb') as f:
            tokenizer = pickle.load(f)

# -------------------------------
# 2. Endpoints
# -------------------------------

@app.route('/')
def health():
    return jsonify({
        "status": "online", 
        "accuracy": "82%", 
        "macro_f1": "78%",
        "vocab_size": 44000
    })

@app.route('/analyze-sentiment', methods=['POST', 'OPTIONS'])
def analyze():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        load_assets()
        data = request.get_json()
        raw_comments = data.get('comments', [])
        
        valid_originals = []
        cleaned_list = []
        
        for raw in raw_comments:
            c = clean_tigrigna_text(raw)
            if c:
                valid_originals.append(raw)
                cleaned_list.append(c)

        if not cleaned_list:
            return jsonify({"error": "No Tigrigna text detected"}), 400

        # Tokenize & Pad
        seqs = tokenizer.texts_to_sequences(cleaned_list)
        padded = tf.keras.preprocessing.sequence.pad_sequences(
            seqs, maxlen=MAX_SEQUENCE_LENGTH, padding='pre', truncating='post'
        )

        # Predict using Bi-LSTM
        probs = model.predict(padded)
        indices = np.argmax(probs, axis=1)

        results = {"positive": [], "neutral": [], "negative": []}
        for i, idx in enumerate(indices):
            label = CLASS_LABELS[int(idx)]
            results[label].append({
                "text": valid_originals[i],
                "confidence": f"{float(np.max(probs[i])) * 100:.2f}%"
            })

        return jsonify({
            "status": "success",
            "total_analyzed": len(valid_originals),
            "counts": {
                "positive": len(results["positive"]),
                "neutral": len(results["neutral"]),
                "negative": len(results["negative"])
            },
            "results": results
        })

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Force the port to 5000 for the browser extension
    app.run(host='0.0.0.0', port=5000, debug=True)