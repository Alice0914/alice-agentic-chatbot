import './Header.css'

export default function Header() {
  return (
    <header className="header" id="main-header">
      <div className="header-content">
        <div className="header-left">
          <div className="header-avatar">
            <span className="avatar-emoji">🤖</span>
            <span className="status-dot"></span>
          </div>
          <div className="header-text">
            <h1 className="header-title">AliceBot</h1>
            <p className="header-subtitle">AI &amp; Data Career Expert</p>
          </div>
        </div>
        <div className="header-right">
          <span className="header-badge">
            <span className="badge-dot"></span>
            Online
          </span>
        </div>
      </div>
    </header>
  )
}
