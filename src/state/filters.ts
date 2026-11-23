import { useSearchParams } from "@solidjs/router";
import type { FilterState } from "@/components/FilterBar";

export function usePagedFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters = (): FilterState => ({
    search: typeof searchParams.search === "string" ? searchParams.search : "",
    subject: typeof searchParams.subject === "string" ? searchParams.subject : "",
    difficulty: typeof searchParams.difficulty === "string" ? searchParams.difficulty : "",
  });

  const page = (): number => {
    const raw = typeof searchParams.page === "string" ? Number(searchParams.page) : 1;
    return Number.isFinite(raw) && raw >= 1 ? Math.floor(raw) : 1;
  };

  const updateFilters = (next: Partial<FilterState>) => {
    const patch: Record<string, string | undefined> = { page: undefined };
    if ("search" in next) patch.search = next.search || undefined;
    if ("subject" in next) patch.subject = next.subject || undefined;
    if ("difficulty" in next) patch.difficulty = next.difficulty || undefined;
    setSearchParams(patch);
  };

  const clearFilters = () => {
    setSearchParams({ search: undefined, subject: undefined, difficulty: undefined, page: undefined });
  };

  const setPage = (nextPage: number) => {
    setSearchParams({ page: nextPage > 1 ? String(nextPage) : undefined });
  };

  const apiQuery = (size = 10) => {
    const f = filters();
    return {
      page: page(),
      size,
      search: f.search.trim() || undefined,
      subject: f.subject || undefined,
      difficulty: f.difficulty || undefined,
    };
  };

  return { filters, page, updateFilters, clearFilters, setPage, apiQuery };
}
