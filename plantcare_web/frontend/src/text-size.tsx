import {
  createContext,
  useCallback,
  useContext,
  useLayoutEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  isTextSizePreference,
  readTextSizePreference,
  saveTextSizePreference,
  TEXT_SIZE_SCALES,
  type TextSizePreference,
} from "./text-size-preference";

type TextSizeValue = {
  preference: TextSizePreference;
  setPreference: (value: TextSizePreference) => void;
};

const TextSizeContext = createContext<TextSizeValue | null>(null);

export function TextSizeProvider({ children }: { children: ReactNode }) {
  const [preference, setPreferenceState] = useState(readTextSizePreference);

  useLayoutEffect(() => {
    const root = document.documentElement;
    root.dataset.textSize = preference;
    root.style.setProperty("--vc-text-scale", String(TEXT_SIZE_SCALES[preference]));
  }, [preference]);

  const setPreference = useCallback((value: TextSizePreference) => {
    if (!isTextSizePreference(value)) return;
    setPreferenceState(value);
    saveTextSizePreference(value);
  }, []);

  const value = useMemo(
    () => ({ preference, setPreference }),
    [preference, setPreference],
  );

  return <TextSizeContext.Provider value={value}>{children}</TextSizeContext.Provider>;
}

export function useTextSize() {
  const value = useContext(TextSizeContext);
  if (!value) throw new Error("useTextSize must be used inside TextSizeProvider");
  return value;
}
