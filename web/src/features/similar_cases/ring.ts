// The similarity ring: an SVG circle whose stroke fills to the score. Clamped, so a bad score draws empty.

export function ringDash(score: number, r: number): { circumference: number; dash: number } {
  const circumference = 2 * Math.PI * r;
  const clamped = Number.isFinite(score) ? Math.min(1, Math.max(0, score)) : 0;
  return { circumference, dash: circumference * clamped };
}

export type Resemblance = { level: "strong" | "some" | "weak"; word: string; bars: 1 | 2 | 3 };

/** The similarity score as a word: easier to read than a number, and no one mistakes "Strong" for 64%. */
export function resemblance(score: number): Resemblance {
  const s = Number.isFinite(score) ? score : 0;
  if (s >= 0.5) return { level: "strong", word: "Strong", bars: 3 };
  if (s >= 0.35) return { level: "some", word: "Some", bars: 2 };
  return { level: "weak", word: "Weak", bars: 1 };
}
