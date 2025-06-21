document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".auth-form");
    const password = document.getElementById("password");
    const confirmPassword = document.getElementById("confirm_password");

    form.addEventListener("submit", (event) => {
        if (password.value !== confirmPassword.value) {
            event.preventDefault();
            alert("Passwords do not match. Please try again.");
        }
        if (password.value.length < 8) {
            event.preventDefault();
            alert("Password must be at least 8 characters long.");
        }
    });
});