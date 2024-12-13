from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
from pymongo import MongoClient
import config

app = Flask(__name__)
CORS(app)

openai.api_key = config.OPENAI_API_KEY

client = MongoClient('mongodb://localhost:27017/')
db = client['KeywordDB']
primary_keywords_collection = db['Primary']
secondary_keywords_collection = db['Secondary']
long_tail_keywords_collection = db['Long-Tail']

def fetch_keywords_from_db():
    try:
        primary_keywords = list(primary_keywords_collection.find().sort([('searchVolume', -1), ('seoDifficulty', 1)]).limit(5))
        secondary_keywords = list(secondary_keywords_collection.find().sort([('searchVolume', -1), ('seoDifficulty', 1)]).limit(3))
        long_tail_keywords = list(long_tail_keywords_collection.find().sort([('searchVolume', -1), ('seoDifficulty', 1)]).limit(2))

        keywords = primary_keywords + secondary_keywords + long_tail_keywords
        if not keywords:
            print("No keywords found in the database.")
        else:
            print(f"Fetched keywords from DB: {keywords}")
        return [kw['keyword'] for kw in keywords]
    except Exception as e:
        print(f"Error fetching keywords from MongoDB: {e}")
        return []

def insert_keywords_with_gpt(text, keywords):
    try:

        prompt = (
            f"Rewrite the following text by inserting each of the following keywords naturally and meaningfully "
            f"into the text: {', '.join(keywords)}. Ensure the flow and marketing tone are maintained.\n\n"
            f"Original Text:\n{text}\n\n"
            f"Rewritten Text:"
        )

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a marketing expert who optimizes content for SEO and readability."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        
        enhanced_text = response['choices'][0]['message']['content']
        print(f"GPT-4 Response: {enhanced_text}")
        return enhanced_text
    
    except Exception as e:
        print(f"Error during keyword insertion with GPT: {e}")
        return text

def highlight_keywords(optimized_text, keywords):
    for kw in keywords:
        optimized_text = optimized_text.replace(kw, f"<span style='color:red;'>{kw}</span>")
    return optimized_text

@app.route('/optimize', methods=['POST'])
def optimize_content():
    try:
        data = request.json
        text = data.get('text', '')

        if not text:
            return jsonify({"error": "No content provided"}), 400

        keywords = fetch_keywords_from_db()

        if not keywords:
            return jsonify({"error": "No keywords found"}), 500

        optimized_text = insert_keywords_with_gpt(text, keywords)
        
        optimized_text = highlight_keywords(optimized_text, keywords)

        return jsonify({
            'optimizedText': optimized_text,
            'highlightedKeywords': keywords
        })

    except Exception as e:
        print(f"Error in /optimize route: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
