import google.generativeai as genai
import json # Needed for handling JSON data
from pathlib import Path # For handling file paths
import PyPDF2 # Make sure this is imported if using the PDF reader function
# You would need to install and import a PDF reading library
# Example: import PyPDF2
# You might also need pathlib
# Example: from pathlib import Path

# --- (Keep your Gemini API Key Setup) ---
GOOGLE_API_KEY = "AIzaSyCMOOMRp4KlgHMoJGOCTn4fsJb47l8vv4g" # Replace with your actual Gemini API key
genai.configure(api_key=GOOGLE_API_KEY)

# --- (Keep the generate_mcq function as is) ---
def generate_mcq(lecture_notes_text, question_answer_text, num_questions=20):
    """
    Generates multiple-choice questions using the Gemini API, incorporating lecture
    notes and question/answer examples. Uses an updated model name.

    Args:
        lecture_notes_text (str): Combined text from lecture notes.
        question_answer_text (str): Combined text from question/answer files.
        num_questions (int): Number of questions to generate. Default is 4.

    Returns:
        list: A list of dictionaries, where each dictionary represents a question
              and its details (question, options, correct answer). Returns an
              empty list on error.
    """
    # --- Use an updated model name ---
    # Changed "gemini-pro" to "gemini-1.5-flash-latest"
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    # --- End of change ---

    # Combine lecture notes and tutorial content for a more comprehensive context
    combined_content = "Lecture Notes:\n" + lecture_notes_text + "\n\n"
    combined_content += "Question/Answer Examples and history:\n" + question_answer_text

    prompt = f"""
    You are an expert in creating educational materials. Based on the following
    lecture notes and question/answer examples, generate {num_questions} multiple-choice
    questions. Each question should have 4 options (labeled A, B, C, D), and clearly indicate the
    correct answer using the format "Correct Answer: [Letter]".

    Here is the content:
    {combined_content}

    Format each question exactly as follows:

    Question: [Question text]
    Options:
    A) [Option A]
    B) [Option B]
    C) [Option C]
    D) [Option D]
    Correct Answer: [Letter of the correct answer (e.g., A, B, C, or D)]

    Ensure that the questions are diverse, cover different aspects of the material,
    and are challenging but fair. Do not include the same question twice or is in the examples and history. Ensure the correct answer letter matches one of the options provided.
    """

    try:
        response = model.generate_content(prompt)
        print(response.text) # Uncomment for debugging the raw response

        # Parse the generated text into a list of question dictionaries
        questions = []
        # Split by "Question: " and ignore the first empty element
        question_blocks = response.text.strip().split("\nQuestion: ")
        if not question_blocks[0].strip(): # Handle potential empty first block if response starts with \n
             question_blocks = question_blocks[1:]
        else:
             # If the first block isn't empty, prepend "Question: " back to it
             question_blocks[0] = "Question: " + question_blocks[0]


        for block in question_blocks:
            block = block.strip() # Remove leading/trailing whitespace from the block
            if not block:
                continue # Skip empty blocks

            lines = block.splitlines() # Split the block into lines

            # Basic validation: Need at least Question line, 4 option lines, 1 answer line
            if len(lines) < 6:
                print(f"\n--- Skipping malformed question block (too few lines) ---\n{block}\n--------------------------------------------------")
                continue

            # Extract question text (remove "Question: " prefix)
            question_text = lines[0]



            # Extract options
            options = {}
            option_lines = []
            # Find the start of options, usually line 1
            options_start_index = -1
            if len(lines) > 2 and lines[2].strip().startswith("Options:"):
                 options_start_index = 3 # Options start on the line after "Options:"
            elif len(lines) > 2 and lines[2].strip().upper().startswith("A)"):
                 options_start_index = 2 # Options start directly on line 1
            else:
                 print(f"\n--- Skipping malformed question block (cannot find start of options) ---\n{block}\n--------------------------------------------------")
                 continue

            if options_start_index != -1 and len(lines) >= options_start_index + 4:
                 option_lines = lines[options_start_index : options_start_index + 4]
                 for line in option_lines:
                     line = line.strip()
                     # Check for format like "A) Text"
                     if len(line) > 2 and line[1] == ')' and line[0].isalpha():
                         option_letter = line[0].upper()
                         option_text = line[2:].strip()
                         options[option_letter] = option_text
                     else:
                          # If format doesn't match, break parsing for this block
                          options = {} # Reset options as they are malformed
                          print(f"\n--- Skipping malformed question block (bad option format: '{line}') ---\n{block}\n--------------------------------------------------")
                          break
            else:
                 print(f"\n--- Skipping malformed question block (not enough option lines found) ---\n{block}\n--------------------------------------------------")
                 continue # Skip if options format is wrong

            if not options or len(options) != 4: # Ensure we got 4 valid options
                 continue # Skip if options parsing failed

            # Extract correct answer
            correct_answer = ""
            # Find the line starting with "Correct Answer: "
            correct_answer_line_index = -1
            for i in range(options_start_index + 4, len(lines)):
                 if lines[i].strip().startswith("Correct Answer:"):
                      correct_answer_line_index = i
                      break

            if correct_answer_line_index != -1:
                 correct_answer_line = lines[correct_answer_line_index].strip()
                 try:
                     correct_answer = correct_answer_line.split("Correct Answer:")[1].strip().upper()
                     # Ensure the extracted answer is just a single letter A, B, C, or D
                     if len(correct_answer) != 1 or correct_answer not in "ABCD":
                          print(f"\n--- Skipping malformed question block (invalid correct answer format: '{correct_answer}') ---\n{block}\n--------------------------------------------------")
                          correct_answer = "" # Invalidate if format is wrong
                 except IndexError:
                      print(f"\n--- Skipping malformed question block (cannot parse correct answer line: '{correct_answer_line}') ---\n{block}\n--------------------------------------------------")
                      correct_answer = "" # Invalidate if split fails
            else:
                 print(f"\n--- Skipping malformed question block (missing 'Correct Answer:' line) ---\n{block}\n--------------------------------------------------")
                 continue # Skip if answer line not found

            # Final validation before adding
            if not question_text or len(options) != 4 or not correct_answer or correct_answer not in options:
                 if not correct_answer:
                      # Already printed a message if correct_answer line was missing/malformed
                      pass
                 elif correct_answer not in options:
                      print(f"\n--- Skipping question: Correct answer '{correct_answer}' not found in options {list(options.keys())} ---\n{block}\n--------------------------------------------------")
                 else: # Should not happen based on previous checks, but as a safeguard
                      print(f"\n--- Skipping question due to validation failure ---\n{block}\n--------------------------------------------------")
                 continue # Skip if any part is invalid

            # Add the successfully parsed question to the list
            questions.append({
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer,
            })

        return questions

    except Exception as e:
        print(f"Error during Gemini API call or response processing: {e}")
        # You might want to inspect the 'response' object here if it exists
        # print("Response object:", response)
        return []


