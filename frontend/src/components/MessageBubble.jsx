import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './MessageBubble.css'

const BOOK_NAME = 'AI Engineering Book 2025 (490p)'

function normalizeSources(text) {
  if (!text) return text
  return text.replace(
    /\[Source:\s*AI[_\s]?Engineering[_\s]?2025[_\s]?490[pP](?:\.pdf)?\s*(,\s*(?:Page\s+-?\d+|Front matter))?\s*\]/gi,
    (_, suffix) => {
      const tail = suffix ? suffix.trim().replace(/^,\s*/, ', ') : ''
      return `(${BOOK_NAME}${tail})`
    }
  )
}

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
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                a: ({ node, ...props }) => (
                  <a {...props} target="_blank" rel="noopener noreferrer" />
                ),
              }}
            >
              {normalizeSources(message.content)}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
