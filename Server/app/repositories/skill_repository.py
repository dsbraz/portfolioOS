import json
import re
import time
from datetime import date
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from app.domain.models.skill import Skill

SKILL_FRONTMATTER_FIELDS = {"name", "description"}
CATALOG_METADATA_FILENAME = ".portfolioos.json"
REQUIRED_CATALOG_FIELDS = {
    "version",
    "writes",
    "reads_external",
    "published",
}
CATALOG_FIELDS = REQUIRED_CATALOG_FIELDS | {"blocked_reason"}
PACKAGE_NAME = "portfolioos"
BASE_SKILL_NAME = "operar-portfolioos"
SKILL_FILENAME = "SKILL.md"
# Upload validators accept exactly one SKILL.md per archive, so internal skills
# are bundled as progressive-disclosure guides instead of nested skills.
INTERNAL_SKILL_FILENAME = "GUIDE.md"
PACK_SKILL_INDEX_MARKER = "<!-- portfolioos:published-skills -->"
_LINKED_FILENAMES = "|".join(
    re.escape(filename) for filename in (SKILL_FILENAME, INTERNAL_SKILL_FILENAME)
)
PACK_SKILL_REFERENCE_PATTERN = re.compile(rf"skills/([^/\s]+)/({_LINKED_FILENAMES})")
PACKAGE_ARTIFACTS = (
    (Path("README.md"), Path("README.md")),
    # OpenAI reads skill UI metadata from `agents/openai.yaml` beside SKILL.md.
    (Path("agents/openai.yaml"), Path("agents/openai.yaml")),
    (Path("PACK_SKILL.md"), Path(SKILL_FILENAME)),
)
# `writestr` stamps 0o600; `write` copies the source mode. Pin both to 0644 so a
# rendered entry extracts like every copied one.
ARCHIVE_FILE_MODE = 0o100644


