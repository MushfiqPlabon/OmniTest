import type { JSX } from "@solidjs/web";
import { createContext, createSignal, useContext } from "solid-js";

export type ToastTone = "info" | "success" | "error";

export interface ToastItem {
  id: number;
  message: string;
  tone: ToastTone;
}

interface ToastContextValue {
  items: () => ToastItem[];
  push: (message: string, tone?: ToastTone) => void;
  dismiss: (id: number) => void;
}

const ToastContext = createContext<ToastContextValue>();

export function ToastProvider(props: { children: JSX.Element }) {
  const [items, setItems] = createSignal<ToastItem[]>([]);
  let nextId = 1;

  const dismiss = (id: number) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
  };

  const push = (message: string, tone: ToastTone = "info") => {
    const id = nextId++;
    setItems((prev) => [...prev.slice(-3), { id, message, tone }]);
    window.setTimeout(() => dismiss(id), 4200);
  };

  return <ToastContext value={{ items, push, dismiss }}>{props.children}</ToastContext>;
}

export function useToast(): ToastContextValue {
  return useContext(ToastContext);
}
