import { useState } from 'react'
import './Sidebar.css'

export default function Sidebar({ onClearChat }) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`} id="sidebar">
      <button
        className="sidebar-toggle"
        onClick={() => setIsCollapsed(!isCollapsed)}
        aria-label="Toggle sidebar"
        id="sidebar-toggle-btn"
      >
        {isCollapsed ? '◀' : '▶'}
      </button>

      <div className="sidebar-content">
        {/* About Section */}
        <section className="sidebar-section">
          <h3 className="section-title">
            <span className="section-icon">💼</span>
            About Alice
          </h3>
          <div className="about-card glass">
            <div className="expertise-list">
              <div className="expertise-item">
                <span className="expertise-dot"></span>
                Agentic AI Data Science
              </div>
              <div className="expertise-item">
                <span className="expertise-dot"></span>
                ML/DL Data Science
              </div>
              <div className="expertise-item">
                <span className="expertise-dot"></span>
                Analytics Engineer
              </div>
              <div className="expertise-item">
                <span className="expertise-dot"></span>
                Data Analyst
              </div>
              <div className="expertise-item">
                <span className="expertise-dot"></span>
                Career Consultant
              </div>
              <div className="expertise-item">
                <span className="expertise-dot"></span>
                AI & Data Technical Consultant
              </div>
            </div>
          </div>
        </section>

        {/* Schedule Section */}
        <section className="sidebar-section">
          <h3 className="section-title">
            <span className="section-icon">📅</span>
            Schedule a Meeting
          </h3>
          <a
            href="https://calendly.com/alicek0914/career-coffee-chat"
            target="_blank"
            rel="noopener noreferrer"
            className="sidebar-btn btn-gradient"
            id="calendly-link"
          >
            📅 Book 15-30 min Meeting
          </a>
        </section>

        {/* LinkedIn Section */}
        <section className="sidebar-section">
          <h3 className="section-title">
            <span className="section-icon">✉️</span>
            Direct Contact
          </h3>
          <a
            href="https://www.linkedin.com/in/alice-k-31049b165/"
            target="_blank"
            rel="noopener noreferrer"
            className="sidebar-btn btn-linkedin"
            id="linkedin-link"
          >
            💼 LinkedIn Profile
          </a>
        </section>



        {/* Clear Chat */}
        <section className="sidebar-section sidebar-bottom">
          <button
            className="sidebar-btn btn-clear"
            onClick={onClearChat}
            id="clear-chat-btn"
          >
            🗑️ Clear Chat History
          </button>
        </section>
      </div>
    </aside>
  )
}
