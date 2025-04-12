async function sendMessage() {
  const input = document.getElementById("userInput");
  const chatBox = document.getElementById("chat-box");
  const message = input.value.trim();
  if (!message) return;

  chatBox.innerHTML += `<p><strong>You:</strong> ${message}</p>`;
  input.value = "";

  const response = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, user_id: "web_user" })
  });

  const data = await response.json();
  chatBox.innerHTML += `<p><strong>PATE:</strong> ${data.reply}</p>`;
  chatBox.scrollTop = chatBox.scrollHeight;
}
