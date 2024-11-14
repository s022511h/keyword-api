from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import openai
from pymongo import MongoClient
import config
import re
from datetime import datetime

app = Flask(__name__, static_folder='build', static_url_path='')
CORS(app)

openai.api_key = config.OPENAI_API_KEY
openai.temperature = 0.4

mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['KeywordDB']
primary_keywords_collection = db['Primary']
secondary_keywords_collection = db['Secondary']
long_tail_keywords_collection = db['Long-Tail']
optimization_log_collection = db['OptimizationLogs']

def fetch_keywords_from_db():
    try:
        primary_keywords = list(primary_keywords_collection.find({'keyword': {'$regex': '.*apprenticeships.*'}}).sort([('searchVolume', -1), ('seoDifficulty', 1)]).limit(5))
        secondary_keywords = list(secondary_keywords_collection.find({'$nor': [{'keyword': {'$regex': '.*apprenticeships.*'}}]}).sort([('searchVolume', -1), ('seoDifficulty', 1)]).limit(5))
        long_tail_keywords = list(long_tail_keywords_collection.find().sort([('searchVolume', -1), ('seoDifficulty', 1)]).limit(3))
        
        for keyword_list in [primary_keywords, secondary_keywords, long_tail_keywords]:
            for keyword in keyword_list:
                split_keywords = re.split(r'\bin\b', keyword['keyword'], flags=re.IGNORECASE)
                if len(split_keywords) > 1:
                    for kw in split_keywords:
                        keyword['keyword'] = kw.strip()

        keywords = primary_keywords + secondary_keywords + long_tail_keywords
        print(f"Fetched keywords from DB: {keywords}")
        return [kw['keyword'] for kw in keywords]
    except Exception as e:
        print(f"Error fetching keywords from MongoDB: {e}")
        return []

def insert_keywords_with_gpt(text, keywords):
    try:
        cleaned_keywords = [keyword.replace("**", "").strip() for keyword in keywords]
        prompt = (
            f"Revise the following text by subtly and naturally integrating these keywords. "
            f"Maintain readability, avoid keyword stuffing, and ensure each keyword fits logically within sentences.\n\n"
            f"Original Text:\n{text}\n\n"
            f"Keywords to Integrate: {', '.join(cleaned_keywords)}\n\n"
            f"Guidelines:\n"
            f"- Use keywords only where they fit naturally within the text.\n"
            f"- Ensure each keyword is contextually relevant to its sentence.\n"
            f"- Do not add symbols around keywords; keep them simple.\n"
            f"- Maintain a professional tone.\n"
        )

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an SEO expert optimizing text by integrating keywords naturally and contextually."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )

        response_text = response['choices'][0]['message']['content']
        cleaned_response_text = response_text.replace("**", "")
        return cleaned_response_text

    except Exception as e:
        print(f"Error during keyword insertion with GPT: {e}")
        return text 

def highlight_keywords(optimized_text, keywords):
    for kw in sorted(keywords, key=len, reverse=True):
        kw_regex = re.escape(kw)
        optimized_text = re.sub(rf"(?<!>)\b{kw_regex}\b(?!<)", f"<span class='highlighted-keyword'>{kw}</span>", optimized_text)
    return optimized_text

def log_keyword_usage(keywords, text, success=True, feedback=False):
    try:
        log_entry = {
            'keywords': keywords,
            'text': text,
            'success': success,
            'feedback': feedback,
            'timestamp': datetime.now()
        }
        optimization_log_collection.insert_one(log_entry)
        print(f"Logged keyword usage: {log_entry}")
    except Exception as e:
        print(f"Error logging keyword usage: {e}")

def has_previous_optimization(text):
    try:
        previous_log = optimization_log_collection.find_one({'text': text, 'feedback': True})
        return previous_log is not None
    except Exception as e:
        print(f"Error checking for previous optimizations: {e}")
        return False

# Updated SEO scoring functions
def calculate_target_seo_score(text, keywords):
    word_count = len(text.split())
    avg_target_density = 3.5
    max_target_density = 5.0
    target_keyword_density = min(avg_target_density, max_target_density)
    target_score = min((word_count * target_keyword_density) / 100, 100)
    print("Target SEO Score Calculation:")
    print(f"Word Count: {word_count}")
    print(f"Target Keyword Density: {target_keyword_density}%")
    print(f"Final Target SEO Score: {round(target_score)}")
    return round(target_score)

def calculate_current_seo_score(original_text, optimized_text, keywords):
    original_word_count = len(original_text.split())
    keyword_count = sum(optimized_text.lower().count(keyword.lower()) for keyword in keywords)
    keyword_density = (keyword_count / original_word_count) * 100 if original_word_count > 0 else 0
    current_score = min(keyword_density, 100)
    print("Current SEO Score Calculation:")
    print(f"Original Word Count: {original_word_count}")
    print(f"Keyword Count in Optimized Text: {keyword_count}")
    print(f"Keyword Density Based on Original Length: {keyword_density}%")
    print(f"Final Current SEO Score: {round(current_score)}")
    return round(current_score)

@app.route('/optimize', methods=['POST'])
def optimize_content():
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({"error": "No content provided"}), 400

        if has_previous_optimization(text):
            return jsonify({"error": "This content was previously marked as undesired by the user."}), 400

        db_keywords = fetch_keywords_from_db()

        if not db_keywords:
            return jsonify({"error": "No keywords found"}), 500

        optimized_text = insert_keywords_with_gpt(text, db_keywords)
        optimized_text = highlight_keywords(optimized_text, db_keywords)
        
        target_seo_score = calculate_target_seo_score(text, db_keywords)
        current_seo_score = calculate_current_seo_score(text, optimized_text if optimized_text else text, db_keywords)

        return jsonify({
            'optimizedText': optimized_text,
            'highlightedKeywords': db_keywords,
            'targetSeoScore': target_seo_score,
            'currentSeoScore': current_seo_score
        })

    except Exception as e:
        print(f"Error in /optimize route: {e}")
        log_keyword_usage([], text, success=False, feedback=False)
        return jsonify({"error": str(e)}), 500

@app.route('/feedback', methods=['POST'])
def user_feedback():
    try:
        data = request.json
        text = data.get('text', '')

        if not text:
            return jsonify({"error": "No content provided"}), 400

        log_keyword_usage([], text, success=False, feedback=True)

        return jsonify({"message": "Feedback received. We will not optimize this content again."}), 200

    except Exception as e:
        print(f"Error in /feedback route: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/')
@app.route('/<path:path>')
def serve_react_app(path='index.html'):
    return send_from_directory(app.static_folder, path)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
