import { Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { apiFetch } from "../api.js";
import IconButton from "../components/IconButton.jsx";
import { hapticImpact } from "../telegram.js";

const mealTypes = [
  { key: "breakfast", label: "Завтрак" },
  { key: "lunch", label: "Обед" },
  { key: "dinner", label: "Ужин" },
  { key: "snack", label: "Перекус" }
];

function macro(product, key, grams) {
  if (!product) return 0;
  return Math.round((Number(product[key]) * Number(grams || 0)) / 10) / 10;
}

export default function NutritionScreen({ nutrition, onSaved }) {
  const [mealType, setMealType] = useState("breakfast");
  const [query, setQuery] = useState("");
  const [products, setProducts] = useState([]);
  const [selected, setSelected] = useState(null);
  const [grams, setGrams] = useState(100);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const timeout = window.setTimeout(async () => {
      try {
        const data = await apiFetch(`/api/dictionaries/foods?query=${encodeURIComponent(query)}`);
        setProducts(data.items || []);
      } catch (err) {
        setError(err.message);
      }
    }, 180);
    return () => window.clearTimeout(timeout);
  }, [query]);

  const preview = useMemo(() => {
    if (!selected) return null;
    return {
      calories: Math.round((selected.calories_per_100g * Number(grams || 0)) / 100),
      protein: macro(selected, "protein_per_100g", grams),
      fat: macro(selected, "fat_per_100g", grams),
      carbs: macro(selected, "carbs_per_100g", grams)
    };
  }, [selected, grams]);

  async function saveMeal() {
    if (!selected) return;
    setSaving(true);
    setError("");
    try {
      await apiFetch("/api/nutrition/entries", {
        method: "POST",
        body: {
          product_id: selected.id,
          meal_type: mealType,
          grams: Number(grams)
        }
      });
      hapticImpact("medium");
      setSelected(null);
      setQuery("");
      await onSaved("Еда добавлена. +10 XP");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function deleteEntry(entryId) {
    setError("");
    try {
      await apiFetch(`/api/nutrition/entries/${entryId}`, { method: "DELETE" });
      hapticImpact("light");
      await onSaved("Запись удалена");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="screen stack">
      <div className="surface">
        <div className="section-head">
          <h2>Новый прием пищи</h2>
        </div>

        <div className="segmented">
          {mealTypes.map((item) => (
            <button
              key={item.key}
              type="button"
              className={mealType === item.key ? "is-active" : ""}
              onClick={() => setMealType(item.key)}
            >
              {item.label}
            </button>
          ))}
        </div>

        <label className="field">
          <span>Продукт</span>
          <div className="input-shell">
            <Search size={18} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Курица, рис, творог" />
          </div>
        </label>

        <div className="product-list">
          {products.map((product) => (
            <button
              key={product.id}
              type="button"
              className={selected?.id === product.id ? "product-row is-active" : "product-row"}
              onClick={() => {
                setSelected(product);
                setGrams(product.default_grams || 100);
              }}
            >
              <span>{product.name}</span>
              <strong>{product.calories_per_100g} ккал</strong>
            </button>
          ))}
        </div>

        {selected ? (
          <div className="selected-panel">
            <label className="field">
              <span>Граммы</span>
              <input className="plain-input" type="number" min="1" max="3000" value={grams} onChange={(event) => setGrams(event.target.value)} />
            </label>
            <div className="metric-grid metric-grid--compact">
              <div className="metric"><span>Ккал</span><strong>{preview.calories}</strong></div>
              <div className="metric"><span>Б</span><strong>{preview.protein}</strong></div>
              <div className="metric"><span>Ж</span><strong>{preview.fat}</strong></div>
              <div className="metric"><span>У</span><strong>{preview.carbs}</strong></div>
            </div>
            <IconButton onClick={saveMeal} disabled={saving}>{saving ? "Сохраняю..." : "Добавить"}</IconButton>
          </div>
        ) : null}

        {error ? <p className="form-error">{error}</p> : null}
      </div>

      <section className="surface">
        <div className="section-head">
          <h2>Сегодня</h2>
          <span>{nutrition?.totals?.calories || 0} ккал</span>
        </div>
        {(nutrition?.entries || []).length === 0 ? <p className="empty">Пока пусто.</p> : null}
        <div className="list">
          {(nutrition?.entries || []).map((entry) => (
            <div className="list-row" key={entry.id}>
              <div>
                <span>{mealTypes.find((item) => item.key === entry.meal_type)?.label}</span>
                <strong>{entry.product_name}</strong>
              </div>
              <p>{entry.grams} г · {entry.calories} ккал</p>
              <button className="ghost-icon" type="button" onClick={() => deleteEntry(entry.id)} aria-label="Удалить запись">
                <Trash2 size={17} />
              </button>
            </div>
          ))}
        </div>
      </section>
    </section>
  );
}
