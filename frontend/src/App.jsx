import { useCallback, useEffect, useState } from "react";

import { apiFetch } from "./api.js";
import Shell from "./components/Shell.jsx";
import NutritionScreen from "./screens/NutritionScreen.jsx";
import ProfileScreen from "./screens/ProfileScreen.jsx";
import StatsScreen from "./screens/StatsScreen.jsx";
import TodayScreen from "./screens/TodayScreen.jsx";
import WorkoutScreen from "./screens/WorkoutScreen.jsx";
import { expandApp } from "./telegram.js";

export default function App() {
  const [activeTab, setActiveTab] = useState("today");
  const [profile, setProfile] = useState(null);
  const [nutrition, setNutrition] = useState(null);
  const [workouts, setWorkouts] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  const resetScroll = useCallback(() => {
    window.scrollTo(0, 0);
    window.requestAnimationFrame(() => window.scrollTo(0, 0));
    window.setTimeout(() => window.scrollTo(0, 0), 120);
  }, []);

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
    resetScroll();
    refreshAll();
  }, [refreshAll, resetScroll]);

  useEffect(() => {
    resetScroll();
  }, [activeTab, resetScroll]);

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
      {activeTab === "stats" ? <StatsScreen /> : null}
      {activeTab === "profile" ? <ProfileScreen profile={profile} /> : null}
    </Shell>
  );
}
