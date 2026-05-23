import { Camera, PencilLine, Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

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

function numeric(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export default function NutritionScreen({ nutrition, onSaved }) {
  const [mealType, setMealType] = useState("breakfast");
  const [entryMode, setEntryMode] = useState("base");
  const [query, setQuery] = useState("");
  const [products, setProducts] = useState([]);
  const [selected, setSelected] = useState(null);
  const [grams, setGrams] = useState(100);
  const [manual, setManual] = useState({
    product_name: "",
    grams: 100,
    calories: 0,
    protein: 0,
    fat: 0,
    carbs: 0
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const photoInputRef = useRef(null);

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
    if (numeric(grams) <= 0 || numeric(grams) > 1000000) {
      setError("Вес продукта должен быть от 1 до 1000000 г");
      return;
    }

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

  function updateManual(field, value) {
    setManual((current) => ({ ...current, [field]: value }));
  }

  async function saveManualMeal() {
    if (!manual.product_name.trim()) {
      setError("Введите название блюда");
      return;
    }
    if (numeric(manual.grams) <= 0 || numeric(manual.grams) > 1000000) {
      setError("Вес блюда должен быть от 1 до 1000000 г");
      return;
    }

    setSaving(true);
    setError("");
    try {
      await apiFetch("/api/nutrition/manual", {
        method: "POST",
        body: {
          product_name: manual.product_name,
          meal_type: mealType,
          grams: Number(manual.grams),
          calories: Number(manual.calories),
          protein: Number(manual.protein),
          fat: Number(manual.fat),
          carbs: Number(manual.carbs)
        }
      });
      hapticImpact("medium");
      setManual({ product_name: "", grams: 100, calories: 0, protein: 0, fat: 0, carbs: 0 });
      await onSaved("БЖУ добавлено вручную. +10 XP");
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

        <button
          type="button"
          className="photo-stub"
          onClick={() => photoInputRef.current?.click()}
        >
          <Camera size={19} />
          <span>Фото блюда</span>
          <strong>позже</strong>
        </button>
        <input
          ref={photoInputRef}
          type="file"
          accept="image/*"
          style={{ display: "none" }}
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (!file) return;
            setNotice("Распознавание еды по фото пока не поддерживается. Вы можете добавить блюдо вручную.");
            event.target.value = "";
          }}
        />
        {notice ? <p className="hint photo-stub__hint">{notice}</p> : null}

        <div className="segmented segmented--two">
          <button type="button" className={entryMode === "base" ? "is-active" : ""} onClick={() => setEntryMode("base")}>
            <Search size={15} />
            База
          </button>
          <button type="button" className={entryMode === "manual" ? "is-active" : ""} onClick={() => setEntryMode("manual")}>
            <PencilLine size={15} />
            Вручную
          </button>
        </div>

        {entryMode === "base" ? (
          <>
            <label className="field">
              <span>Продукт</span>
              <div className="input-shell">
                <Search size={18} />
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Курица, рис, творог" />
              </div>
            </label>

            {selected ? (
              <div className="selected-panel selected-panel--compact sticky-actions">
                <div className="selected-title">
                  <div>
                    <span>Выбран продукт</span>
                    <strong>{selected.name}</strong>
                  </div>
                </div>
                <label className="field">
                  <span>Граммы</span>
                  <input className="plain-input" type="number" min="1" max="1000000" value={grams} onChange={(event) => setGrams(event.target.value)} />
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
          </>
        ) : null}

        {entryMode === "manual" ? (
          <div className="selected-panel selected-panel--plain sticky-actions">
            <label className="field">
              <span>Название блюда</span>
              <input
                className="plain-input"
                value={manual.product_name}
                onChange={(event) => updateManual("product_name", event.target.value)}
                placeholder="Например, омлет с сыром"
              />
            </label>
            <div className="form-grid">
              <label className="field">
                <span>Граммы</span>
                <input className="plain-input" type="number" min="1" max="1000000" value={manual.grams} onChange={(event) => updateManual("grams", event.target.value)} />
              </label>
              <label className="field">
                <span>Ккал</span>
                <input className="plain-input" type="number" min="0" max="10000" value={manual.calories} onChange={(event) => updateManual("calories", event.target.value)} />
              </label>
            </div>
            <div className="form-grid form-grid--three">
              <label className="field">
                <span>Белки</span>
                <input className="plain-input" type="number" min="0" max="1000" step="0.1" value={manual.protein} onChange={(event) => updateManual("protein", event.target.value)} />
              </label>
              <label className="field">
                <span>Жиры</span>
                <input className="plain-input" type="number" min="0" max="1000" step="0.1" value={manual.fat} onChange={(event) => updateManual("fat", event.target.value)} />
              </label>
              <label className="field">
                <span>Углеводы</span>
                <input className="plain-input" type="number" min="0" max="1000" step="0.1" value={manual.carbs} onChange={(event) => updateManual("carbs", event.target.value)} />
              </label>
            </div>
            <IconButton onClick={saveManualMeal} disabled={saving}>{saving ? "Сохраняю..." : "Добавить БЖУ"}</IconButton>
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
            <div className="list-row list-row--deletable" key={entry.id}>
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
