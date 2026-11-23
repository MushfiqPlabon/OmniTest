import { createSignal, onSettled, untrack } from "solid-js";

export type ColorSchemePref = "light dark" | "light" | "dark";

const STORAGE_KEY = "color-scheme";

function readStoredScheme(): ColorSchemePref {
  try {
    const val = localStorage.getItem(STORAGE_KEY);
    if (val === "light" || val === "dark") return val;
  } catch {
    // Ignore restricted storage access.
  }
  return "light dark";
}

function writeMetaScheme(pref: ColorSchemePref): void {
  const meta = document.querySelector<HTMLMetaElement>('meta[name="color-scheme"]');
  if (meta) meta.content = pref;
}

const initialSystemDark =
  typeof window !== "undefined" ? window.matchMedia("(prefers-color-scheme: dark)").matches : false;

const [schemePref, setSchemePref] = createSignal<ColorSchemePref>(readStoredScheme());
const [systemIsDark, setSystemIsDark] = createSignal<boolean>(initialSystemDark);

export function resolvedScheme(): "light" | "dark" {
  const current = schemePref();
  if (current === "light" || current === "dark") return current;
  return systemIsDark() ? "dark" : "light";
}

export function setColorScheme(next: ColorSchemePref): void {
  setSchemePref(next);
  writeMetaScheme(next);
  try {
    if (next === "light dark") {
      localStorage.removeItem(STORAGE_KEY);
    } else {
      localStorage.setItem(STORAGE_KEY, next);
    }
  } catch {
    // Ignore storage failures.
  }
}

export function cycleColorScheme(): void {
  const order: ColorSchemePref[] = ["light dark", "light", "dark"];
  const idx = order.indexOf(untrack(schemePref));
  setColorScheme(order[(idx + 1) % order.length]);
}

export function initThemeSync(): void {
  onSettled(() => {
    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    if (mql.matches !== untrack(systemIsDark)) {
      setSystemIsDark(mql.matches);
    }
    const onMediaChange = (e: MediaQueryListEvent) => setSystemIsDark(e.matches);
    const onStorage = (e: StorageEvent) => {
      if (e.key !== STORAGE_KEY && e.key !== null) return;
      const synced = e.newValue === "light" || e.newValue === "dark" ? e.newValue : "light dark";
      setSchemePref(synced);
      writeMetaScheme(synced);
    };
    mql.addEventListener("change", onMediaChange);
    window.addEventListener("storage", onStorage);
    return () => {
      mql.removeEventListener("change", onMediaChange);
      window.removeEventListener("storage", onStorage);
    };
  });
}

export { schemePref };
