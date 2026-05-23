import { useState } from "react";
import { X, Camera } from "lucide-react";
import { apiFetch } from "../api.js";

export default function FoodRecognition({ onRecognized, onClose }) {
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");
  const [recognizedData, setRecognizedData] = useState(null);

  async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    setPreview(URL.createObjectURL(file));
    setLoading(true);
    setError("");
    setRecognizedData(null);

    try {
      const formData = new FormData();
      formData.append("image", file);

      const result = await apiFetch("/api/nutrition/recognize", {
        method: "POST",
        body: formData,
      });

      if (result.success && result.recognized) {
        setRecognizedData(result.recognized);
      } else {
        setError(result.message || "Не удалось распознать блюдо");
      }
    } catch (err) {
      setError("Ошибка загрузки: " + err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleConfirm() {
    if (recognizedData && onRecognized) {
      onRecognized(recognizedData);
    }
  }

  return (
    <div className="food-recognition-modal">
      <div className="food-recognition-content">
        <div className="food-recognition-header">
          <h2>📸 Распознать блюдо</h2>
          <button type="button" className="food-recognition-close" onClick={() => onClose(null)}>
            <X size={24} />
          </button>
        </div>

        {!preview ? (
          <label className="food-recognition-upload">
            <input
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleImageUpload}
              disabled={loading}
              style={{ display: "none" }}
            />
            <div className="upload-icon">
              <Camera size={42} />
            </div>
            <p>Нажмите, чтобы сфотографировать</p>
            <p className="hint">или выбрать из галереи</p>
          </label>
        ) : (
          <div className="food-recognition-preview">
            <img src={preview} alt="Предпросмотр" />
            {loading && (
              <div className="food-recognition-loading">
                <div className="spinner"></div>
                <p>🤖 Распознаю блюдо...</p>
              </div>
            )}
          </div>
        )}

        {recognizedData && (
          <div className="food-recognition-result">
            <h3>✅ Распознано:</h3>
            <div className="food-info">
              <p><strong>Блюдо:</strong> {recognizedData.food_name}</p>
              <p><strong>Вес:</strong> {recognizedData.nutrition.grams}г</p>
              <p><strong>Калории:</strong> {recognizedData.nutrition.calories} ккал</p>
              <p><strong>БЖУ:</strong> {recognizedData.nutrition.protein}г / {recognizedData.nutrition.fat}г / {recognizedData.nutrition.carbs}г</p>
            </div>
            <div className="food-recognition-buttons">
              <button type="button" className="button--secondary" onClick={() => onClose(null)}>
                Отмена
              </button>
              <button type="button" className="button--primary" onClick={handleConfirm} disabled={loading}>
                Использовать эти данные
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="food-recognition-error">
            <p>⚠️ {error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
