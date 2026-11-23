import { api, type Schemas, unwrap, uploadMaterialFile } from "@/api/client";

export type Diff = "easy" | "medium" | "hard";

export async function saveMaterialSubmission(opts: {
  editingId: number | null;
  mode: "text" | "file";
  title: string;
  subject: string;
  topic: string;
  difficulty: Diff;
  source: string;
  content: string;
  file: File | null;
}): Promise<string> {
  const payload: Schemas["MaterialCreate"] = {
    title: opts.title.trim(),
    subject: opts.subject.trim(),
    topic: opts.topic.trim(),
    difficulty: opts.difficulty,
    source: opts.source.trim() || null,
    content: opts.content,
  };
  if (opts.editingId !== null) {
    await unwrap(
      api.PATCH("/api/v1/materials/{material_id}", {
        params: { path: { material_id: opts.editingId } },
        body: payload,
      }),
    );
    return "Study material updated";
  }
  if (opts.mode === "file") {
    if (!opts.file) throw new Error("Choose a .pdf, .md, or .txt file to upload");
    const fd = new FormData();
    fd.append("title", payload.title);
    fd.append("subject", payload.subject);
    fd.append("topic", payload.topic);
    fd.append("difficulty", payload.difficulty);
    fd.append("file", opts.file);
    await uploadMaterialFile(fd);
    return "Material uploaded & ingested";
  }
  await unwrap(api.POST("/api/v1/materials", { body: payload }));
  return "Study material created";
}
