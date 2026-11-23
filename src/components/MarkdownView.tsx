import { Marked } from "marked";
import markedKatex from "marked-katex-extension";
import { createEffect, createSignal } from "solid-js";
import "katex/dist/katex.min.css";

const renderer = new Marked();
renderer.use(markedKatex({ throwOnError: false, nonStandard: true, output: "mathml" }));

type PurifyModule = typeof import("dompurify");
let domPurifyPromise: Promise<PurifyModule["default"]> | undefined;

function loadDOMPurify() {
  domPurifyPromise ??= import("dompurify").then((mod) => mod.default ?? mod);
  return domPurifyPromise;
}

async function renderSafeHtml(el: HTMLElement, rawHtml: string): Promise<void> {
  if (
    "setHTML" in Element.prototype &&
    typeof (el as HTMLElement & { setHTML?: (s: string) => void }).setHTML === "function"
  ) {
    (el as HTMLElement & { setHTML: (s: string) => void }).setHTML(rawHtml);
    return;
  }
  const DOMPurify = await loadDOMPurify();
  el.innerHTML = DOMPurify.sanitize(rawHtml, {
    USE_PROFILES: { html: true, mathMl: true },
    ALLOW_ARIA_ATTR: false,
    ALLOW_DATA_ATTR: false,
    KEEP_CONTENT: false,
  });
}

export function MarkdownView(props: { content: string; class?: string }) {
  const [host, setHost] = createSignal<HTMLDivElement>();

  createEffect(
    () => ({ el: host(), text: props.content }),
    ({ el, text }) => {
      if (!el) return;
      let cancelled = false;
      const html = String(renderer.parse(text ?? ""));
      renderSafeHtml(el, html).catch(() => {
        if (!cancelled) el.textContent = text;
      });
      return () => {
        cancelled = true;
      };
    },
  );

  return (
    <div
      ref={setHost}
      class={[
        "prose-study max-w-[74ch] text-sm leading-relaxed text-ink [&_a]:text-brand [&_a]:underline [&_code]:rounded [&_code]:bg-canvas [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-xs [&_h1]:mt-4 [&_h1]:text-xl [&_h1]:font-bold [&_h2]:mt-4 [&_h2]:text-lg [&_h2]:font-semibold [&_h3]:mt-3 [&_h3]:text-base [&_h3]:font-semibold [&_ol]:my-2 [&_ol]:list-decimal [&_ol]:pl-5 [&_p]:my-2 [&_pre]:my-3 [&_pre]:overflow-x-auto [&_pre]:rounded-xl [&_pre]:border [&_pre]:border-edge [&_pre]:bg-canvas [&_pre]:p-3 [&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5",
        props.class,
      ]}
    />
  );
}
