export type RoastIntensity = "mentor" | "senior_examiner" | "friday_459";

const LEVELS: { value: RoastIntensity; label: string }[] = [
  { value: "mentor", label: "Mentor" },
  { value: "senior_examiner", label: "Senior Examiner" },
  { value: "friday_459", label: "DOB at 4:59 pm on Friday" },
];

export function RoastDial({ value, onChange }: { value: RoastIntensity; onChange: (v: RoastIntensity) => void }) {
  return (
    <fieldset className="flex flex-col text-xs">
      <legend>Roast</legend>
      <div className="flex overflow-hidden rounded border">
        {LEVELS.map((level) => (
          <button key={level.value} onClick={() => onChange(level.value)}
            className={`px-2 py-1 text-xs ${value === level.value ? "bg-ink text-white" : "bg-white"}`}>
            {level.label}
          </button>
        ))}
      </div>
    </fieldset>
  );
}
