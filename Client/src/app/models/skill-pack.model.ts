/** A guide bundled in the portfolioOS skill package. */
export interface PackagedSkill {
  name: string;
  title: string;
  description: string;
  writes: boolean;
}

/** A workflow kept out of the package, with why. */
export interface UnpublishedSkill {
  name: string;
  title: string;
  description: string;
  reason: string;
}

/** `Server/static/portfolioos-manifest.json`, generated with the package. */
export interface SkillPackManifest {
  revised_at: string;
  content_sha256: string;
  published: PackagedSkill[];
  unpublished: UnpublishedSkill[];
}
