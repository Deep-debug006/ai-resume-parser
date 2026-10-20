/**
 * Types for Phase 10: Skill Normalization & Taxonomy.
 */

export interface NormalizeSkillsResponse {
  original_count: number;
  normalized_count: number;
  normalized_skills: string[];
  aliases_resolved: Record<string, string>;
  duplicates_removed: string[];
  unrecognized_skills: string[];
}

export interface SkillDictionaryStatsResponse {
  canonical_count: number;
  aliases_count: number;
  canonical_skills: string[];
}
