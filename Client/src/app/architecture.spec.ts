/// <reference types="vite/client" />
/**
 * Architecture fitness functions — enforce layer boundaries at test time.
 *
 * Uses Vite's import.meta.glob to read source files at build time
 * and asserts that no layer imports from a forbidden layer.
 */

const importRegex = /from\s+['"]([^'"]+)['"]/g;

function extractImportPaths(content: string): string[] {
  const paths: string[] = [];
  let match: RegExpExecArray | null;
  while ((match = importRegex.exec(content)) !== null) {
    paths.push(match[1]);
  }
  importRegex.lastIndex = 0;
  return paths;
}

type Violation = { file: string; importPath: string };

function findViolations(
  files: Record<string, string>,
  forbidden: string[],
): Violation[] {
  const violations: Violation[] = [];
  for (const [file, content] of Object.entries(files)) {
    for (const imp of extractImportPaths(content)) {
      if (forbidden.some((f) => imp.includes(f))) {
        violations.push({ file, importPath: imp });
      }
    }
  }
  return violations;
}

function formatViolations(violations: Violation[]): string {
  if (violations.length === 0) return '';
  return '\n' + violations.map((v) => `  ${v.file}: ${v.importPath}`).join('\n');
}

// Load source files at build time via Vite glob imports
/* eslint-disable @typescript-eslint/no-explicit-any */
const serviceFiles = import.meta.glob(
  ['./services/*.ts', '!./services/*.spec.ts'],
  { query: '?raw', eager: true },
) as Record<string, any>;

const componentFiles = import.meta.glob(
  ['./components/**/*.ts', '!./components/**/*.spec.ts'],
  { query: '?raw', eager: true },
) as Record<string, any>;

const modelFiles = import.meta.glob('./models/*.ts', {
  query: '?raw',
  eager: true,
}) as Record<string, any>;

const guardFiles = import.meta.glob(
  ['./guards/*.ts', '!./guards/*.spec.ts'],
  { query: '?raw', eager: true },
) as Record<string, any>;

const interceptorFiles = import.meta.glob(
  ['./interceptors/*.ts', '!./interceptors/*.spec.ts'],
  { query: '?raw', eager: true },
) as Record<string, any>;
/* eslint-enable @typescript-eslint/no-explicit-any */

function toRawMap(globResult: Record<string, unknown>): Record<string, string> {
  const map: Record<string, string> = {};
  for (const [path, mod] of Object.entries(globResult)) {
    map[path] = typeof mod === 'string' ? mod : (mod as { default: string }).default;
  }
  return map;
}

describe('Architecture boundaries', () => {
  it('services must not import from pages or components', () => {
    const violations = findViolations(toRawMap(serviceFiles), ['/pages/', '/components/']);
    expect(violations, formatViolations(violations)).toEqual([]);
  });

  it('components must not import from pages', () => {
    const violations = findViolations(toRawMap(componentFiles), ['/pages/']);
    expect(violations, formatViolations(violations)).toEqual([]);
  });

  it('models must not import from services, pages, or components', () => {
    const violations = findViolations(toRawMap(modelFiles), [
      '/services/',
      '/pages/',
      '/components/',
    ]);
    expect(violations, formatViolations(violations)).toEqual([]);
  });

  it('guards and interceptors must not import from pages or components', () => {
    const guardViolations = findViolations(toRawMap(guardFiles), ['/pages/', '/components/']);
    const interceptorViolations = findViolations(toRawMap(interceptorFiles), [
      '/pages/',
      '/components/',
    ]);
    const all = [...guardViolations, ...interceptorViolations];
    expect(all, formatViolations(all)).toEqual([]);
  });
});
