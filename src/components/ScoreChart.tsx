import Chart, { type ChartConfiguration } from "chart.js/auto";
import { createEffect, createSignal } from "solid-js";
import { resolvedScheme } from "@/state/theme";

export function ScoreChart(props: {
  title: string;
  buildConfig: (isDark: boolean) => ChartConfiguration;
  heightClass?: string;
}) {
  const [canvas, setCanvas] = createSignal<HTMLCanvasElement>();

  createEffect(
    () => ({ el: canvas(), scheme: resolvedScheme(), cfg: props.buildConfig(resolvedScheme() === "dark") }),
    ({ el, cfg }) => {
      if (!el) return;
      const instance = new Chart(el, cfg);
      return () => instance.destroy();
    },
  );

  return (
    <div class="reading-surface rounded-2xl p-5">
      <h3 class="mb-3 text-sm font-semibold text-ink">{props.title}</h3>
      <div class={["relative w-full", props.heightClass ?? "h-64"]}>
        <canvas ref={setCanvas} aria-label={props.title} />
      </div>
    </div>
  );
}
