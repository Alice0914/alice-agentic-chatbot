import { useState, useEffect } from 'react'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import MobileProfile from './components/MobileProfile'
import ChatWindow from './components/ChatWindow'
import ChatInput from './components/ChatInput'
import './App.css'

const initialMessage = {
  role: 'assistant',
  content: "Hello! I'm AliceBot, your AI assistant on behalf of Alice. I'm here to help with questions about her career in AI and data science, study methods, how she prepared for a career transition, job-change advice, or the latest AI trends. Feel free to ask me anything at any time!"
}

function App() {
  const [messages, setMessages] = useState([initialMessage])
  const [isProcessing, setIsProcessing] = useState(false)
  const [visitCount, setVisitCount] = useState(null)

  useEffect(() => {
    const API_BASE = import.meta.env.VITE_API_URL || ''
    fetch(`${API_BASE}/api/visit`, { method: 'POST' })
      .then(r => r.json())
      .then(data => setVisitCount(data.count))
      .catch(() => {})
  }, [])

  const handleSendMessage = async (userText) => {
    // Optimistically add user message
    const newMessage = { role: 'user', content: userText }
    const updatedMessages = [...messages, newMessage]
    setMessages(updatedMessages)
    setIsProcessing(true)

    try {
      const API_BASE = import.meta.env.VITE_API_URL || ''
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userText,
          // Exclude the last message since we're passing it as `message`
          history: messages.map(m => ({ role: m.role, content: m.content }))
        }),
      })

      if (!response.ok) {
        throw new Error('Network response was not ok')
      }

      const data = await response.json()
      
      setMessages([...updatedMessages, { role: 'assistant', content: data.response }])
    } catch (error) {
      console.error('Error fetching chat response:', error)
      setMessages([
        ...updatedMessages, 
        { 
          role: 'assistant', 
          content: 'Sorry, I am experiencing some technical difficulties. Please ensure the backend server is running.' 
        }
      ])
    } finally {
      setIsProcessing(false)
    }
  }

  const handleClearChat = () => {
    setMessages([initialMessage])
  }

  return (
    <div className="app-container">
      <Sidebar onClearChat={handleClearChat} />
      
      <main className="main-content">
        <Header visitCount={visitCount} />
        <MobileProfile onClearChat={handleClearChat} />

        <div className="chat-area">
          <ChatWindow messages={messages} isProcessing={isProcessing} />
          <ChatInput onSendMessage={handleSendMessage} isProcessing={isProcessing} />
        </div>
      </main>
    </div>
  )
}

export default App
