// Evidence ids look like "ecb_violations:39553409Z" or "open_meteo:2026-09-27". Each one becomes a short
// label and a link that reproduces that one record on its source.

type Dataset = { label: string; id: string; field: string };

const DATASETS: Record<string, Dataset> = {
  dob_now_filings: { label: "DOB NOW filing", id: "w9ak-ipjd", field: "job_filing_number" },
  dob_violations: { label: "DOB violation", id: "3h2n-5cm9", field: "isn_dob_bis_viol" },
  ecb_violations: { label: "ECB violation", id: "6bgk-3dad", field: "ecb_violation_number" },
  dob_safety_violations: { label: "DOB safety violation", id: "855j-jady", field: "violation_number" },
  dob_complaints: { label: "DOB complaint", id: "eabe-havv", field: "complaint_number" },
  dob_311_requests: { label: "311 request", id: "erm2-nwe9", field: "unique_key" },
};

export type Evidence = { id: string; label: string; source: string; url: string };

export function evidence(ref: string): Evidence {
  const [kind, recordId = ""] = ref.split(/:(.*)/s);
  if (kind === "open_meteo") {
    return {
      id: ref,
      label: `Weather ${recordId}`,
      source: "Open-Meteo historical weather",
      url: "https://open-meteo.com/en/docs/historical-weather-api",
    };
  }
  const dataset = DATASETS[kind];
  if (!dataset) return { id: ref, label: ref, source: "Public record", url: "" };
  const query = new URLSearchParams({ [dataset.field]: recordId });
  return {
    id: ref,
    label: `${dataset.label} ${recordId}`,
    source: `NYC Open Data ${dataset.id}`,
    url: `https://data.cityofnewyork.us/resource/${dataset.id}.json?${query}`,
  };
}
