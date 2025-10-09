// FILE: exams/static/exams/js/live_test.js (Final Functioning Version)

document.addEventListener('DOMContentLoaded', () => {
    // --- 1. DOM Elements & Initial Configuration ---
    const allQuestions = document.querySelectorAll('.question-container');
    const totalQuestions = allQuestions.length;
    
    // Check if any questions were rendered
    if (totalQuestions === 0) {
        console.error("ERROR: No questions were found on this page.");
        return; 
    }

    let currentQuestionIndex = 0;
    let questionStartTime = null; 
    let testState = {}; 
    let timerInterval; // Accessible globally for starting/stopping the timer

    // --- 2. Initialization ---
    function initializeTest() {
        const paletteGrid = document.querySelector('.question-palette-grid');

        allQuestions.forEach((q, index) => {
            const qId = q.dataset.id;
            // Provide code with comments: Initialize state for each question with default values
            testState[qId] = { status: 'unanswered', selectedOption: null, timeSpent: 0 };
            const paletteItem = document.createElement('div');
            paletteItem.classList.add('palette-item', 'unanswered');
            paletteItem.textContent = index + 1;
            paletteItem.dataset.index = index;
            paletteItem.addEventListener('click', () => navigateToQuestion(index));
            paletteGrid.appendChild(paletteItem);

            // Attach event listener to options to track answers instantly
            q.querySelectorAll('input[type="radio"]').forEach(option => {
                option.addEventListener('change', () => updateQuestionStatus(index));
            });
        });

        updateNavigationButtons();
        showQuestion(currentQuestionIndex); 
        startTimer(); // Call to start the timer countdown
    }

    // --- 3. Time Tracking & Navigation ---
    function calculateTimeSpent() {
        if (questionStartTime) {
            const qId = allQuestions[currentQuestionIndex].dataset.id;
            // Provide code with comments: Calculate time elapsed in seconds and add to total timeSpent
            const timeElapsed = Math.round((new Date() - questionStartTime) / 1000);
            testState[qId].timeSpent += timeElapsed;
        }
    }

    function showQuestion(index) {
        if (index < 0 || index >= totalQuestions) return;
        // Hide all questions and show the current one
        allQuestions.forEach(q => q.style.display = 'none');
        allQuestions[index].style.display = 'block';
        document.getElementById('current-q-number').textContent = index + 1;
        currentQuestionIndex = index;
        // Provide code with comments: Reset question start time for accurate tracking
        questionStartTime = new Date();
        updateNavigationButtons();
    }

    function navigateToQuestion(index) {
        if (index === currentQuestionIndex) return;
        // Provide code with comments: Save state before leaving the current question
        calculateTimeSpent();
        updateQuestionStatus(currentQuestionIndex); 
        showQuestion(index);
    }

    // --- 4. Submission Logic (Final Direct Redirection) ---
    function submitTest() {
        // Provide code with comments: Final save for the last viewed question state and time
        calculateTimeSpent();
        updateQuestionStatus(currentQuestionIndex);
        
        // Safety check before processing submission
        if (!confirm("Click OK to finalize your submission.")) {
            return;
        }

        const mockTestId = document.querySelector('.test-header').dataset.testId;
        
        // Provide code with comments: Retrieve token directly from the hidden input field (CRITICAL CSRF FIX)
        const csrfTokenInput = document.getElementById('csrf-token-input');
        const csrfToken = csrfTokenInput ? csrfTokenInput.value : '';

        // Prepare the JSON payload for the backend
        const answers = Object.keys(testState).map(qId => ({
            question_id: qId,
            selected_option_id: testState[qId].selectedOption,
            time_spent: testState[qId].timeSpent
        }));
        
        const url = `/test/submit/${mockTestId}/`;

        // Provide code with comments: Send data via Fetch (should now resolve submission failure)
        fetch(url, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json', 
                'X-CSRFToken': csrfToken // Send the CSRF token securely
            },
            body: JSON.stringify({ answers: answers })
        })
        .then(response => {
            if (!response.ok) {
                // If the server returns a 500 or 403, this triggers the catch block
                throw new Error(`Server responded with status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Check if the backend processing status is 'success'
            if (data.status === 'success' && data.result_id) {
                // Provide code with comments: SUCCESS: Stop the timer and redirect immediately
                if (timerInterval) { clearInterval(timerInterval); }
                
                const resultId = data.result_id;
                
                // FINAL REDIRECT: Go straight to the results page
                window.location.href = `/test/results/${resultId}/`; 
                
            } else {
                // Provide code with comments: Fallback for processing failure (status 200 but data.status != success)
                alert("An error occurred during submission. Please check the console for details.");
                console.error("Submission Error from Server:", data.message);
            }
        })
        .catch(error => {
            // Provide code with comments: Catches network/server errors (the source of the persistent alert)
            console.error('Network Fetch Error:', error);
            alert("A network error occurred. Please check your connection and the console for details.");
        });
    }

    // --- Helper functions and Event Listeners ---
    function updateNavigationButtons() {
        document.getElementById('prev-btn').disabled = currentQuestionIndex === 0;
        document.getElementById('next-btn').textContent = currentQuestionIndex === totalQuestions - 1 ? 'Finish & Submit' : 'Save & Next \u00BB';
    }

    function updateQuestionStatus(index) {
        if (!allQuestions[index]) return;
        const qId = allQuestions[index].dataset.id;
        const selectedOption = allQuestions[index].querySelector('input[type="radio"]:checked');
        const paletteItem = document.querySelector(`.palette-item[data-index="${index}"]`);
        
        testState[qId].selectedOption = selectedOption ? selectedOption.value : null;

        let newStatus = 'unanswered';
        if (testState[qId].status === 'marked') {
            newStatus = 'marked';
        }
        if (selectedOption) {
            newStatus = 'answered';
        }
        
        testState[qId].status = newStatus;

        if (paletteItem) {
            paletteItem.className = 'palette-item ' + newStatus;
        }
    }

    function markForReview() {
        const qId = allQuestions[currentQuestionIndex].dataset.id;
        const paletteItem = document.querySelector(`.palette-item[data-index="${currentQuestionIndex}"]`);

        // Provide code with comments: Toggle 'marked' status
        if (testState[qId].status === 'marked') {
            const selectedOption = allQuestions[currentQuestionIndex].querySelector('input[type="radio"]:checked');
            testState[qId].status = selectedOption ? 'answered' : 'unanswered';
        } else {
            testState[qId].status = 'marked';
        }
        
        paletteItem.className = 'palette-item ' + testState[qId].status;
    }

    function startTimer() {
        const headerElement = document.querySelector('.test-header');
        
        // Provide code with comments: CRITICAL FIX: Ensure safe parsing of duration data attribute
        const durationMinutes = parseInt(headerElement.dataset.duration, 10);
        let timeInSeconds = (isNaN(durationMinutes) ? 0 : durationMinutes) * 60;
        const timerDisplay = document.getElementById('timer-display');
        
        // Initial timer display before interval starts
        const minutes = String(Math.floor(timeInSeconds / 60)).padStart(2, '0');
        const seconds = String(timeInSeconds % 60).padStart(2, '0');
        timerDisplay.textContent = `${minutes}:${seconds}`;

        // Stop previous interval just in case
        if (timerInterval) { clearInterval(timerInterval); }
        
        timerInterval = setInterval(() => { 
            if (timeInSeconds <= 0) {
                clearInterval(timerInterval);
                timerDisplay.textContent = "00:00";
                alert("Time is up! Submitting your test...");
                submitTest();
                return;
            }
            timeInSeconds--;
            const minutes = String(Math.floor(timeInSeconds / 60)).padStart(2, '0');
            const seconds = String(timeInSeconds % 60).padStart(2, '0');
            timerDisplay.textContent = `${minutes}:${seconds}`;
        }, 1000);
    }
    
    // --- Attaching Event Listeners ---
    
    // Provide code with comments: Safety check for "Save & Next" button (Fixes non-working button issue)
    const nextBtn = document.getElementById('next-btn');

    if (nextBtn) { 
        nextBtn.addEventListener('click', () => {
            if (currentQuestionIndex < totalQuestions - 1) {
                navigateToQuestion(currentQuestionIndex + 1);
            } else {
                submitTest(); // Submit if on the last question
            }
        });
    }

    document.getElementById('prev-btn').addEventListener('click', () => { navigateToQuestion(currentQuestionIndex - 1); });
    document.getElementById('mark-review-btn').addEventListener('click', markForReview);
    document.getElementById('submit-test-btn').addEventListener('click', submitTest);

    // --- Start the Test ---
    initializeTest();
});