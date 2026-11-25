import { useId } from "react";
import { useI18n, type MessageKey } from "./i18n";
import { useTextSize } from "./text-size";
import { isTextSizePreference, type TextSizePreference } from "./text-size-preference";

const sizeLabels: Record<TextSizePreference, MessageKey> = {
  small: "settings.textSizeSmall",
  normal: "settings.textSizeNormal",
  large: "settings.textSizeLarge",
  "extra-large": "settings.textSizeExtraLarge",
  maximum: "settings.textSizeMaximum",
};

export function TextSizeControl() {
  const { t } = useI18n();
  const { preference, setPreference } = useTextSize();
  const id = useId();

  return (
    <section className="appearance-settings" aria-labelledby={`${id}-title`}>
      <h3 id={`${id}-title`}>{t("settings.appearance")}</h3>
      <label htmlFor={`${id}-size`}>{t("settings.textSize")}</label>
      <select
        id={`${id}-size`}
        value={preference}
        aria-describedby={`${id}-hint`}
        onChange={(event) => {
          const value = event.target.value;
          if (isTextSizePreference(value)) setPreference(value);
        }}
      >
        {Object.entries(sizeLabels).map(([value, key]) => (
          <option key={value} value={value}>{t(key)}</option>
        ))}
      </select>
      <p id={`${id}-hint`} className="muted small-text">
        {t("settings.textSizeHint")}
      </p>
      <div className="text-size-preview">
        <strong>{t("settings.textSizePreview")}</strong>
        <p>{t("settings.textSizeSample")}</p>
      </div>
      <button
        type="button"
        className="button secondary"
        disabled={preference === "normal"}
        onClick={() => setPreference("normal")}
      >
        {t("settings.textSizeReset")}
      </button>
    </section>
  );
}
