document.addEventListener("DOMContentLoaded", () => {
    const flashMessages = []; // Replace with actual data or ensure server-side rendering outputs valid JSON
    const flashContainer = document.getElementById("flash-message-container");

    flashMessages.forEach(([category, message]) => {
        // Create a flash message element
        const flashMessage = document.createElement("div");
        flashMessage.className = `flash-message flash-${category}`;
        flashMessage.textContent = message;

        // Append the flash message to the container
        flashContainer.appendChild(flashMessage);

        // Automatically remove the flash message after 5 seconds
        setTimeout(() => {
            flashMessage.remove();
        }, 5000);
    });
});