# Example app.py (using Flask) - Added /clear_history route
import os
from flask import Flask, render_template, request, jsonify
from pathlib import Path # Make sure Path is imported
import random # Needed for shuffling (although shuffling happens in JS)
import traceback # For better error logging

import config
import data_manager as dm
import file_handler as fh
import gemini_handler as gh

app = Flask(__name__)

# Configure Gemini once on startup
if not gh.configure_gemini():
    print("CRITICAL: Failed to configure Gemini API on startup.")

# --- Routes ---

@app.route('/')
def index():
    """Serves the main HTML page."""
    topics = dm.get_available_topics()
    return render_template('index.html', topics=topics, current_topic=topics[0] if topics else None)

@app.route('/get_bank', methods=['GET'])
def get_question_bank():
    """API endpoint to fetch the question bank for a topic."""
    topic = request.args.get('topic')
    if not topic:
        return jsonify({"error": "Topic parameter is required"}), 400
    bank = dm.load_question_bank(topic)
    # Shuffling will be done in JavaScript before displaying
    return jsonify(bank)

@app.route('/get_context_files', methods=['GET'])
def get_context_files():
    """API endpoint to list PDF files in the topic's context folder."""
    topic = request.args.get('topic')
    if not topic:
        return jsonify({"error": "Topic parameter is required"}), 400

    context_folder_path = dm.get_context_folder(topic)
    pdf_files = []
    if context_folder_path.is_dir():
        pdf_files = sorted([f.name for f in context_folder_path.glob('*.pdf')])
    return jsonify({"files": pdf_files})


@app.route('/generate', methods=['POST'])
def handle_generate():
    """API endpoint to trigger question generation from selected existing PDFs."""
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Request body must be JSON"}), 400

    topic = data.get('topic')
    num_questions_str = data.get('num_questions')
    selected_files = data.get('selected_files')

    # --- Validation ---
    if not topic: return jsonify({"status": "error", "message": "Topic is missing"}), 400
    if not num_questions_str: return jsonify({"status": "error", "message": "Number of questions is missing"}), 400
    if not selected_files or not isinstance(selected_files, list) or len(selected_files) == 0:
         return jsonify({"status": "error", "message": "No context files selected"}), 400

    try:
        num_questions = int(num_questions_str)
        if num_questions <= 0: raise ValueError()
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid number of questions"}), 400

    print(f"Received generation request for topic '{topic}', count: {num_questions} from files: {selected_files}")

    extracted_text = ""
    context_folder_path = dm.get_context_folder(topic)

    if not context_folder_path.is_dir():
         return jsonify({"status": "error", "message": f"Context folder for topic '{topic}' not found on server."}), 400

    if not fh.PDF_LIB_AVAILABLE:
         print("PDF library (pypdf) not available.")
         return jsonify({"status": "error", "message": "PDF processing library not available on server."}), 500

    try:
        for filename in selected_files:
            if ".." in filename or filename.startswith("/"):
                 print(f"Warning: Skipping potentially unsafe filename: {filename}")
                 continue

            file_path = context_folder_path / filename
            if file_path.is_file() and filename.lower().endswith('.pdf'):
                print(f"  Reading selected file: {file_path}")
                try:
                    from pypdf import PdfReader, errors
                    reader = PdfReader(file_path)
                    file_text = ""
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text: file_text += page_text + "\n"
                    if file_text:
                        extracted_text += file_text + f"\n--- End of Document: {filename} ---\n\n"
                        print(f"    Extracted ~{len(file_text)} chars from {filename}.")
                    else: print(f"    No text extracted from {filename}.")
                except errors.PdfReadError: print(f"    Warning: Could not read corrupted/encrypted PDF: {filename}")
                except Exception as e: print(f"    Error reading {filename}: {e}")
            else: print(f"  Warning: Selected file not found or not a PDF: {filename}")

        if not extracted_text.strip():
             return jsonify({"status": "error", "message": "Could not extract any text from the selected PDF file(s)."}), 400

        print("Loading current question bank for history...")
        current_bank = dm.load_question_bank(topic)
        history_text = dm.format_bank_for_prompt(current_bank, relevant_source_pdfs=selected_files)

        print(f"Sending context ({len(extracted_text)} chars) and history to Gemini...")
        new_mcqs = gh.generate_new_mcqs(extracted_text, history_text, num_questions)

        if new_mcqs:
            print(f"Received {len(new_mcqs)} new MCQs from Gemini.")
            # Tag each new MCQ with the list of PDF files used for its generation
            for mcq in new_mcqs:
                mcq['source_pdfs'] = selected_files
            dm.add_questions_to_bank(topic, new_mcqs)
            return jsonify({"status": "success", "message": f"Generated and added {len(new_mcqs)} new questions.", "new_questions_count": len(new_mcqs)})
        else:
            print("No new MCQs were successfully generated or parsed by Gemini.")
            return jsonify({"status": "success", "message": "Context processed, but no new unique questions were generated by Gemini.", "new_questions_count": 0})

    except Exception as e:
        print(f"Error during generation process: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"An internal error occurred: {e}"}), 500


@app.route('/format_examples', methods=['POST'])
def handle_format_examples():
    data = request.json
    topic = data.get('topic')
    if not topic: return jsonify({"status": "error", "message": "Topic is missing"}), 400

    print(f"Received format examples request for topic '{topic}'")
    try:
        examples_folder = dm.get_examples_folder(topic)
        example_text = fh.read_text_files_in_folder(str(examples_folder))
        if not example_text or example_text.isspace():
             return jsonify({"status": "success", "message": "No text found in example files to format.", "formatted_count": 0})

        formatted_mcqs = gh.format_examples_to_mcq(example_text)
        count = len(formatted_mcqs)
        if count > 0:
            dm.add_questions_to_bank(topic, formatted_mcqs)
            return jsonify({"status": "success", "message": f"Formatted and added {count} questions from examples.", "formatted_count": count})
        else:
             return jsonify({"status": "success", "message": "Examples processed, but no MCQs were formatted.", "formatted_count": 0})

    except Exception as e:
        print(f"Error formatting examples: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Error formatting examples: {e}"}), 500


