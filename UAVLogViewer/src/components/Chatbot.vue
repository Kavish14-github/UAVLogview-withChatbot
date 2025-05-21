<template>
  <div class="chatbot">
    <div class="chat-header">Flight Chat Assistant</div>

    <div class="chat-messages">
      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
        <span>{{ msg.text }}</span>
      </div>
      <div v-if="isLoading" class="message bot loading">
        <span>Processing...</span>
      </div>
    </div>

    <div class="file-upload" v-if="!sessionId && !isLoading">
      <input type="file" ref="fileInput" @change="uploadFile" accept=".bin" />
    </div>

    <div class="chat-input" v-if="sessionId">
      <input v-model="userInput" @keyup.enter="sendMessage" placeholder="Ask about the flight..." />
      <button @click="sendMessage">Send</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
    name: 'Chatbot',
    data () {
        return {
            sessionId: null,
            userInput: '',
            messages: [{ role: 'bot', text: 'Hi! Please upload a .BIN file to begin analysis.' }],
            isLoading: false
        }
    },
    methods: {
        async uploadFile (e) {
            const file = e.target.files[0]
            if (!file) return

            this.isLoading = true

            const formData = new FormData()
            formData.append('file', file)

            try {
                const response = await axios.post('http://localhost:8000/upload', formData)
                this.sessionId = response.data.session_id
                this.messages.push({ role: 'bot', text: 'File uploaded successfully! Ask me anything about the flight.' })
            } catch (err) {
                this.messages.push({ role: 'bot', text: 'Failed to upload file. Please try again.' })
            } finally {
                this.isLoading = false
            }
        },
        async sendMessage () {
            if (!this.userInput.trim()) return

            const userMsg = this.userInput.trim()
            this.messages.push({ role: 'user', text: userMsg })
            this.userInput = ''
            this.isLoading = true

            try {
                const response = await axios.post(
                    'http://localhost:8000/chat',
                    new URLSearchParams({
                        /* eslint-disable-next-line camelcase */
                        session_id: this.sessionId,
                        query: userMsg
                    }),
                    {
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded'
                        }
                    }
                )

                this.messages.push({ role: 'bot', text: response.data.response || 'No response from server.' })
            } catch (error) {
                this.messages.push({ role: 'bot', text: 'Error communicating with server.' })
            } finally {
                this.isLoading = false
            }
        }
    }
}
</script>

<style scoped>
.chatbot {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 350px;
  background-color: #161b28;
  color: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.4);
  font-family: sans-serif;
  display: flex;
  flex-direction: column;
  z-index: 2000;
}

.chat-header {
  padding: 12px 16px;
  background-color: #1f2537;
  font-weight: bold;
  border-bottom: 1px solid #2c344d;
}

.chat-messages {
  max-height: 300px;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message {
  padding: 8px 12px;
  border-radius: 8px;
  max-width: 90%;
  word-wrap: break-word;
}

.message.user {
  background-color: #3e445c;
  align-self: flex-end;
}

.message.bot {
  background-color: #2b3146;
  align-self: flex-start;
}

.message.loading {
  font-style: italic;
  opacity: 0.7;
}

.chat-input {
  display: flex;
  border-top: 1px solid #2c344d;
  padding: 8px;
  gap: 4px;
}

.chat-input input {
  flex: 1;
  padding: 6px 10px;
  border: none;
  border-radius: 6px;
  outline: none;
}

.chat-input button {
  background-color: white;
  color: #161b28;
  border: none;
  border-radius: 6px;
  padding: 6px 10px;
  cursor: pointer;
}

.chat-input button:hover {
  background-color: #e6e6e6;
}

.file-upload {
  padding: 10px;
  text-align: center;
}

.file-upload input[type='file'] {
  color: white;
  background-color: #2b3146;
  border: 1px solid #444;
  padding: 6px;
  border-radius: 6px;
  cursor: pointer;
  width: 90%;
}
.chat-container {
  display: flex;
  flex-direction: column;
  height: 400px;
  max-height: 400px;
  overflow-y: auto;
  background-color: #161b28;
  padding: 10px;
  border-radius: 10px;
  color: white;
}

.message {
  margin: 8px 0;
  max-width: 90%;
  word-break: break-word;
  white-space: pre-wrap;
}

.bot {
  background-color: #22283a;
  color: #fff;
  align-self: flex-start;
  padding: 10px 14px;
  border-radius: 10px;
}

.user {
  background-color: #ffffff;
  color: #000000;
  align-self: flex-end;
  padding: 10px 14px;
  border-radius: 10px;
}

input[type='file'] {
  color: white;
  margin-top: 10px;
}

input[type='text'] {
  padding: 10px;
  border-radius: 6px;
  border: none;
  width: 80%;
  margin-top: 10px;
}

button {
  background-color: #64e9ff;
  color: #000;
  padding: 10px 15px;
  margin-left: 10px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.loader {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #64e9ff;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
  display: inline-block;
  margin-left: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
