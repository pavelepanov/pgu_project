import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "./api.js";
import Shell from "./components/Shell.jsx";
import NutritionScreen from "./screens/NutritionScreen.jsx";
import ProfileScreen from "./screens/ProfileScreen.jsx";
import TodayScreen from "./screens/TodayScreen.jsx";
import WorkoutScreen from "./screens/WorkoutScreen.jsx";
import { expandApp, getThemeParams } from "./telegram.js";

function applyTelegramTheme() {
  const theme = getThemeParams();
  if (theme.bg_color) document.documentElement.style.setProperty("--app-bg", theme.bg_color);
  if (theme.text_color) document.documentElement.style.setProperty("--text", theme.text_color);
  if (theme.button_color) document.documentElement.style.setProperty("--accent", theme.button_color);
}

export default function App() {
  const [activeTab, setActiveTab] = useState("today");
  const [profile, setProfile] = useState(null);
  const [nutrition, setNutrition] = useState(null);
  const [workouts, setWorkouts] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  const refreshAll = useCallback(async () => {
    setError("");
    try {
      const [profileData, nutritionData, workoutsData] = await Promise.all([
        apiFetch("/api/profile"),
        apiFetch("/api/nutrition/today"),
        apiFetch("/api/workouts/today")
      ]);
      setProfile(profileData);
      setNutrition(nutritionData);
      setWorkouts(workoutsData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSaved = useCallback(
    async (message) => {
      setToast(message);
      await refreshAll();
      window.setTimeout(() => setToast(""), 1800);
    },
    [refreshAll]
  );

  useEffect(() => {
    expandApp();
    applyTelegramTheme();
    refreshAll();
  }, [refreshAll]);

  return (
    <Shell activeTab={activeTab} onTabChange={setActiveTab} profile={profile} toast={toast}>
      {activeTab === "today" ? (
        <TodayScreen
          profile={profile}
          nutrition={nutrition}
          workouts={workouts}
          loading={loading}
          error={error}
          onNavigate={setActiveTab}
          onRefresh={refreshAll}
        />
      ) : null}
      {activeTab === "nutrition" ? <NutritionScreen nutrition={nutrition} onSaved={handleSaved} /> : null}
      {activeTab === "workout" ? <WorkoutScreen workouts={workouts} onSaved={handleSaved} /> : null}
      {activeTab === "profile" ? <ProfileScreen profile={profile} /> : null}
    </Shell>
  );
}
