import { case01 } from "./case-01";
import { case02 } from "./case-02";
import { case03 } from "./case-03";
import type { CaseData, CaseSlug } from "./types";

export const cases: Record<CaseSlug, CaseData> = {
  "case-01": case01,
  "case-02": case02,
  "case-03": case03,
};

export const caseSlugs = Object.keys(cases) as CaseSlug[];

export function getCase(slug: string): CaseData | undefined {
  return Object.hasOwn(cases, slug) ? cases[slug as CaseSlug] : undefined;
}
