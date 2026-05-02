import { useState, useRef, useEffect } from 'react'
import './ChatInput.css'

export default function ChatInput({ onSendMessage, isProcessing }) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef(null)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() && !isProcessing) {
      onSendMessage(message.trim())
      setMessage('')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`
    }
  }, [message])

  return (
    <div className="chat-input-container">
      <div className="suggested-prompts">
        {[
          "Tell me about your AI experience",
          "AI & Data career transition tips?",
          "Recommend an AI study path"
        ].map((promptText, index) => (
          <button 
            key={index} 
            className="prompt-pill"
            onClick={() => setMessage(promptText)}
            type="button"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            {promptText}
          </button>
        ))}
      </div>

      <form className="chat-input-form glass" onSubmit={handleSubmit}>
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          placeholder="Ask me anything about my career and experience..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isProcessing}
          rows={1}
        />
        <button
          type="submit"
          className={`send-button ${message.trim() && !isProcessing ? 'active' : ''}`}
          disabled={!message.trim() || isProcessing}
          aria-label="Send message"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </form>
    </div>
  )
}
