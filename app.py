from flask import Flask, render_template, request, jsonify
import re
import os

app = Flask(__name__)

# --- Symbol Table ---
def load_dictionary():
    words = set()
    if os.path.exists("dictionary.txt"):
        with open("dictionary.txt", "r") as f:
            for line in f:
                words.add(line.strip().lower())
    else:
        words = {"she", "said", "this", "is", "a", "test", "system", "grammar"}
    return words

word_db = load_dictionary()

def get_best_match(word):
    word = word.lower()
    best_word = "???"
    min_distance = 99
    for dict_word in word_db:
        if abs(len(dict_word) - len(word)) > 2: continue
        diff = max(len(word), len(dict_word)) - sum(1 for a, b in zip(word, dict_word) if a == b)
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
    
    # Priority logic for Input Stream
    if 'file' in request.files and request.files['file'].filename != '':
        text = request.files['file'].read().decode('utf-8')
    elif request.is_json:
        text = request.get_json().get('text', '')
    else:
        # Fallback for form data
        text = request.form.get('text', '')

    # --- Phase 1: Syntax Analysis (Capitalization) ---
    grammar_warning = None
    first_letter_search = re.search(r'[a-zA-Z]', text)
    
    has_grammar_error = False
    if first_letter_search:
        if not first_letter_search.group().isupper():
            grammar_warning = "Syntax Violation: Sentence must start with an Uppercase letter."
            has_grammar_error = True

    # --- Phase 2: Lexical Analysis ---
    raw_tokens = re.findall(r"\b[a-zA-Z']+\b|[^\w\s]|\s+", text)
    
    errors = []
    corrected_html = []
    total_words = 0

    for token in raw_tokens:
        if re.match(r"[a-zA-Z']+", token):
            total_words += 1
            if token.lower() not in word_db:
                suggestion = get_best_match(token)
                errors.append(token)
                corrected_html.append(f'<span class="err-strike">{token}</span><span class="fix-green">{suggestion}</span>')
            else:
                corrected_html.append(token)
        else:
            corrected_html.append(token)

    # --- Phase 4: Scoring (Accuracy) ---
    # Accuracy is reduced if there are spelling OR grammar errors
    error_count = len(errors)
    penalty = 1 if has_grammar_error else 0
    
    if total_words > 0:
        accuracy = round(((total_words - (error_count + penalty)) / total_words) * 100, 1)
    else:
        accuracy = 100
        
    if accuracy < 0: accuracy = 0

    return jsonify({
        "total_errors": error_count + penalty,
        "accuracy": accuracy,
        "corrected_text": "".join(corrected_html),
        "grammar_issue": grammar_warning
    })

if __name__ == '__main__':
    app.run(debug=True)
