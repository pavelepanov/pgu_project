import { Activity, Dumbbell, Utensils, UserRound } from "lucide-react";

import { isTelegram } from "../telegram.js";

const tabs = [
  { key: "today", label: "Сегодня", icon: Activity },
  { key: "nutrition", label: "Еда", icon: Utensils },
  { key: "workout", label: "Зал", icon: Dumbbell },
  { key: "profile", label: "Профиль", icon: UserRound }
];

export default function Shell({ activeTab, onTabChange, profile, children, toast }) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">HealthQuest</p>
          <h1>{profile?.first_name ? `Привет, ${profile.first_name}` : "Твой день"}</h1>
        </div>
        <div className="topbar__meta">
          {!isTelegram() ? <span className="dev-pill">Dev</span> : null}
          <span className="xp-pill">Lv {profile?.level || 1}</span>
        </div>
      </header>

      <main className="app-content">{children}</main>

      {toast ? <div className="toast">{toast}</div> : null}

      <nav className="tabbar" aria-label="Основная навигация">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              type="button"
              className={`tabbar__item ${active ? "is-active" : ""}`}
              onClick={() => onTabChange(tab.key)}
              aria-label={tab.label}
            >
              <Icon size={21} strokeWidth={2.2} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
