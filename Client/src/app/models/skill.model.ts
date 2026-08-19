export interface Skill {
  name: string;
  description: string;
  version: string;
  writes: boolean;
  reads_external: boolean;
  published: boolean;
  blocked_reason?: string;
  files?: string[];
}

export interface SkillListResponse {
  items: Skill[];
  total: number;
}
