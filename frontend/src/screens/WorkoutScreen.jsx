import { Plus, Search } from "lucide-react";
import { useEffect, useState } from "react";

import { apiFetch } from "../api.js";
import IconButton from "../components/IconButton.jsx";
import { hapticImpact } from "../telegram.js";

export default function WorkoutScreen({ workouts, onSaved }) {
  const [title, setTitle] = useState("Тренировка");
  const [query, setQuery] = useState("");
  const [exercises, setExercises] = useState([]);
  const [selected, setSelected] = useState(null);
  const [previous, setPrevious] = useState(null);
  const [weight, setWeight] = useState(0);
  const [reps, setReps] = useState(8);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const activeWorkout = workouts?.workouts?.[0] || null;

  useEffect(() => {
    const timeout = window.setTimeout(async () => {
      try {
        const data = await apiFetch(`/api/dictionaries/exercises?query=${encodeURIComponent(query)}`);
        setExercises(data.items || []);
      } catch (err) {
        setError(err.message);
      }
    }, 180);
    return () => window.clearTimeout(timeout);
  }, [query]);

  async function chooseExercise(exercise) {
    setSelected(exercise);
    setError("");
    try {
      const data = await apiFetch(`/api/workouts/previous-set?exercise_id=${exercise.id}`);
      setPrevious(data.item);
      if (data.item) {
        setWeight(data.item.weight_kg);
        setReps(data.item.reps);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function createWorkout(showToast = true) {
    setError("");
    try {
      const workout = await apiFetch("/api/workouts", {
        method: "POST",
        body: { title: title || "Тренировка" }
      });
      if (showToast) await onSaved(`Создана: ${workout.title}`);
      return workout;
    } catch (err) {
      setError(err.message);
      if (!showToast) throw err;
      return null;
    }
  }

  async function addSet() {
    if (!selected) return;
    setSaving(true);
    setError("");
    try {
      const workout = activeWorkout || (await createWorkout(false));
      await apiFetch(`/api/workouts/${workout.id}/sets`, {
        method: "POST",
        body: {
          exercise_id: selected.id,
          weight_kg: Number(weight),
          reps: Number(reps)
        }
      });
      hapticImpact("medium");
      await onSaved("Подход добавлен. +5 XP");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="screen stack">
      <div className="surface">
        <div className="section-head">
          <h2>{activeWorkout ? activeWorkout.title : "Новая тренировка"}</h2>
          {!activeWorkout ? (
            <button type="button" onClick={() => createWorkout(true)} aria-label="Создать тренировку">
              <Plus size={18} />
            </button>
          ) : null}
        </div>

        {!activeWorkout ? (
          <label className="field">
            <span>Название</span>
            <input className="plain-input" value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>
        ) : null}

        <label className="field">
          <span>Упражнение</span>
          <div className="input-shell">
            <Search size={18} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Жим, присед, тяга" />
          </div>
        </label>

        <div className="product-list">
          {exercises.map((exercise) => (
            <button
              key={exercise.id}
              type="button"
              className={selected?.id === exercise.id ? "product-row is-active" : "product-row"}
              onClick={() => chooseExercise(exercise)}
            >
              <span>{exercise.name}</span>
              <strong>{exercise.muscle_group}</strong>
            </button>
          ))}
        </div>

        {selected ? (
          <div className="selected-panel">
            {previous ? (
              <p className="hint">
                Прошлый раз: {previous.weight_kg} кг × {previous.reps}
              </p>
            ) : (
              <p className="hint">Первый подход по этому упражнению.</p>
            )}
            <div className="form-grid">
              <label className="field">
                <span>Вес, кг</span>
                <input className="plain-input" type="number" min="0" max="500" value={weight} onChange={(event) => setWeight(event.target.value)} />
              </label>
              <label className="field">
                <span>Повторы</span>
                <input className="plain-input" type="number" min="1" max="300" value={reps} onChange={(event) => setReps(event.target.value)} />
              </label>
            </div>
            <IconButton onClick={addSet} disabled={saving}>{saving ? "Сохраняю..." : "Добавить подход"}</IconButton>
          </div>
        ) : null}

        {error ? <p className="form-error">{error}</p> : null}
      </div>

      <section className="surface">
        <div className="section-head">
          <h2>Сегодня</h2>
          <span>{workouts?.total_sets || 0} подходов</span>
        </div>
        {(workouts?.workouts || []).length === 0 ? <p className="empty">Тренировка еще не начата.</p> : null}
        <div className="list">
          {(workouts?.workouts || []).map((workout) => (
            <div className="workout-mini" key={workout.id}>
              <div className="list-row">
                <div>
                  <span>{workout.sets.length} подходов</span>
                  <strong>{workout.title}</strong>
                </div>
              </div>
              {workout.sets.map((set) => (
                <div className="sub-row" key={set.id}>
                  <span>{set.set_index}. {set.exercise_name}</span>
                  <strong>{set.weight_kg} кг × {set.reps}</strong>
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>
    </section>
  );
}
