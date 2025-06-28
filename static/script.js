document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const topicSelect = document.getElementById('topic-select');
    const questionBankDisplay = document.getElementById('question-bank-display');
    const logDisplay = document.getElementById('log-display');
    const generateBtn = document.getElementById('generate-mcq-btn');
    const formatBtn = document.getElementById('format-examples-btn');
    const addTopicBtn = document.getElementById('add-topic-btn');
    const clearHistoryBtn = document.getElementById('clear-history-btn'); // New Button
    const numQuestionsInput = document.getElementById('num-questions');
    // const loadingOverlay = document.getElementById('loading-overlay'); // Overlay is removed
    const contextFileSelector = document.getElementById('context-file-selector');

    // --- Quiz DOM Elements ---
    const quizArea = document.getElementById('quiz-area');
    const questionText = document.getElementById('question-text');
    const optionsContainer = document.getElementById('options-container');
    const submitAnswerBtn = document.getElementById('submit-answer-btn');
    const feedbackText = document.getElementById('feedback-text');
    const prevQuestionBtn = document.getElementById('prev-question-btn');
    const nextQuestionBtn = document.getElementById('next-question-btn');
    const questionCounter = document.getElementById('question-counter');
    const quizPdfFilterContainer = document.getElementById('quiz-pdf-filter-container');

    // --- State Variables ---
    let currentTopicBank = [];
    let currentQuestionIndex = 0;
    let activeQuizBank = []; // Holds the currently active set of questions for the quiz (can be filtered)
    let answerSubmitted = false;

    // --- Helper Functions ---
    function logMessage(message, isError = false) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = `[${timestamp}] ${message}\n`;
        logDisplay.textContent += logEntry;
        logDisplay.scrollTop = logDisplay.scrollHeight; // Auto-scroll
        if (isError) {
            console.error(message);
        } else {
            console.log(message);
        }
    }

    function setLoading(isLoading) {
        // loadingOverlay.style.display = isLoading ? 'flex' : 'none'; // Overlay display logic removed
        generateBtn.disabled = isLoading;
        formatBtn.disabled = isLoading;
        addTopicBtn.disabled = isLoading;
        clearHistoryBtn.disabled = isLoading; // Disable clear button too
        topicSelect.disabled = isLoading;
        submitAnswerBtn.disabled = isLoading;
        prevQuestionBtn.disabled = isLoading;
        nextQuestionBtn.disabled = isLoading;
        // Disable context file checkboxes
        contextFileSelector.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.disabled = isLoading);
        // Disable quiz PDF filter checkboxes
        quizPdfFilterContainer.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.disabled = isLoading);
    }

    function displayQuestion(index) {
        if (!activeQuizBank || index < 0 || index >= activeQuizBank.length) {
            logMessage("Invalid question index.", true);
            // Update UI to show no questions available
            questionText.textContent = 'No question to display for the current filter.';
            optionsContainer.innerHTML = '';
            feedbackText.textContent = '';
            questionCounter.textContent = 'Question 0 of 0';
            prevQuestionBtn.disabled = true;
            nextQuestionBtn.disabled = true;
            submitAnswerBtn.disabled = true;
            if (activeQuizBank.length === 0 && currentTopicBank.length > 0) { // Filters resulted in no questions
                 questionText.textContent = 'No questions match the current PDF filter.';
            } else if (currentTopicBank.length === 0) { // No questions for topic
                 quizArea.style.display = 'none';
            }
            return;
        }

        answerSubmitted = false; // Reset submission state for new question
        const question = activeQuizBank[index];
        questionText.textContent = question.question || 'N/A';
        optionsContainer.innerHTML = ''; // Clear previous options
        feedbackText.textContent = ''; // Clear previous feedback
        feedbackText.className = 'mt-2'; // Reset feedback styling, keep margin

        // Check if options exist and are in the expected format
        if (question.options && typeof question.options === 'object') {
            // Sort options A, B, C, D for consistent display
            const sortedKeys = Object.keys(question.options).sort();

            sortedKeys.forEach(key => {
                const optionValue = question.options[key];
                const optionId = `option-${key}`;

                const formCheckDiv = document.createElement('div');
                formCheckDiv.classList.add('form-check');

                const radioInput = document.createElement('input');
                radioInput.type = 'radio';
                radioInput.name = 'mcqOption';
                radioInput.value = key;
                radioInput.id = optionId;
                radioInput.classList.add('form-check-input');
                // Re-enable radio buttons when displaying a new question
                radioInput.disabled = false;

                const label = document.createElement('label');
                label.htmlFor = optionId;
                label.classList.add('form-check-label');
                label.textContent = ` ${key}) ${optionValue}`;

                formCheckDiv.appendChild(radioInput);
                formCheckDiv.appendChild(label);
                optionsContainer.appendChild(formCheckDiv);
            });
        } else {
            optionsContainer.textContent = 'No options available for this question.';
        }

        // Update counter and button states
        questionCounter.textContent = `Question ${index + 1} of ${activeQuizBank.length}`;
        prevQuestionBtn.disabled = index === 0;
        nextQuestionBtn.disabled = index === activeQuizBank.length - 1;
        submitAnswerBtn.disabled = false; // Enable submit for the new question
        quizArea.style.display = 'block'; // Make sure quiz area is visible
    }

    function checkAnswer() {
        if (answerSubmitted) return; // Don't allow re-submission

        const selectedOption = optionsContainer.querySelector('input[name="mcqOption"]:checked');
        if (!selectedOption) {
            feedbackText.textContent = 'Please select an answer.';
            feedbackText.className = 'mt-2 feedback-incorrect';
            Swal.fire({
                icon: 'warning', title: 'Oops...', text: 'Please select an answer before submitting!',
            });
            return;
        }

        answerSubmitted = true;
        submitAnswerBtn.disabled = true; // Disable after submitting
        const userAnswer = selectedOption.value;
        const correctAnswer = activeQuizBank[currentQuestionIndex].correct_answer;

        // Disable all radio buttons after submission
        optionsContainer.querySelectorAll('input[name="mcqOption"]').forEach(radio => {
            radio.disabled = true;
        });

        // Provide feedback and highlight options
        const labels = optionsContainer.querySelectorAll('label');
        optionsContainer.querySelectorAll('.form-check-input').forEach(radio => {
            const label = radio.nextElementSibling; // Get the label associated with this radio
            if (radio.value === correctAnswer) {
                label.classList.add('correct-option');
            }
            if (radio.value === userAnswer && userAnswer !== correctAnswer) {
                label.classList.add('incorrect-option-selected');
            }
        });


        if (userAnswer === correctAnswer) {
            feedbackText.textContent = 'Correct!';
            feedbackText.className = 'mt-2 feedback-correct';
        } else {
            feedbackText.textContent = `Incorrect. The correct answer was ${correctAnswer}.`;
            feedbackText.className = 'mt-2 feedback-incorrect';
        }
    }

    // Function to fetch and display context files from the server
    async function fetchAndDisplayContextFiles(topic) {
        contextFileSelector.innerHTML = '<p>Loading available files...</p>'; // Show loading state
        if (!topic) {
            contextFileSelector.innerHTML = '<p>Select a topic to see available files.</p>';
            return;
        }
        logMessage(`Fetching context files for topic: ${topic}`);
        try {
            const response = await fetch(`/get_context_files?topic=${encodeURIComponent(topic)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            if (data.error) {
                logMessage(`Error fetching context files: ${data.error}`, true);
                contextFileSelector.innerHTML = `<p style="color: red;">Error loading files: ${data.error}</p>`;
            } else if (data.files && data.files.length > 0) {
                contextFileSelector.innerHTML = ''; // Clear loading message
                data.files.sort().forEach(filename => { // Sort filenames alphabetically
                    // Create a safe ID from the filename
                    const checkboxId = `file-${filename.replace(/[^a-zA-Z0-9_.-]/g, '-')}`;

                    const formCheckDiv = document.createElement('div');
                    formCheckDiv.classList.add('form-check');

                    const checkbox = document.createElement('input');
                    checkbox.classList.add('form-check-input');
                    checkbox.type = 'checkbox';
                    checkbox.id = checkboxId;
                    checkbox.value = filename; // Store filename in value
                    checkbox.name = 'contextFile';
                    
                    const label = document.createElement('label');
                    label.classList.add('form-check-label');
                    label.htmlFor = checkboxId;
                    label.textContent = ` ${filename}`;

                    formCheckDiv.appendChild(checkbox);
                    formCheckDiv.appendChild(label);
                    contextFileSelector.appendChild(formCheckDiv);
                });
                 logMessage(`Found ${data.files.length} context files for ${topic}.`);
            } else {
                contextFileSelector.innerHTML = '<p>No PDF files found in the context folder for this topic.</p>';
                 logMessage(`No context files found for ${topic}.`);
            }
        } catch (error) {
            logMessage(`Failed to fetch context files: ${error}`, true);
            contextFileSelector.innerHTML = '<p style="color: red;">Error loading available files. See log.</p>';
        }
    }
    function shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]]; // Swap elements
        }
    }

    function populatePdfFilters() {
        const filterTitleHTML = '<h5 class="h6">Filter Questions by Source PDF:</h5>';
        quizPdfFilterContainer.innerHTML = filterTitleHTML; // Reset but keep title

        const allSourcePdfs = new Set();
        currentTopicBank.forEach(q => {
            if (q.source_pdfs && Array.isArray(q.source_pdfs)) {
                q.source_pdfs.forEach(pdf => allSourcePdfs.add(pdf));
            }
        });

        if (allSourcePdfs.size === 0) {
            quizPdfFilterContainer.style.display = 'none';
            return;
        }

        Array.from(allSourcePdfs).sort().forEach(pdfName => {
            const checkboxId = `pdf-filter-${pdfName.replace(/[^a-zA-Z0-9_.-]/g, '-')}`;
            const formCheckDiv = document.createElement('div');
            // Use form-check-inline for horizontal layout if preferred, or just form-check for vertical
            formCheckDiv.classList.add('form-check', 'form-check-inline');

            const checkbox = document.createElement('input');
            checkbox.classList.add('form-check-input');
            checkbox.type = 'checkbox';
            checkbox.id = checkboxId;
            checkbox.value = pdfName;
            checkbox.name = 'quizPdfFilter';
            checkbox.addEventListener('change', updateFilteredQuizAndDisplay);

            const label = document.createElement('label');
            label.classList.add('form-check-label');
            label.htmlFor = checkboxId;
            label.textContent = pdfName;

            formCheckDiv.appendChild(checkbox);
            formCheckDiv.appendChild(label);
            quizPdfFilterContainer.appendChild(formCheckDiv);
        });
        const helpText = document.createElement('p');
        helpText.classList.add('text-muted', 'small', 'mt-2');
        helpText.textContent = 'Select PDFs to filter questions. If none selected, all questions for the topic are shown.';
        quizPdfFilterContainer.appendChild(helpText);
        quizPdfFilterContainer.style.display = 'block';
    }

    function getFilteredQuizBank() {
        const selectedFilterPDFs = Array.from(quizPdfFilterContainer.querySelectorAll('input[name="quizPdfFilter"]:checked'))
                                      .map(cb => cb.value);

        if (selectedFilterPDFs.length === 0) {
            return [...currentTopicBank]; // Return a copy of all questions if no filter
        }

        return currentTopicBank.filter(q => {
            if (!q.source_pdfs || q.source_pdfs.length === 0) {
                // If question has no source_pdfs, it won't match any filter if filters are selected.
                // If no filters are selected, it would have been included by the above condition.
                return false;
            }
            return q.source_pdfs.some(sourcePdf => selectedFilterPDFs.includes(sourcePdf));
        });
    }

    function updateFilteredQuizAndDisplay() {
        activeQuizBank = getFilteredQuizBank();
        currentQuestionIndex = 0; // Reset index
        if (activeQuizBank.length > 0) {
            displayQuestion(currentQuestionIndex); // displayQuestion will use activeQuizBank
            quizArea.style.display = 'block';
        } else {
            quizArea.style.display = 'block'; // Keep quiz area visible
            questionText.textContent = 'No questions match the current PDF filter.';
            optionsContainer.innerHTML = '';
            feedbackText.textContent = '';
            questionCounter.textContent = 'Question 0 of 0';
            prevQuestionBtn.disabled = true;
            nextQuestionBtn.disabled = true;
            submitAnswerBtn.disabled = true;
        }
    }

    // --- MODIFIED fetchQuestionBank ---
    async function fetchQuestionBank(topic) {
        currentTopicBank = []; // Clear previous bank
        quizArea.style.display = 'none';
        questionBankDisplay.textContent = 'Loading bank...';

        if (!topic) {
            questionBankDisplay.textContent = 'Please select a topic.';
            return;
        }
        logMessage(`Fetching question bank for topic: ${topic}`);
        try {
            const response = await fetch(`/get_bank?topic=${encodeURIComponent(topic)}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            let bank = await response.json(); // Use 'let' as we modify it

            // Display raw bank in the text area (BEFORE shuffling)
            if (bank.error) {
                 logMessage(`Error fetching bank: ${bank.error}`, true);
                 questionBankDisplay.textContent = `Error: ${bank.error}`;
            } else if (bank.length === 0) {
                questionBankDisplay.textContent = `Question bank for '${topic}' is empty.`;
            } else {
                // Display the raw, ordered bank first
                let displayStr = `--- Question Bank for: ${topic} (${bank.length} questions) ---\n\n`;
                bank.forEach((q, i) => {
                    displayStr += `${i + 1}. Question: ${q.question || 'N/A'}\n`;
                    if (q.options && typeof q.options === 'object') {
                        for (const [key, value] of Object.entries(q.options)) {
                            displayStr += `  ${key}) ${value}\n`;
                        }
                    }
                    displayStr += `   Correct Answer: ${q.correct_answer || 'N/A'}\n--------------------\n`;
                });
                questionBankDisplay.textContent = displayStr;

                // --- SHUFFLE the bank for the quiz ---
                shuffleArray(bank);
                logMessage(`Shuffled ${bank.length} questions for quiz mode.`);
                // --- End Shuffle ---

                // Prepare for Quiz Mode with the shuffled bank
                currentTopicBank = bank; // Store the SHUFFLED bank
                populatePdfFilters(); // Populate filters based on the full bank
                updateFilteredQuizAndDisplay(); // Initial display based on filters (or no filters)
            }
             logMessage(`Successfully loaded and processed bank for ${topic}.`);
        } catch (error) {
            logMessage(`Failed to fetch question bank: ${error}`, true);
            questionBankDisplay.textContent = 'Error loading question bank. See log for details.';
            quizArea.style.display = 'none';
        }
    }

    // --- Event Listeners ---

    topicSelect.addEventListener('change', () => {
        const selectedTopic = topicSelect.value;
        fetchQuestionBank(selectedTopic);
        fetchAndDisplayContextFiles(selectedTopic);
    });

    // --- Quiz Navigation Listeners ---
    prevQuestionBtn.addEventListener('click', () => {
        if (activeQuizBank.length > 0 && currentQuestionIndex > 0) {
            currentQuestionIndex--;
            displayQuestion(currentQuestionIndex);
        }
    });

    nextQuestionBtn.addEventListener('click', () => {
        if (activeQuizBank.length > 0 && currentQuestionIndex < activeQuizBank.length - 1) {
            currentQuestionIndex++;
            displayQuestion(currentQuestionIndex);
        }
    });

    submitAnswerBtn.addEventListener('click', checkAnswer);


    // --- Generate Button Listener (Using selected files) ---
    generateBtn.addEventListener('click', async () => {
        const topic = topicSelect.value;
        const numQuestions = parseInt(numQuestionsInput.value, 10);

        // Get selected filenames from checkboxes
        const selectedCheckboxes = contextFileSelector.querySelectorAll('input[name="contextFile"]:checked');
        const selectedFiles = Array.from(selectedCheckboxes).map(cb => cb.value);

        // --- Validation ---
        if (!topic) {
            logMessage('Please select a topic first.', true);
            Swal.fire({
                icon: 'error', title: 'Validation Error', text: 'Please select a topic first.',
            });
            return;
        }
        if (isNaN(numQuestions) || numQuestions <= 0) {
            logMessage('Please enter a valid positive number of questions.', true);
            Swal.fire({
                icon: 'error',
                title: 'Validation Error',
                text: 'Please enter a valid positive number of questions.',
            });
            return;
        }
        if (selectedFiles.length === 0) { // Check if any files were selected
            logMessage('Please select at least one context PDF file.', true);
            Swal.fire({
                icon: 'error',
                title: 'Validation Error',
                text: 'Please select at least one context PDF file.',
            });
            return;
        }

        logMessage(`Starting generation for topic '${topic}', count: ${numQuestions} from files: ${selectedFiles.join(', ')}...`);
        setLoading(true);

        try {
            // Send JSON data, including the list of selected filenames
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json', // Set content type to JSON
                },
                body: JSON.stringify({ // Send data as a JSON string
                    topic: topic,
                    num_questions: numQuestions,
                    selected_files: selectedFiles // Send the array of filenames
                 }),
            });

            const result = await response.json(); // Expect JSON response

            if (response.ok && result.status === 'success') {
                logMessage(`Generation successful: ${result.message}`);
                Swal.fire({
                    icon: 'success', title: 'Success!', text: result.message || 'MCQs generated successfully!',
                });
                // Refresh the bank display and quiz (which might now include new questions)
                fetchQuestionBank(topic);
            } else {
                 const errorMsg = result.message || `HTTP error ${response.status}`;
                 logMessage(`Generation failed: ${errorMsg}`, true);
                 Swal.fire({
                    icon: 'error', title: 'Generation Failed', text: errorMsg,
                 });
            }
        } catch (error) {
            logMessage(`Error during generation request: ${error}`, true);
            Swal.fire({
                icon: 'error', title: 'Request Error', text: `An error occurred during generation: ${error}`,
            });
        } finally {
            setLoading(false);
            // Optionally uncheck boxes after generation? Or leave them checked?
            // selectedCheckboxes.forEach(cb => cb.checked = false);
        }
    });

    // --- Format Examples Listener ---
    formatBtn.addEventListener('click', async () => {
        const topic = topicSelect.value;
        if (!topic) {
            logMessage('Please select a topic first.', true);
            Swal.fire({
                icon: 'error', title: 'Validation Error', text: 'Please select a topic first.',
            });
            return;
        }
        logMessage(`Starting example formatting for topic '${topic}'...`);
        setLoading(true);
        try {
            const response = await fetch('/format_examples', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic: topic }),
            });
            const result = await response.json();
             if (response.ok && result.status === 'success') {
                logMessage(`Formatting successful: ${result.message}`);
                Swal.fire({
                    icon: 'success', title: 'Success!', text: result.message || 'Examples formatted successfully!',
                });
                fetchQuestionBank(topic); // Refresh bank and quiz
            } else {
                 const errorMsg = result.message || `HTTP error ${response.status}`;
                 logMessage(`Formatting failed: ${errorMsg}`, true);
                  Swal.fire({
                    icon: 'error', title: 'Formatting Failed', text: errorMsg,
                  });
            }
        } catch (error) {
            logMessage(`Error during formatting request: ${error}`, true);
             Swal.fire({
                icon: 'error', title: 'Request Error', text: `An error occurred during formatting: ${error}`,
             });
        } finally {
            setLoading(false);
        }
    });

    // --- Add Topic Listener ---
    addTopicBtn.addEventListener('click', async () => {
        const { value: newTopicName } = await Swal.fire({
            title: 'Add New Topic',
            input: 'text',
            inputLabel: 'Enter name for the new topic:',
            inputPlaceholder: 'e.g., Python Basics',
            showCancelButton: true,
            inputValidator: (value) => {
                if (!value || value.trim() === '') {
                    return 'Topic name cannot be empty!';
                }
            }
        });

        if (newTopicName) { // User entered a value and clicked "OK"
            const topicName = newTopicName.trim();
            logMessage(`Attempting to add topic: ${topicName}`);
            setLoading(true);
             try {
                 const response = await fetch('/add_topic', {
                     method: 'POST',
                     headers: { 'Content-Type': 'application/json' },
                     body: JSON.stringify({ topic_name: topicName }),
                 });
                 const result = await response.json();
                 if (response.ok && result.status === 'success') {
                     logMessage(`Topic '${topicName}' added successfully.`);
                     Swal.fire({
                        icon: 'success', title: 'Topic Added!', text: `Topic '${topicName}' added successfully.`,
                     });
                     // Update dropdown
                     topicSelect.innerHTML = ''; // Clear existing options
                     result.topics.forEach(t => {
                         const option = document.createElement('option');
                         option.value = t;
                         option.textContent = t;
                         topicSelect.appendChild(option);
                     });
                     topicSelect.value = topicName; // Select the new topic
                     // Fetch bank and files for the newly added topic
                     fetchQuestionBank(topicName);
                     fetchAndDisplayContextFiles(topicName);
                 } else {
                     const errorMsg = result.message || `HTTP error ${response.status}`;
                     logMessage(`Failed to add topic: ${errorMsg}`, true);
                     Swal.fire({
                        icon: 'error', title: 'Failed to Add Topic', text: errorMsg,
                     });
                 }
             } catch (error) {
                 logMessage(`Error adding topic: ${error}`, true);
                 Swal.fire({
                    icon: 'error', title: 'Error', text: `An error occurred while adding topic: ${error}`,
                 });
             } finally {
                 setLoading(false);
             }
        }
    });

    clearHistoryBtn.addEventListener('click', async () => {
        const topic = topicSelect.value;
        if (!topic) {
            Swal.fire({
                icon: 'warning', title: 'No Topic Selected', text: 'Please select a topic first.',
            });
            return;
        }

        // Confirmation dialog
        const resultConfirm = await Swal.fire({
            title: 'Are you sure?',
            text: `Permanently delete all questions for the topic "${topic}"? This cannot be undone.`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Yes, delete it!'
        });

        const confirmed = resultConfirm.isConfirmed;

        if (!confirmed) {
            logMessage(`Clear history cancelled for topic '${topic}'.`);
            return;
        }

        logMessage(`Attempting to clear history for topic '${topic}'...`);
        setLoading(true);

        try {
            const response = await fetch('/clear_history', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ topic: topic }),
            });

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                logMessage(`Successfully cleared history: ${result.message}`);
                Swal.fire('Deleted!', result.message, 'success');
                // Refresh the view
                fetchQuestionBank(topic);
                // No need to refresh context files, they weren't changed
            } else {
                const errorMsg = result.message || `HTTP error ${response.status}`;
                logMessage(`Failed to clear history: ${errorMsg}`, true);
                Swal.fire({
                    icon: 'error', title: 'Failed to Clear History', text: errorMsg,
                });
            }
        } catch (error) {
            logMessage(`Error during clear history request: ${error}`, true);
            Swal.fire({
                icon: 'error', title: 'Error', text: `An error occurred while clearing history: ${error}`,
            });
        } finally {
            setLoading(false);
        }
    });

    // --- Initial Load ---
    const initialTopic = topicSelect.value;
    if (initialTopic) {
        fetchQuestionBank(initialTopic);
        fetchAndDisplayContextFiles(initialTopic);
    } else {
        logMessage("No topics found on initial load.");
        questionBankDisplay.textContent = 'No topics available. Add a topic to begin.';
        contextFileSelector.innerHTML = '<p>No topics available.</p>';
        quizPdfFilterContainer.style.display = 'none';
        quizArea.style.display = 'none';
    }
    logMessage("Application initialized.");

});