def read_all_pdfs_in_folder(folder_path_str):
    """
    Reads text content from all PDF files within a specified folder.

    Args:
        folder_path_str (str): The path to the folder containing PDF files.

    Returns:
        str: The combined text content extracted from all PDF files in the folder.
             Returns an empty string if the folder doesn't exist or no PDFs are found/readable.
    """
    all_text = ""
    folder_path = Path(folder_path_str) # Convert string path to Path object

    if not folder_path.is_dir():
        print(f"Error: Directory not found at {folder_path_str}")
        return "" # Return empty string if directory doesn't exist

    print(f"Reading PDF files from: {folder_path}")
    pdf_files = list(folder_path.glob('*.pdf')) # Find all files ending with .pdf

    if not pdf_files:
        print(f"No PDF files found in {folder_path_str}")
        return ""

    for pdf_file in pdf_files:
        try:
            # Open the PDF file in binary read mode
            with open(pdf_file, 'rb') as file:
                reader = PyPDF2.PdfReader(file) # Create a PDF reader object
                num_pages = len(reader.pages)
                print(f"  Reading {pdf_file.name} ({num_pages} pages)...")
                # Iterate through each page and extract text
                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text: # Add text only if extraction was successful
                        all_text += page_text + "\n" # Add extracted text and a newline
            all_text += "\n--- End of Document: " + pdf_file.name + " ---\n\n" # Separator between files
        except PyPDF2.errors.PdfReadError:
             print(f"  Warning: Could not read corrupted or encrypted PDF: {pdf_file.name}")
        except Exception as e:
            # Catch other potential errors during file processing
            print(f"  Error reading {pdf_file.name}: {e}")

    print(f"Finished reading {len(pdf_files)} PDF file(s).")
    return all_text # Return the combined text from all readable PDFs

def load_question_history(filepath):
    """
    Loads question history from a JSON file.

    Args:
        filepath (Path): Path object for the history file.

    Returns:
        list: A list of question dictionaries, or an empty list if
              the file doesn't exist or is invalid.
    """
    if not filepath.exists():
        print(f"History file not found at {filepath}. Starting fresh.")
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            history = json.load(f)
            # Basic validation: Check if it's a list
            if isinstance(history, list):
                 print(f"Loaded {len(history)} questions from {filepath}")
                 return history
            else:
                 print(f"Warning: Invalid format in history file {filepath}. Expected a list.")
                 return []
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from history file {filepath}. File might be corrupt.")
        return []
    except Exception as e:
        print(f"Error loading history file {filepath}: {e}")
        return []

