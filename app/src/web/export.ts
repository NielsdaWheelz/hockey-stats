export type CsvCell = string | number | boolean | null | undefined;

// textual cells are always quoted; a leading apostrophe prevents spreadsheet
// formula execution. numeric cells retain their sign and exact finite value.
export function csvText(
  headers: readonly string[],
  rows: readonly (readonly CsvCell[])[],
): string {
  const cell = (value: CsvCell): string => {
    if (value === null || value === undefined) return "";
    if (typeof value === "number") {
      if (!Number.isFinite(value))
        throw new Error("csv numbers must be finite");
      return String(value);
    }
    if (typeof value === "boolean") return String(value);
    const text =
      /^[\s]*[=+\-@]/.test(value) || /^[\t\r\n]/.test(value)
        ? `'${value}`
        : value;
    return `"${text.replaceAll('"', '""')}"`;
  };
  return (
    [headers, ...rows].map((row) => row.map(cell).join(",")).join("\r\n") +
    "\r\n"
  );
}

export function downloadBlob(blob: Blob, filename: string): void {
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  try {
    link.href = url;
    link.download = filename;
    document.body.append(link);
    link.click();
  } finally {
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}

export function downloadCsv(
  headers: readonly string[],
  rows: readonly (readonly CsvCell[])[],
  filename: string,
): void {
  downloadBlob(
    new Blob([csvText(headers, rows)], { type: "text/csv;charset=utf-8" }),
    filename,
  );
}

export async function svgPng(svg: string): Promise<Blob> {
  const source = URL.createObjectURL(
    new Blob([svg], { type: "image/svg+xml;charset=utf-8" }),
  );
  try {
    const image = new Image();
    await new Promise<void>((resolve, reject) => {
      image.onload = () => resolve();
      image.onerror = () => reject(new Error("the image could not be decoded"));
      image.src = source;
    });
    if (!image.naturalWidth || !image.naturalHeight)
      throw new Error("the image has no drawable dimensions");
    const canvas = document.createElement("canvas");
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    const context = canvas.getContext("2d");
    if (!context) throw new Error("image rendering is unavailable");
    context.drawImage(image, 0, 0);
    return await new Promise<Blob>((resolve, reject) =>
      canvas.toBlob(
        (blob) =>
          blob
            ? resolve(blob)
            : reject(new Error("the png could not be created")),
        "image/png",
      ),
    );
  } finally {
    URL.revokeObjectURL(source);
  }
}
