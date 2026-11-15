// The similarity ring: an SVG circle whose stroke fills to the score. Clamped, so a bad score draws empty.

export function ringDash(score: number, r: number): { circumference: number; dash: number } {
  const circumference = 2 * Math.PI * r;
  const clamped = Number.isFinite(score) ? Math.min(1, Math.max(0, score)) : 0;
  return { circumference, dash: circumference * clamped };
}
