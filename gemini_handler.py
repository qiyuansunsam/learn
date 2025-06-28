# gemini_handler.py
import google.generativeai as genai
import config
import re # For more robust parsing

# --- Gemini Configuration ---
_MODEL = None

def configure_gemini():
    """Configures the Gemini API using the key from config."""
    global _MODEL
    try:
        if not config.GOOGLE_API_KEY or "YOUR_DEFAULT_API_KEY_HERE" in config.GOOGLE_API_KEY:
             print("Error: Gemini API Key not configured in config.py or .env file.")
             print("Please set the GOOGLE_API_KEY.")
             _MODEL = None
             return False
        genai.configure(api_key=config.GOOGLE_API_KEY)
        _MODEL = genai.GenerativeModel(config.GEMINI_MODEL_NAME)
        print(f"Gemini API configured successfully with model: {config.GEMINI_MODEL_NAME}")
        return True
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        _MODEL = None
        return False

def _parse_mcq_response(text: str) -> list[dict]:
    """Parses the Gemini response text into a list of MCQ dictionaries."""
    questions = []
    # Regex to find question blocks, handling variations in spacing and numbering
    # This regex looks for "Question:" possibly preceded by a number and dot,
    # then captures the question text, options block, and correct answer line.
    pattern = re.compile(
        r"^\s*(?:\d+\.\s*)?Question:\s*(.*?)\s*" # Capture question text
        r"Options:\s*\n"                         # Options header
        r"^\s*A\)\s*(.*?)\s*\n"                  # Option A
        r"^\s*B\)\s*(.*?)\s*\n"                  # Option B
        r"^\s*C\)\s*(.*?)\s*\n"                  # Option C
        r"^\s*D\)\s*(.*?)\s*\n"                  # Option D
        r"^\s*Correct Answer:\s*([A-D])\s*$",    # Correct Answer (single letter)
        re.MULTILINE | re.IGNORECASE             # Multiline and case-insensitive
    )

    matches = pattern.finditer(text)

    for match in matches:
        question_text = match.group(1).strip()
        options = {
            "A": match.group(2).strip(),
            "B": match.group(3).strip(),
            "C": match.group(4).strip(),
            "D": match.group(5).strip(),
        }
        correct_answer = match.group(6).strip().upper()

        if question_text and all(options.values()) and correct_answer in options:
            questions.append({
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer,
            })
        else:
             # Log the block that failed parsing for debugging
             print(f"\n--- Skipping malformed block detected by regex ---\n{match.group(0)}\n--------------------------------------------------")


    if not questions and text.strip(): # If regex found nothing, try the old split method as fallback
         print("Warning: Regex parsing failed, attempting fallback split method.")
         # (Include the parsing logic from your original script here as a fallback)
         # ... (omitted for brevity, but you'd paste your original parsing loop here)
         # Make sure the fallback also appends to the 'questions' list
         pass # Placeholder for your original parsing logic


    print(f"Parsed {len(questions)} questions from response.")
    return questions


def format_examples_to_mcq(example_text: str) -> list[dict]:
    """
    Sends raw example text (Q&A pairs) to Gemini and asks it to
    format them into the standard MCQ structure.
    """
    if not _MODEL:
        print("Error: Gemini model not initialized. Call configure_gemini() first.")
        return []
    if not example_text or example_text.isspace():
         print("No example text provided to format.")
         return []

    prompt = f"""
    You are an expert in creating educational multiple-choice questions.
    Based on the following raw text, which contains questions and potentially their answers or related concepts,
    please format each distinct concept into a standard multiple-choice question (MCQ).

    For each concept you identify, create one MCQ with:
    1. A clear question text.
    2. Four plausible options labeled A, B, C, D. One option must be the correct answer based on the provided text.
    3. A clear indication of the correct answer using the format "Correct Answer: [Letter]".

    Ensure the options are relevant and the incorrect options (distractors) are plausible but clearly wrong according to the text.

    Here is the raw text:
    --- START OF RAW TEXT ---
    {example_text}
    --- END OF RAW TEXT ---

    Format each generated MCQ exactly like this example:

    Question: What is the capital of France?
    Options:
    A) London
    B) Berlin
    C) Paris
    D) Madrid
    Correct Answer: C

    Generate as many MCQs as you can derive from the provided text. Separate each complete MCQ block with a blank line.
    """

    try:
        print("Sending examples to Gemini for formatting...")
        response = _MODEL.generate_content(prompt)
        # print("--- Gemini Formatting Response ---") # Optional: Debugging
        # print(response.text)
        # print("----------------------------------")
        return _parse_mcq_response(response.text)
    except Exception as e:
        print(f"Error during Gemini API call for formatting examples: {e}")
        return []


def generate_new_mcqs(context_text: str, history_text: str, num_questions: int) -> list[dict]:
    """
    Generates new MCQs based on context, using history/bank for examples and avoiding duplicates.
    """
    if not _MODEL:
        print("Error: Gemini model not initialized. Call configure_gemini() first.")
        return []
    if not context_text or context_text.isspace():
         print("No context text provided for generation.")
         return []

    prompt = f"""
    You are an expert in creating educational multiple-choice questions.
    Your task is to generate {num_questions} NEW multiple-choice questions based *only* on the provided 'Context Text'.

    You are also given an 'Existing Question Bank'. Use this bank for two purposes:
    1.  **Avoid Duplication:** DO NOT generate questions that are identical or very similar in meaning to the questions already present in the bank.
    2.  **Style Guide:** Use the format and style of the questions in the bank as a reference for the new questions you create.

    Each new question must have:
    1.  A clear question text derived from the 'Context Text'.
    2.  Four plausible options labeled A, B, C, D. One option must be the correct answer based *only* on the 'Context Text'.
    3.  A clear indication of the correct answer using the format "Correct Answer: [Letter]".

    Ensure the questions cover different aspects of the 'Context Text', are challenging but fair, and the correct answer letter matches one of the options provided.

    --- Context Text ---
    {context_text}
    --- End of Context Text ---

    {history_text}

    Generate exactly {num_questions} new, unique MCQs based on the 'Context Text' above, following the specified format.
    Format each new question exactly like this:

    Question: [New question text based on Context Text]
    Options:
    A) [Option A]
    B) [Option B]
    C) [Option C]
    D) [Option D]
    Correct Answer: [Letter]
    """

    try:
        print(f"Sending context and history to Gemini for generating {num_questions} new questions...")
        response = _MODEL.generate_content(prompt)
        # print("--- Gemini Generation Response ---") # Optional: Debugging
        # print(response.text)
        # print("----------------------------------")
        return _parse_mcq_response(response.text)
    except Exception as e:
        print(f"Error during Gemini API call for generating new questions: {e}")
        return []

