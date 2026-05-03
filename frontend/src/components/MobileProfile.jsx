import { HiSparkles, HiChip, HiChartBar, HiTable, HiUserGroup, HiLightBulb, HiCode, HiTemplate } from 'react-icons/hi'
import './MobileProfile.css'

const expertise = [
  { icon: HiCode,      label: 'AI Engineer' },
  { icon: HiTemplate,  label: 'Agentic AI Systems Architect' },
  { icon: HiSparkles,  label: 'Agentic AI Data Science' },
  { icon: HiChip,      label: 'ML/DL Data Science' },
  { icon: HiChartBar,  label: 'Analytics Engineer' },
  { icon: HiTable,     label: 'Data Analyst' },
  { icon: HiUserGroup, label: 'Career Consultant' },
  { icon: HiLightBulb, label: 'AI & Data Technical Consultant' },
]

export default function MobileProfile({ onClearChat }) {
  return (
    <div className="mobile-profile">
      <div className="mobile-left">
        <img
          src="/alice-avatar.png.jpg"
          alt="Alice"
          className="mobile-avatar"
        />
        <div className="mobile-actions">
          <a
            href="https://www.linkedin.com/in/alice-k-31049b165/"
            target="_blank"
            rel="noopener noreferrer"
            className="mobile-btn mobile-btn-linkedin"
          >
            💼 LinkedIn
          </a>
          <button
            className="mobile-btn mobile-btn-clear"
            onClick={onClearChat}
          >
            🗑️ Clear Chat
          </button>
        </div>
      </div>

      <div className="mobile-right">
        <span className="mobile-section-title">About Alice</span>
        <ul className="mobile-expertise-list">
          {expertise.map(({ icon: Icon, label }) => (
            <li key={label}>
              <Icon className="mobile-expertise-icon" />
              {label}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
