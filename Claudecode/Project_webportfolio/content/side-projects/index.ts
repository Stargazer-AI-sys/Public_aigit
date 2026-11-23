import type { CaseData, SideSlug } from "@/content/cases/types";
import { llmwiki } from "./llmwiki";

export const sideProjects: Record<SideSlug, CaseData> = {
  llmwiki,
};

export const sideSlugs = Object.keys(sideProjects) as SideSlug[];

export function getSideProject(slug: string): CaseData | undefined {
  return Object.hasOwn(sideProjects, slug)
    ? sideProjects[slug as SideSlug]
    : undefined;
}
