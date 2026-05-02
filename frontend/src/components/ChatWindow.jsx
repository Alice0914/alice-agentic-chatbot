import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'
import './ChatWindow.css'

export default function ChatWindow({ messages, isProcessing }) {
  const containerRef = useRef(null)
  
  // Auto-scroll to bottom
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [messages, isProcessing])

  return (
    <div className="chat-window-container">
      <div className="chat-messages" ref={containerRef}>
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
        {isProcessing && <MessageBubble key="typing" isTyping={true} />}
      </div>
    </div>
  )
}
