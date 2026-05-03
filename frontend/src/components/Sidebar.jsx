import { useState } from 'react'
import { HiSparkles, HiChip, HiChartBar, HiTable, HiUserGroup, HiLightBulb, HiCode, HiTemplate } from 'react-icons/hi'
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
        {/* Profile Image */}
        <section className="sidebar-section sidebar-profile">
          <img
            src="/alice-avatar.png.jpg"
            alt="Alice"
            className="profile-avatar"
          />
        </section>

        {/* About Section */}
        <section className="sidebar-section">
          <h3 className="section-title">
            <span className="section-icon">💼</span>
            About Alice
          </h3>
          <div className="about-card glass">
            <div className="expertise-list">
              <div className="expertise-item">
                <HiCode className="expertise-icon" />
                AI Engineer
              </div>
              <div className="expertise-item">
                <HiTemplate className="expertise-icon" />
                Agentic AI Systems Architect
              </div>
              <div className="expertise-item">
                <HiSparkles className="expertise-icon" />
                Agentic AI Data Science
              </div>
              <div className="expertise-item">
                <HiChip className="expertise-icon" />
                ML/DL Data Science
              </div>
              <div className="expertise-item">
                <HiChartBar className="expertise-icon" />
                Analytics Engineer
              </div>
              <div className="expertise-item">
                <HiTable className="expertise-icon" />
                Data Analyst
              </div>
              <div className="expertise-item">
                <HiUserGroup className="expertise-icon" />
                Career Consultant
              </div>
              <div className="expertise-item">
                <HiLightBulb className="expertise-icon" />
                AI & Data Technical Consultant
              </div>
            </div>
          </div>
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
