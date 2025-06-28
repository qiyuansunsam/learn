# data_manager.py
import json
import os
from pathlib import Path
import config # Import your config file

def get_topic_path(topic_name: str) -> Path:
    """Gets the base directory path for a given topic."""
    return Path(config.TOPICS_BASE_DIR) / topic_name

def get_context_folder(topic_name: str) -> Path:
    """Gets the context folder path for a topic."""
    return get_topic_path(topic_name) / "context"

def get_examples_folder(topic_name: str) -> Path:
    """Gets the examples folder path for a topic."""
    return get_topic_path(topic_name) / "examples"

def get_question_bank_file(topic_name: str) -> Path:
    """Gets the question bank JSON file path for a topic."""
    return get_topic_path(topic_name) / "question_bank.json"

def get_available_topics() -> list[str]:
    """Lists available topics by looking for directories in the base path."""
    base_path = Path(config.TOPICS_BASE_DIR)
    if not base_path.is_dir():
        return []
    return sorted([d.name for d in base_path.iterdir() if d.is_dir()])

def create_topic(topic_name: str) -> bool:
    """Creates the necessary directory structure for a new topic."""
    if not topic_name or topic_name.isspace():
         print("Error: Topic name cannot be empty.")
         return False
    if topic_name in get_available_topics():
        print(f"Topic '{topic_name}' already exists.")
        return True # Or False, depending on desired behavior

    topic_path = get_topic_path(topic_name)
    context_path = get_context_folder(topic_name)
    examples_path = get_examples_folder(topic_name)

    try:
        topic_path.mkdir(parents=True, exist_ok=True)
        context_path.mkdir(exist_ok=True)
        examples_path.mkdir(exist_ok=True)
        # Create an empty question bank file
        save_question_bank(topic_name, [])
        print(f"Created topic structure for '{topic_name}' at {topic_path}")
        return True
    except OSError as e:
        print(f"Error creating topic '{topic_name}': {e}")
        return False

def load_question_bank(topic_name: str) -> list[dict]:
    """Loads the question bank for a specific topic."""
    filepath = get_question_bank_file(topic_name)
    if not filepath.exists():
        print(f"Question bank file not found for topic '{topic_name}'. Starting fresh.")
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            history = json.load(f)
            if isinstance(history, list):
                print(f"Loaded {len(history)} questions for topic '{topic_name}' from {filepath}")
                return history
            else:
                print(f"Warning: Invalid format in bank file {filepath}. Expected a list. Returning empty list.")
                return []
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from bank file {filepath}. File might be corrupt. Returning empty list.")
        return []
    except Exception as e:
        print(f"Error loading question bank file {filepath}: {e}")
        return []

def save_question_bank(topic_name: str, questions: list[dict]):
    """Saves the list of questions for a specific topic."""
    filepath = get_question_bank_file(topic_name)
    try:
        # Ensure the parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=4)
            print(f"Saved {len(questions)} questions for topic '{topic_name}' to {filepath}")
    except Exception as e:
        print(f"Error saving question bank file {filepath}: {e}")

def add_questions_to_bank(topic_name: str, new_questions: list[dict]):
    """Adds new, unique questions to the topic's bank."""
    if not new_questions:
        return

    current_bank = load_question_bank(topic_name)
    existing_question_texts = {q.get('question', '').strip() for q in current_bank if q.get('question')}
    added_count = 0

    for q_new in new_questions:
        q_text = q_new.get('question', '').strip()
        # Add if it has text and is not already in the bank (case-sensitive check)
        if q_text and q_text not in existing_question_texts:
            current_bank.append(q_new)
            existing_question_texts.add(q_text) # Add to set to prevent adding duplicates from the *new* list
            added_count += 1

    if added_count > 0:
        print(f"Adding {added_count} new unique questions to bank for topic '{topic_name}'.")
        save_question_bank(topic_name, current_bank)
    else:
        print(f"No new unique questions found to add for topic '{topic_name}'.")

def format_bank_for_prompt(question_bank: list[dict], relevant_source_pdfs: list[str] = None) -> str:
    """
    Formats question bank questions into a string for the Gemini prompt history.
    If relevant_source_pdfs is provided, filters the bank to include only questions
    derived from at least one of those PDFs.
    """
    if not question_bank:
        return "No existing questions in the bank."

    filtered_bank = question_bank
    if relevant_source_pdfs:
        filtered_bank = []
        for q in question_bank:
            q_sources = q.get('source_pdfs')
            if isinstance(q_sources, list):
                # Check for any overlap between question's sources and relevant sources
                if any(source_pdf in q_sources for source_pdf in relevant_source_pdfs):
                    filtered_bank.append(q)
        if not filtered_bank:
            return "No existing questions in the bank relevant to the selected PDF(s)."

    history_text = "\n\n--- Existing Question Bank (Avoid Duplicates and Use as Examples) ---\n"
    for i, q in enumerate(filtered_bank):
        q_text = q.get('question', 'N/A')
        options_str = ""
        options = q.get('options', {})
        if isinstance(options, dict):
             options_str = "\n".join([f"  {k}) {v}" for k, v in options.items()])
        correct = q.get('correct_answer', 'N/A')
        sources = q.get('source_pdfs', [])
        source_info = f" (Sources: {', '.join(sources)})" if sources else ""
        history_text += f"{i+1}. Question: {q_text}{source_info}\n{options_str}\n   Correct Answer: {correct}\n---\n"
    history_text += "--- End of Existing Question Bank ---\n"
    return history_text