class SkillRepository:
    def __init__(self, skills_dir: str | Path) -> None:
        self._skills_dir = Path(skills_dir)

    def get_all(self) -> tuple[list[Skill], int]:
        skills = [
            self._load_skill(skill_dir)
            for skill_dir in self._known_skill_directories().values()
        ]
        return skills, len(skills)

    def get_package(self, name: str) -> bytes | None:
        skill_dir = self._known_skill_directories().get(name)
        if skill_dir is None:
            return None

        skill = self._load_skill(skill_dir)
        if not skill.published:
            return None

        output = BytesIO()
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            self._write_skill_files(archive, skill_dir, Path(name))
        return output.getvalue()

    def get_pack(self) -> bytes:
        skill_directories = self._known_skill_directories()
        base_skill_dir = skill_directories.get(BASE_SKILL_NAME)
        if base_skill_dir is None:
            raise ValueError(f"Required base skill is missing: {BASE_SKILL_NAME}")

        base_skill = self._load_skill(base_skill_dir)
        if not base_skill.published:
            raise ValueError(f"Required base skill is unpublished: {BASE_SKILL_NAME}")

        skills_with_directories = [
            (base_skill, base_skill_dir),
            *(
                (self._load_skill(skill_dir), skill_dir)
                for name, skill_dir in skill_directories.items()
                if name != BASE_SKILL_NAME
            ),
        ]
        published_skills = [
            (skill, skill_dir)
            for skill, skill_dir in skills_with_directories
            if skill.published
        ]
        output = BytesIO()
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
            self._write_package_artifacts(
                archive,
                [skill for skill, _ in published_skills],
            )
            for skill, skill_dir in published_skills:
                archive_root = Path(PACKAGE_NAME) / "skills" / skill.name
                self._write_skill_files(
                    archive,
                    skill_dir,
                    archive_root,
                    skill_filename=INTERNAL_SKILL_FILENAME,
                )
            self._validate_single_skill_entrypoint(archive)
        return output.getvalue()

    @staticmethod
    def _validate_single_skill_entrypoint(archive: ZipFile) -> None:
        """Upload validators reject an archive holding more than one SKILL.md."""
        entrypoints = [
            name for name in archive.namelist() if Path(name).name == SKILL_FILENAME
        ]
        expected = [str(Path(PACKAGE_NAME) / SKILL_FILENAME)]
        if entrypoints != expected:
            raise ValueError(
                f"Package must expose exactly one {SKILL_FILENAME} "
                f"at {expected[0]}; found: {entrypoints}"
            )

    def _write_package_artifacts(
        self,
        archive: ZipFile,
        published_skills: list[Skill],
    ) -> None:
        package_dir = self._skills_dir / PACKAGE_NAME
        if not package_dir.is_dir():
            raise ValueError(f"Package artifact is missing: {PACKAGE_NAME}")
        if package_dir.is_symlink():
            raise ValueError("Package directory must not be a symlink")

        for source_relative_path, archive_relative_path in PACKAGE_ARTIFACTS:
            source_path = package_dir / source_relative_path
            if not source_path.is_file() or self._path_contains_symlink(
                source_path,
                package_dir,
            ):
                raise ValueError(
                    f"Package artifact is missing: {source_relative_path.as_posix()}"
                )
            archive_path = str(Path(PACKAGE_NAME) / archive_relative_path)
            if source_relative_path.name == "PACK_SKILL.md":
                self._write_rendered_file(
                    archive,
                    archive_path,
                    source_path,
                    self._render_pack_skill(source_path, published_skills),
                )
            else:
                archive.write(source_path, arcname=archive_path)

    @staticmethod
    def _write_rendered_file(
        archive: ZipFile,
        archive_path: str,
        source_path: Path,
        content: str,
    ) -> None:
        entry = ZipInfo(
            archive_path,
            date_time=time.localtime(source_path.stat().st_mtime)[:6],
        )
        entry.external_attr = ARCHIVE_FILE_MODE << 16
        entry.compress_type = ZIP_DEFLATED
        archive.writestr(entry, content)

    @staticmethod
    def _render_pack_skill(
        template_path: Path,
        published_skills: list[Skill],
    ) -> str:
        template = template_path.read_text(encoding="utf-8")
        marker_count = template.count(PACK_SKILL_INDEX_MARKER)
        if marker_count == 0:
            raise ValueError("Package skill index marker is missing")
        if marker_count > 1:
            raise ValueError("Package skill index marker must appear exactly once")

        ordered_skills = sorted(
            published_skills,
            key=lambda skill: (skill.name != BASE_SKILL_NAME, skill.name),
        )
        skill_index = "\n".join(
            f"- [`{skill.name}`](skills/{skill.name}/{INTERNAL_SKILL_FILENAME}): "
            f"{skill.description}"
            for skill in ordered_skills
        )
        rendered_skill = template.replace(PACK_SKILL_INDEX_MARKER, skill_index)
        references = PACK_SKILL_REFERENCE_PATTERN.findall(rendered_skill)
        published_names = {skill.name for skill in published_skills}
        invalid_references = sorted({name for name, _ in references} - published_names)
        if invalid_references:
            names = ", ".join(invalid_references)
            raise ValueError(
                "Package wrapper references unpublished or unknown skills: " + names
            )

        # An internal workflow is a GUIDE.md inside the archive. A link to the
        # source filename would dangle and hint at a second skill entrypoint.
        stale_references = sorted(
            {name for name, filename in references if filename == SKILL_FILENAME}
        )
        if stale_references:
            names = ", ".join(stale_references)
            raise ValueError(
                f"Package wrapper must link internal workflows as "
                f"{INTERNAL_SKILL_FILENAME}; found {SKILL_FILENAME} links for: {names}"
            )
        return rendered_skill

    def _known_skill_directories(self) -> dict[str, Path]:
        return {
            path.name: path
            for path in sorted(self._skills_dir.iterdir(), key=lambda item: item.name)
            if path.is_dir()
            and not path.is_symlink()
            and not path.name.startswith(".")
            and (path / SKILL_FILENAME).is_file()
            and not (path / SKILL_FILENAME).is_symlink()
        }

    def _load_skill(self, skill_dir: Path) -> Skill:
        frontmatter = self._parse_frontmatter(skill_dir / SKILL_FILENAME)
        self._validate_frontmatter(frontmatter, skill_dir.name)
        catalog_metadata = self._parse_catalog_metadata(skill_dir)
        self._validate_catalog_metadata(catalog_metadata, skill_dir.name)
        published = catalog_metadata["published"]
        blocked_reason = catalog_metadata.get("blocked_reason")

        if published and "blocked_reason" in catalog_metadata:
            raise ValueError(
                f"Skill {skill_dir.name}: blocked_reason must be absent when published"
            )
        if not published and (
            not isinstance(blocked_reason, str) or not blocked_reason.strip()
        ):
            raise ValueError(
                f"Skill {skill_dir.name}: blocked_reason is required when unpublished"
            )

        files = None
        if published:
            files = [
                path.relative_to(skill_dir).as_posix()
                for path in self._visible_files(skill_dir)
            ]

        return Skill(
            name=frontmatter["name"],
            description=frontmatter["description"],
            version=catalog_metadata["version"],
            writes=catalog_metadata["writes"],
            reads_external=catalog_metadata["reads_external"],
            published=published,
            blocked_reason=blocked_reason,
            files=files,
        )

    @staticmethod
    def _parse_frontmatter(skill_file: Path) -> dict[str, str]:
        content = skill_file.read_text(encoding="utf-8")
        parts = content.split("---", maxsplit=2)
        if len(parts) != 3 or parts[0].strip():
            raise ValueError(f"Skill {skill_file.parent.name}: invalid frontmatter")

        metadata: dict[str, str] = {}
        for line in parts[1].splitlines():
            if not line.strip():
                continue
            if ":" not in line:
                raise ValueError(
                    f"Skill {skill_file.parent.name}: invalid frontmatter line"
                )
            key, value = line.split(":", maxsplit=1)
            metadata[key.strip()] = value.strip()
        return metadata

    @staticmethod
    def _parse_catalog_metadata(skill_dir: Path) -> dict[str, object]:
        metadata_file = skill_dir / CATALOG_METADATA_FILENAME
        if not metadata_file.is_file() or metadata_file.is_symlink():
            raise ValueError(f"Skill {skill_dir.name}: catalog metadata is missing")
        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Skill {skill_dir.name}: invalid catalog metadata JSON"
            ) from error
        if not isinstance(metadata, dict):
            raise TypeError(
                f"Skill {skill_dir.name}: catalog metadata must be a JSON object"
            )
        return metadata

    @staticmethod
    def _validate_frontmatter(metadata: dict[str, str], directory_name: str) -> None:
        missing = SKILL_FRONTMATTER_FIELDS - metadata.keys()
        if missing:
            fields = ", ".join(sorted(missing))
            raise ValueError(
                f"Skill {directory_name}: missing frontmatter fields: {fields}"
            )
        unsupported = metadata.keys() - SKILL_FRONTMATTER_FIELDS
        if unsupported:
            fields = ", ".join(sorted(unsupported))
            raise ValueError(
                f"Skill {directory_name}: unsupported frontmatter fields: {fields}"
            )
        if metadata["name"] != directory_name:
            raise ValueError(
                f"Skill {directory_name}: frontmatter name must match directory"
            )
        if not metadata["description"]:
            raise ValueError(f"Skill {directory_name}: description must not be empty")

    @staticmethod
    def _validate_catalog_metadata(
        metadata: dict[str, object], directory_name: str
    ) -> None:
        missing = REQUIRED_CATALOG_FIELDS - metadata.keys()
        if missing:
            fields = ", ".join(sorted(missing))
            raise ValueError(
                f"Skill {directory_name}: missing catalog metadata fields: {fields}"
            )
        unsupported = metadata.keys() - CATALOG_FIELDS
        if unsupported:
            fields = ", ".join(sorted(unsupported))
            raise ValueError(
                f"Skill {directory_name}: unsupported catalog metadata fields: {fields}"
            )

        version = metadata["version"]
        if (
            not isinstance(version, str)
            or re.fullmatch(r"\d{4}-\d{2}-\d{2}", version) is None
        ):
            raise ValueError(f"Skill {directory_name}: version must use YYYY-MM-DD")
        try:
            date.fromisoformat(version)
        except ValueError as error:
            raise ValueError(
                f"Skill {directory_name}: version must use YYYY-MM-DD"
            ) from error

        for field in ("writes", "reads_external", "published"):
            if not isinstance(metadata[field], bool):
                raise TypeError(
                    f"Skill {directory_name}: {field} must be a JSON boolean"
                )

    @staticmethod
    def _visible_files(skill_dir: Path) -> list[Path]:
        return sorted(
            (
                path
                for path in skill_dir.rglob("*")
                if path.is_file()
                and not SkillRepository._path_contains_symlink(path, skill_dir)
                and not any(
                    part.startswith(".") or part == "__pycache__"
                    for part in path.relative_to(skill_dir).parts
                )
            ),
            key=lambda path: path.relative_to(skill_dir).as_posix(),
        )

    @staticmethod
    def _path_contains_symlink(path: Path, root: Path) -> bool:
        relative_path = path.relative_to(root)
        return any(
            (root / Path(*relative_path.parts[:index])).is_symlink()
            for index in range(1, len(relative_path.parts) + 1)
        )

    @staticmethod
    def _write_skill_files(
        archive: ZipFile,
        skill_dir: Path,
        archive_root: Path,
        skill_filename: str = SKILL_FILENAME,
    ) -> None:
        for path in SkillRepository._visible_files(skill_dir):
            relative_path = path.relative_to(skill_dir)
            if relative_path == Path(SKILL_FILENAME):
                relative_path = Path(skill_filename)
            archive.write(path, arcname=str(archive_root / relative_path))