def save_question_history(filepath, questions):
    """
    Saves the list of questions to a JSON file.

    Args:
        filepath (Path): Path object for the history file.
        questions (list): The list of question dictionaries to save.
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            # Use indent for readability in the JSON file
            json.dump(questions, f, indent=4)
            print(f"Saved {len(questions)} questions to {filepath}")
    except Exception as e:
        print(f"Error saving history file {filepath}: {e}")

def format_history_for_prompt(historical_questions):
    """
    Formats historical questions into a string for the Gemini prompt.
    Includes only the question text to avoid making the prompt too long.

    Args:
        historical_questions (list): List of question dictionaries.

    Returns:
        str: A string containing the text of historical questions.
    """
    if not historical_questions:
        return ""

    history_text = "\n\n--- Previously Generated Questions (Avoid Duplicates) ---\n"
    for i, q in enumerate(historical_questions):
        # Ensure the question dictionary has the 'question' key
        if 'question' in q:
            history_text += f"{i+1}. {q['question']}\n"
        else:
            # Handle cases where a historical entry might be malformed
             print(f"Warning: Malformed historical question entry found at index {i}")

    history_text += "--- End of Previously Generated Questions ---\n"
    return history_text

# --- Updated Main Function ---

def main():
    """
    Main function to load data, generate questions incorporating history,
    run an interactive quiz on new questions, and save updated history.
    """
    # --- Configuration ---
    lecture_folder = "lln/lec"   # Your lecture notes folder
    question_folder = "lln/ques" # Your questions folder (e.g., .txt files)
    history_filename = "lln/question_history.json" # File to store question history

    history_filepath = Path(history_filename)

    # --- Load Data ---
    # 1. Load historical questions
    historical_questions = load_question_history(history_filepath)

    # 2. Load lecture and base question/answer text
    lecture_text = read_all_pdfs_in_folder(lecture_folder)
    base_question_text = read_all_pdfs_in_folder(question_folder)

    if not lecture_text and not base_question_text:
        print("Error: Could not load content from lecture or question folders. Cannot generate new questions.")
        # Still proceed to save history if it was loaded, but skip generation/quiz
        if historical_questions:
             save_question_history(history_filepath, historical_questions)
        return

    # 3. Format history for the prompt context
    history_prompt_text = format_history_for_prompt(historical_questions)

    # 4. Combine base question text with history for the full context
    full_question_context = base_question_text + history_prompt_text

    # --- Generate New Questions ---
    num_new_questions_to_generate = input("How many questions:\n>") # How many new questions to ask for
    
    print(f"\nGenerating {num_new_questions_to_generate} new questions...")
    new_questions = generate_mcq(lecture_text, full_question_context, num_questions=num_new_questions_to_generate)

    # --- Interactive Quiz on New Questions ---
    if new_questions:
        print("\n--- Starting Quiz with Newly Generated Questions ---")
        num_correct = 0
        for i, q in enumerate(new_questions):
            print(f"\nQuestion {i+1}: {q['question']}")
            # Print options
            for letter, option_text in q['options'].items():
                print(f"  {letter}) {option_text}")

            # Get user answer
            while True:
                 ans = input("Your answer (A, B, C, or D)?\n> ").strip().upper()
                 if ans in ["A", "B", "C", "D"]:
                      break
                 else:
                      print("Invalid input. Please enter A, B, C, or D.")

            # Check answer and provide feedback
            if ans == q['correct_answer']:
                print("Correct!")
                num_correct += 1
            else:
                print(f"Incorrect. The correct answer was: {q['correct_answer']}")
            print("-" * 20) # Separator

        print(f"\n--- Quiz Complete ---")
        print(f"You answered {num_correct} out of {len(new_questions)} questions correctly.")

    else:
        print("\nNo new questions were generated.")
        if not lecture_text and not base_question_text:
             print("Ensure lecture/question files are available and readable.")
        else:
             print("Could not generate new questions. Check API key and model availability.")


    # --- Save Updated History (Old + New) ---
    # Combine historical and newly generated questions
    all_questions = historical_questions + new_questions
    # Remove potential duplicates before saving (optional, based on exact question text)
    # This simple check assumes identical question strings mean duplicates.
    unique_questions_dict = {q['question']: q for q in all_questions}
    unique_questions_list = list(unique_questions_dict.values())

    if len(unique_questions_list) < len(all_questions):
        print(f"Removed {len(all_questions) - len(unique_questions_list)} duplicate questions before saving.")


    save_question_history(history_filepath, unique_questions_list)


if __name__ == "__main__":
    # --- Ensure API Key is configured ---
    # It's better to use environment variables or a config file in real applications
    # For simplicity here, you might uncomment and set the key directly:
    # GOOGLE_API_KEY = "YOUR_GEMINI_API_KEY" # Replace with your actual key
    # try:
    #    genai.configure(api_key=GOOGLE_API_KEY)
    # except Exception as e:
    #    print(f"Error configuring Gemini API: {e}")
    #    print("Please ensure your API key is set correctly.")
    #    exit() # Exit if API key is not configured

    main()