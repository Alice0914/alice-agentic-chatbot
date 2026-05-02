import ReactMarkdown from 'react-markdown'
import './MessageBubble.css'

export default function MessageBubble({ message, isTyping }) {
  if (isTyping) {
    return (
      <div className="message-wrapper assistant">
        <div className="message-avatar">🤖</div>
        <div className="message-content typing-indicator">
          <span className="dot"></span>
          <span className="dot"></span>
          <span className="dot"></span>
        </div>
      </div>
    )
  }

  const isUser = message?.role === 'user'

  return (
    <div className={`message-wrapper ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && <div className="message-avatar">🤖</div>}
      <div className={`message-content ${isUser ? 'user-content' : 'assistant-content'}`}>
        {isUser ? (
          message.content
        ) : (
          <div className="markdown-body">
            <ReactMarkdown>
              {message.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
