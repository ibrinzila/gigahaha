const chatMessages = document.querySelector('.chat-messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const recordButton = document.getElementById('record-button');
const quickReplyButtons = document.querySelectorAll('.quick-reply');
let mediaRecorder;
let audioChunks = [];

function addMessage(message, isUser = false) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');
    messageElement.classList.add(isUser ? 'user-message' : 'bot-message');

    const senderElement = document.createElement('div');
    senderElement.classList.add('message-sender');
    senderElement.textContent = isUser ? 'You' : 'Bot';

    const contentElement = document.createElement('div');
    contentElement.classList.add('message-content');

    // Parse and format the message content
    const formattedContent = formatMessageContent(message);
    contentElement.innerHTML = formattedContent;

    messageElement.appendChild(senderElement);
    messageElement.appendChild(contentElement);

    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMessageContent(message) {
    // Split the message into lines
    const lines = message.split('\n');
    let formattedContent = '';
    let listCounter = 0;
    let inList = false;

    lines.forEach((line, index) => {
        line = line.trim();
        if (line.startsWith('#')) {
            // Handle numbered points
            listCounter++;
            formattedContent += `<p class="numbered-point"><strong>${listCounter}.</strong> ${line.substring(1).trim()}</p>`;
            inList = true;
        } else if (line.startsWith('*') || line.startsWith('-')) {
            // Handle bullet points
            formattedContent += `<p class="bullet-point">${line.substring(1).trim()}</p>`;
            inList = true;
        } else if (line === '') {
            // Handle empty lines
            if (inList) {
                listCounter = 0;
                inList = false;
            }
            formattedContent += '<br>';
        } else {
            // Regular text
            if (inList) {
                listCounter = 0;
                inList = false;
                formattedContent += '<br>';
            }
            formattedContent += `<p>${line}</p>`;
        }
    });

    return formattedContent;
}

function sendMessage(message) {
    addMessage(message, true);
    userInput.value = '';

    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message }),
    })
    .then(response => response.json())
    .then(data => {
        addMessage(data.response);
        if (data.escalated) {
            console.log("Conversația a fost escaladată către un reprezentant al serviciului clienți.");
            // Aici puteți adăuga logică suplimentară pentru gestionarea escaladării în interfața utilizatorului
        }
    })
    .catch(error => {
        console.error('Error:', error);
        addMessage('Sorry, there was an error processing your request.');
    });
}

sendButton.addEventListener('click', () => sendMessage(userInput.value.trim()));
userInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage(userInput.value.trim());
    }
});

quickReplyButtons.forEach(button => {
    button.addEventListener('click', () => {
        const message = button.textContent;
        sendMessage(message);
    });
});

recordButton.addEventListener('click', toggleRecording);

function toggleRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        recordButton.textContent = 'Start Recording';
    } else {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.start();
                recordButton.textContent = 'Stop Recording';

                mediaRecorder.addEventListener('dataavailable', event => {
                    audioChunks.push(event.data);
                });

                mediaRecorder.addEventListener('stop', () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    audioChunks = [];
                    sendAudioToServer(audioBlob);
                });
            })
            .catch(error => {
                console.error('Error accessing microphone:', error);
                addMessage('Error accessing microphone. Please make sure you have given permission to use the microphone.');
            });
    }
}

function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    fetch('/api/voice-to-text', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.text) {
            userInput.value = data.text;
            sendMessage(data.text);
        } else if (data.error) {
            addMessage(`Error: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        addMessage('Sorry, there was an error processing your audio.');
    });
}

function showFeedbackForm() {
    const feedbackForm = document.createElement('div');
    feedbackForm.innerHTML = `
        <h3>How was your experience?</h3>
        <select id="rating">
            <option value="5">Excellent</option>
            <option value="4">Good</option>
            <option value="3">Average</option>
            <option value="2">Poor</option>
            <option value="1">Very Poor</option>
        </select>
        <textarea id="comment" placeholder="Any additional comments?"></textarea>
        <button onclick="submitFeedback()">Submit Feedback</button>
    `;
    chatMessages.appendChild(feedbackForm);
}

function submitFeedback() {
    const rating = document.getElementById('rating').value;
    const comment = document.getElementById('comment').value;

    fetch('/api/feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ rating: rating, comment: comment }),
    })
    .then(response => response.json())
    .then(data => {
        addMessage('Thank you for your feedback!');
        document.querySelector('.chat-messages > div:last-child').remove();
    })
    .catch(error => {
        console.error('Error:', error);
        addMessage('Sorry, there was an error submitting your feedback.');
    });
}