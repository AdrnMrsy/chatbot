const chatBox = document.getElementById("chat-box");
const userInputBox = document.getElementById("userInput");
let currentAction = null; // Keeps track of the current action (summarize, availability, suggest)

/**
 * Adds a message to the chat box.
 * @param {string} content - The message content.
 * @param {string} role - The role of the sender ('user' or 'bot').
 */
function addMessageToChat(content, role) {
    
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", `${role}-message`);

    const messageContent = document.createElement("div");
    messageContent.classList.add("message-content");
    messageContent.innerHTML = content;
    messageDiv.appendChild(messageContent);
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the bottom
}

/**
 * Sends a request to the server and handles the response.
 * @param {string} url - The endpoint URL.
 * @param {string} method - The HTTP method (GET, POST, etc.).
 * @param {object|null} body - The request body, if any.
 */
async function sendRequest(url, method, body = null) {
    const typingMessage = document.createElement("div");
    typingMessage.classList.add("message", "bot-message");
    typingMessage.innerHTML = `<div class="message-content">Typing...</div>`;
    chatBox.appendChild(typingMessage);
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the bottom

    userInputBox.disabled = true; // Disable input during request

    try {
        const options = {
            method,
            headers: { "Content-Type": "application/json" },
        };
        if (body) options.body = JSON.stringify(body);

        const response = await fetch(url, options);
        const data = await response.json();
        typingMessage.remove();

        if (response.ok) {
            const formattedAnswer = data.answer
                ? data.answer
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\n/g, "<br>")
                : "No response received.";
            addMessageToChat(formattedAnswer, "bot");
        } else {
            addMessageToChat(data.error || `Error ${response.status}: ${response.statusText}`, "bot");
        }
    } catch (error) {
        console.error("Error:", error);
        typingMessage.remove();
        addMessageToChat("An error occurred. Please try again.", "bot");
    } finally {
        userInputBox.disabled = false; // Re-enable input
    }
}


/**
 * Handles user input and performs actions based on the current context.
 */
function handleUserInput() {
    const userInput = userInputBox.value.trim();
    if (!userInput) return;
    if (userInput.length > 500) { // Example input length limit
        addMessageToChat("Your input is too long. Please shorten it.", "bot");
        return;
    }

    addMessageToChat(userInput, "user");
    userInputBox.value = ""; // Clear the input box
    sendRequest("/ask_question", "POST", { question: userInput });
}

