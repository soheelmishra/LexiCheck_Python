from flask import Flask, render_template, request, jsonify
import re
import os

app = Flask(__name__)

# --- Phase 0: Load Dictionary (The Language Definition) ---
def load_dictionary():
    words = set()
    if os.path.exists("dictionary.txt"):
        with open("dictionary.txt", "r") as f:
            for line in f:
                words.add(line.strip().lower())
    else:
        # Emergency defaults if dictionary.txt is missing
        words = {"this", "is", "a", "test", "of", "the", "system", "and", "it", "has", "grammar", "errors", "with", "python"}
    return words

word_db = load_dictionary()

# --- Phase 3: Semantic Repair (The Suggestion Engine) ---
def get_best_match(word):
    """Simple Similarity Algorithm: Finds the word with the most matching characters"""
    word = word.lower()
    best_word = "???"
    min_distance = 99
    
    for dict_word in word_db:
        # Length filter for performance
        if abs(len(dict_word) - len(word)) > 2: continue
        
        # Calculate 'Distance' (lower is better)
        # We check how many characters are different
        diff = 0
        max_len = max(len(word), len(dict_word))
        for i in range(max_len):
            if i >= len(word) or i >= len(dict_word) or word[i] != dict_word[i]:
                diff += 1
        
        if diff < min_distance:
            min_distance = diff
            best_word = dict_word
            
    return best_word

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check_text():
    text = ""
    if 'file' in request.files:
        file = request.files['file']
        text = file.read().decode('utf-8')
    elif request.is_json:
        text = request.get_json().get('text', '')

    # --- Phase 1: Lexical Analysis (Tokenization) ---
    # Keeps words, punctuation, and spaces separate
    raw_tokens = re.findall(r"\b[a-zA-Z']+\b|[^\w\s]|\s+", text)
    
    errors = []
    corrected_html = []
    total_words = 0

    for token in raw_tokens:
        if re.match(r"[a-zA-Z']+", token): # If it's a word
            total_words += 1
            low_word = token.lower()
            if low_word not in word_db:
                suggestion = get_best_match(low_word)
                errors.append({"original": token, "corrected": suggestion})
                # Wrap the correction in HTML tags for the UI
                corrected_html.append(f'<span class="err-strike">{token}</span><span class="fix-green">{suggestion}</span>')
            else:
                corrected_html.append(token)
        else:
            # Punctuation/Spaces are passed through untouched
            corrected_html.append(token)

    # Accuracy Calculation
    accuracy = 100
    if total_words > 0:
        accuracy = round(((total_words - len(errors)) / total_words) * 100, 1)

    return jsonify({
        "total_errors": len(errors),
        "accuracy": accuracy,
        "corrected_text": "".join(corrected_html)
    })

if __name__ == '__main__':
    app.run(debug=True)