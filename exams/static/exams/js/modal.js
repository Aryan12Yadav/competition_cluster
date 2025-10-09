// FILE: exams/static/exams/js/modal.js (Final Functioning Version)

document.addEventListener('DOMContentLoaded', () => {

    const modalOverlay = document.getElementById('auth-modal-overlay');
    
    // Stop the script if the modal HTML element is not present (i.e., user is logged in).
    if (!modalOverlay) {
        return;
    }

    // Get all elements by their specific IDs
    const closeModalBtn = document.getElementById('close-modal-btn');
    const loginTabBtn = document.getElementById('login-tab-btn');
    const signupTabBtn = document.getElementById('signup-tab-btn');
    const loginForm = document.getElementById('login-form-container');
    const signupForm = document.getElementById('signup-form-container');

    // --- FUNCTION TO OPEN THE MODAL (NEW) ---
    function openModal() {
        // Sets the modal container to visible (display: flex)
        modalOverlay.style.display = 'flex';
        // Prevents the background page from scrolling
        document.body.style.overflow = 'hidden'; 
    }
    
    // --- FUNCTION TO SWITCH TABS ---
    function switchTab(tabToShow) {
        if (tabToShow === 'login') {
            loginForm.style.display = 'block';
            signupForm.style.display = 'none';
            loginTabBtn.classList.add('active');
            signupTabBtn.classList.remove('active');
        } else {
            signupForm.style.display = 'block';
            loginForm.style.display = 'none';
            signupTabBtn.classList.add('active');
            loginTabBtn.classList.remove('active');
        }
    }

    // --- FUNCTION TO CLOSE THE MODAL (UPDATED) ---
    function closeModal() {
        modalOverlay.style.display = 'none';
        // Restore background scrolling (FIX)
        document.body.style.overflow = 'auto'; 
    }
    
    // -------------------------------------------------------------------
    // CORE FIX: OPEN THE MODAL IMMEDIATELY ON PAGE LOAD 
    // -------------------------------------------------------------------
    openModal();

    // --- EVENT LISTENERS (Making the buttons clickable) ---
    
    // Tab switching event listeners
    loginTabBtn.addEventListener('click', () => switchTab('login'));
    signupTabBtn.addEventListener('click', () => switchTab('signup'));

    // Close button event listener (Resolves X button issue)
    closeModalBtn.addEventListener('click', closeModal);

    // Close when clicking outside the content
    modalOverlay.addEventListener('click', (event) => {
        if (event.target === modalOverlay) {
            closeModal();
        }
    });
});