@app.route('/add_topic', methods=['POST'])
def handle_add_topic():
    data = request.json
    topic_name = data.get('topic_name')
    if not topic_name or topic_name.isspace():
        return jsonify({"status": "error", "message": "Topic name cannot be empty"}), 400

    print(f"Received add topic request for: '{topic_name}'")
    try:
        # Check existence *before* trying to create
        if topic_name in dm.get_available_topics():
             return jsonify({"status": "error", "message": f"Topic '{topic_name}' already exists."}), 400

        success = dm.create_topic(topic_name)
        if success:
            all_topics = dm.get_available_topics()
            return jsonify({"status": "success", "message": f"Topic '{topic_name}' created.", "topics": all_topics})
        else:
             # create_topic prints errors, assume failure if not success
             return jsonify({"status": "error", "message": f"Failed to create topic '{topic_name}'. Check server logs."}), 500
    except Exception as e:
        print(f"Error adding topic: {e}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Internal server error adding topic: {e}"}), 500

# --- NEW Endpoint: Clear History ---
@app.route('/clear_history', methods=['POST']) # Using POST for action that modifies data
def handle_clear_history():
    """API endpoint to clear the question bank for a specific topic."""
    data = request.json
    topic = data.get('topic')
    if not topic:
        return jsonify({"status": "error", "message": "Topic is missing"}), 400

    print(f"Received request to clear history for topic: '{topic}'")

    # Check if topic exists before trying to clear
    if topic not in dm.get_available_topics():
         return jsonify({"status": "error", "message": f"Topic '{topic}' not found."}), 404 # Not Found

    try:
        # Overwrite the bank with an empty list
        dm.save_question_bank(topic, [])
        print(f"Successfully cleared question bank for topic: '{topic}'")
        return jsonify({"status": "success", "message": f"Question history for topic '{topic}' has been cleared."})
    except Exception as e:
        print(f"Error clearing history for topic '{topic}': {e}")
        traceback.print_exc()
        # Internal Server Error
        return jsonify({"status": "error", "message": f"An internal error occurred while clearing history: {e}"}), 500


if __name__ == '__main__':
    # Consider setting debug=False for production
    app.run(debug=True, host='0.0.0.0', port=5000)
