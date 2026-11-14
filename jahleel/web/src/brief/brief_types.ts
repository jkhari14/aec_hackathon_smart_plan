// Names for the generated API types. Regenerate the source with `npm run types` after an API change.
import type { components } from "./brief_api_types";

type Schemas = components["schemas"];
export type Brief = Schemas["Brief"];
export type BriefListing = Schemas["BriefListing"];
export type Lot = Schemas["Lot"];
export type PublicRecord = Schemas["PublicRecord"];
export type ComplaintCodeKey = Schemas["ComplaintCodeKey"];
export type ComplaintCodeKeys = Record<string, ComplaintCodeKey>;
export type ChecklistRow = Schemas["ChecklistRow"];
export type ApplyStatus = ChecklistRow["applies"]["status"];
export type Party = ChecklistRow["parties"][number];
export type ProjectType = Brief["project_type"];
