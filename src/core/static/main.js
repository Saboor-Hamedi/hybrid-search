// --- JAVASCRIPT CORRECTION START ---

const searchForm = document.getElementById("main-search-form");
const spinner = document.getElementById("loading");
// CRITICAL: Select the actual radio input elements
const modeRadios = document.querySelectorAll(
  '.mode-selector input[type="radio"]',
);
const modeHiddenInput = document.getElementById("selected-mode-input");

// --- 1. Mode Selection Handler (Updates Hidden Field, DOES NOT SUBMIT) ---
modeRadios.forEach((radio) => {
  // 1a. Listen for the 'change' event on the radio button itself
  radio.addEventListener("change", function () {
    // Find the data-mode attribute on the parent container
    const selectedMode =
      this.closest(".mode-selector").getAttribute("data-mode");

    // CRITICAL: Update the hidden 'mode' field in the main search form
    modeHiddenInput.value = selectedMode;

    // Ensure the correct radio button in the UI stays checked
    // (This is mostly handled by the browser if the NAME attribute is correct,
    // but we ensure the hidden input tracks the value.)
  });
});

// --- 2. Form Submission Handler (Triggers on Search Button or Pagination) ---
function handleFormSubmission(form) {
  form.addEventListener("submit", function () {
    // Show global spinner
    spinner.style.display = "block";

    // Add loading state to search button (only on main search form)
    if (form.id === "main-search-form") {
      const submitButton = form.querySelector('button[type="submit"]');
      if (submitButton) {
        submitButton.innerHTML =
          '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Searching...';
        submitButton.disabled = true;
      }
    }
  });
}

// Apply handler to main form
handleFormSubmission(searchForm);

// Apply handler to all pagination forms (they submit the same way)
document.querySelectorAll(".pagination-form").forEach((form) => {
  handleFormSubmission(form);
});

// Final check to ensure the initial radio state matches the Jinja value
document.addEventListener("DOMContentLoaded", function () {
  const initialMode = "{{ mode }}";

  // Find the radio button corresponding to the mode passed from Flask
  const initialRadio = document.querySelector(
    `.mode-selector[data-mode="${initialMode}"] input[type="radio"]`,
  );

  if (initialRadio) {
    // Set the checked state on the correct radio button
    initialRadio.checked = true;
    // Ensure the hidden form value is also set (it should be, but this guarantees it)
    modeHiddenInput.value = initialMode;
  }
});

// --- JAVASCRIPT CORRECTION END ---
