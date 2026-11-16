"""Substantive quality checks for workplace assignments.

The structural validator only proves a scenario has the right shape. These
checks look at substance: a README people can work from, connected modules
with existing behaviour to preserve, tests that exercise the code, evidence
worth investigating, requirements grounded in the project, a private rubric
that covers every requirement, and proof that the starter project does not
already satisfy the assignment. No single size number decides the result.

Every check returns readable problems so a rejected generation can be retried
with concrete feedback.
"""

import posixpath
import re
from typing import Any

README_SECTIONS = {
    "overview": r"overview|about|purpose|what (?:this|the)|introduction|summary",
    "structure": r"structure|layout|modules|architecture|components|files|organi[sz]ation",
    "behaviour": r"behavio|expected|api|endpoints?|usage|contract|features|how it works|interface",
    "data": r"data|fixtures?|samples?|resources|evidence|seed",
    "verification": r"verif|testing|tests|quality|checks",
    "deliverables": r"deliverables?|hand-?over|submission|definition of done|handing",
}
README_SECTION_EXAMPLES = {
    "overview": "## Overview",
    "structure": "## Project structure",
    "behaviour": "## Expected behaviour",
    "data": "## Sample data and resources",
    "verification": "## Verification",
    "deliverables": "## Deliverables and handover",
}
MIN_SECTION_WORDS = 20
ENVIRONMENT_LIMITATION = re.compile(
    r"cannot (?:run|execute)|can ?not (?:run|execute)|does not (?:run|execute)|"
    r"not (?:be )?(?:run|executed)|no (?:code|test) execution|outside (?:of )?(?:careergrid|this workspace|the workspace)|"
    r"\bci\b|continuous integration|local (?:python|node|development) environment|external environment|your own machine",
    re.IGNORECASE,
)
RUNS_IN_WORKSPACE = re.compile(
    r"run (?:the )?tests? (?:in|from|inside|using) (?:the )?(?:careergrid|simulated|workspace|built-in)|"
    r"(?:in|from) (?:the )?(?:careergrid|simulated) terminal,? run",
    re.IGNORECASE,
)
EDGE_CASE_TERMS = re.compile(
    r"invalid|empty|missing|duplicate|unsupported|boundar|limit|zero|negative|null|none|"
    r"malformed|concurren|retr(?:y|ies)|timeout|expired|unknown|out[- ]of[- ]range|"
    r"deactivated|deleted|disabled|keyboard|small screen|mobile|repeated|twice|"
    r"non-?existent|does not exist|not found|unauthori[sz]ed|forbidden|does not belong|another user|"
    r"\bpast\b|exceed|overlap|conflict|outside|whitespace|too (?:long|large|many|short)",
    re.IGNORECASE,
)
PRESERVE_TERMS = re.compile(
    r"preserv|existing|unchanged|still|continue|backward|regression|without breaking|keep",
    re.IGNORECASE,
)
STOPWORDS = {
    "that", "this", "with", "from", "into", "when", "they", "their", "there", "should",
    "must", "only", "also", "have", "will", "each", "than", "then", "were", "been",
    "does", "other", "make", "sure", "ensure", "return", "returns", "using", "user",
    "users", "data", "about", "which", "what", "where", "after", "before", "while",
}

CODE_EXTENSIONS = {".py", ".js", ".ts", ".mjs"}
PY_DEFINITION = re.compile(r"^\s*(?:async\s+)?def\s+\w+|^\s*class\s+\w+", re.MULTILINE)
JS_DEFINITION = re.compile(
    r"\bfunction\s+\w+|\b(?:const|let|var)\s+\w+\s*=\s*(?:async\s*)?(?:function\b|\([^)]*\)\s*=>|\w+\s*=>)|"
    r"^\s*(?:export\s+)?class\s+\w+|"
    # Object-literal and class methods: `validateEmail(value) {` or `save: function () {`.
    r"^\s*(?:async\s+)?(?!(?:if|for|while|switch|catch|return|function)\b)[A-Za-z_$][\w$]*\s*\([^)]*\)\s*\{|"
    r"^\s*[A-Za-z_$][\w$]*\s*:\s*(?:async\s+)?(?:function\b|\([^)]*\)\s*=>|[A-Za-z_$][\w$]*\s*=>)",
    re.MULTILINE,
)
PY_TEST_CASE = re.compile(r"^\s*(?:async\s+)?def\s+test_\w+", re.MULTILINE)
JS_TEST_CASE = re.compile(r"\b(?:test|it)\s*\(\s*['\"`]")
PY_IMPORT = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE)
# Wording that makes a pull request mandatory. Mentioning PRs as one option is fine.
PR_ONLY = re.compile(
    r"\b(?:must|should|please|required to|need to)\s+(?:open|create|submit|raise|use)\s+(?:a\s+)?(?:pull request|PR)\b"
    r"(?![^.]*\bor\b)",  # "open a pull request or push to main" offers a choice
    re.IGNORECASE,
)
DIFF_MARKERS = re.compile(r"^(?:diff --git |@@ -\d+(?:,\d+)? \+\d+|--- a/|\+\+\+ b/)", re.MULTILINE)
CODE_LIKE = re.compile(r"[()]|==|!=|<=|>=|\bif\s|\breturn\s|\.get\(|\bnot in\b|=>")
GENERIC_TITLE = re.compile(
    r"^\s*(?:junior|senior|lead|mid-level)?\s*(?:backend|back-end|frontend|front-end|software|web|full[- ]?stack)?\s*"
    r"(?:developer|engineer)\s*(?:task|assignment)?\s*$",
    re.IGNORECASE,
)
JS_IMPORT = re.compile(r"(?:from\s+|require\(\s*|import\s*\(\s*)['\"](\.{1,2}/[^'\"]+)['\"]")
HTML_SCRIPT = re.compile(r"<script[^>]+src=['\"]([^'\"]+)['\"]", re.IGNORECASE)


def _extension(path: str) -> str:
    return posixpath.splitext(path)[1].lower()


def is_test_file(path: str) -> bool:
    name = posixpath.basename(path).lower()
    return (
        path.lower().startswith(("tests/", "test/", "__tests__/"))
        or name.startswith("test_")
        or re.search(r"[._-](?:test|spec)\.[a-z]+$", name) is not None
        or name.endswith("_test.py")
    )


def _definitions(path: str, content: str) -> int:
    pattern = PY_DEFINITION if _extension(path) == ".py" else JS_DEFINITION
    return len(pattern.findall(content))


def _test_cases(path: str, content: str) -> int:
    pattern = PY_TEST_CASE if _extension(path) == ".py" else JS_TEST_CASE
    return len(pattern.findall(content))


def _resolve_python(module: str, files: set[str], source: str = "") -> str | None:
    if module.startswith("."):
        level = len(module) - len(module.lstrip("."))
        base = posixpath.dirname(source)
        for _ in range(level - 1):
            base = posixpath.dirname(base)
        candidate = posixpath.join(base, module.lstrip(".").replace(".", "/")) if module.lstrip(".") else base
    else:
        candidate = module.replace(".", "/")
    for path in (f"{candidate}.py", f"{candidate}/__init__.py"):
        if path in files:
            return path
    return None


# Names after `from X import`: a parenthesised list may span lines, a plain one may not.
PY_FROM_IMPORT_NAMES = re.compile(r"^[ \t]*from[ \t]+([\w.]+)[ \t]+import[ \t]+(?:\(([\w\s,]+)\)|([\w \t,]+))", re.MULTILINE)


def _resolve_relative(source: str, target: str, files: set[str]) -> str | None:
    base = posixpath.dirname(source)
    joined = posixpath.normpath(posixpath.join(base, target))
    for path in (joined, f"{joined}.js", f"{joined}.ts", f"{joined}/index.js"):
        if path in files:
            return path
    return None


def project_edges(files: dict[str, str]) -> set[tuple[str, str]]:
    """Return (importer, imported) pairs between project files."""

    paths = set(files)
    edges = set()
    for path, content in files.items():
        extension = _extension(path)
        targets = []
        if extension == ".py":
            for groups in PY_IMPORT.findall(content):
                for module in groups:
                    if module:
                        targets.append(_resolve_python(module, paths, path))
            # `from package import module` imports the module file itself.
            for module, grouped, plain in PY_FROM_IMPORT_NAMES.findall(content):
                for name in re.split(r"[\s,]+", grouped or plain):
                    if name:
                        joined = f"{module}{name}" if module.endswith(".") else f"{module}.{name}"
                        targets.append(_resolve_python(joined, paths, path))
        elif extension in CODE_EXTENSIONS:
            targets = [_resolve_relative(path, target, paths) for target in JS_IMPORT.findall(content)]
        elif extension == ".html":
            targets = [_resolve_relative(path, f"./{src.lstrip('./')}", paths) for src in HTML_SCRIPT.findall(content)]
        for target in targets:
            if target and target != path:
                edges.add((path, target))
    return edges


def unused_modules(files: dict[str, str]) -> list[str]:
    """Source modules that no file imports or loads and that import nothing.

    Such a module plays no part in the project's behaviour (for example a
    models.py nobody uses), so it is filler. Entry points such as app.py import
    other modules, and package markers (__init__.py) are exempt.
    """

    edges = project_edges(files)
    touched = {path for edge in edges for path in edge}
    return sorted(
        path for path in files
        if _extension(path) in CODE_EXTENSIONS and not is_test_file(path)
        and posixpath.basename(path) != "__init__.py" and path not in touched
    )


def readme_sections(readme: str) -> dict[str, str]:
    """Split Markdown into heading -> body text."""

    sections: dict[str, str] = {}
    current = None
    for line in readme.splitlines():
        heading = re.match(r"^#{2,4}\s+(.+?)\s*#*\s*$", line)
        if heading:
            current = heading.group(1).strip()
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return sections


def _words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9_`'/.-]+", text))


def _significant_tokens(text: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z][a-z0-9_]{3,}", text.lower())
        if token not in STOPWORDS
    }


def condition_passes(condition: dict[str, Any], files: dict[str, str]) -> bool:
    content = files.get(condition.get("file", ""), "")
    if not content:
        return False
    include_all = condition.get("must_include_all") or []
    include_any = condition.get("must_include_any") or []
    exclude = condition.get("must_not_include") or []
    return (
        all(pattern in content for pattern in include_all)
        and (not include_any or any(pattern in content for pattern in include_any))
        and not any(pattern in content for pattern in exclude)
    )


def check_passes(check: dict[str, Any], files: dict[str, str]) -> bool:
    return any(condition_passes(condition, files) for condition in check.get("any_of", []))


def _check_readme(readme: str, files: dict[str, str], task: dict[str, Any]) -> list[str]:
    problems = []
    if not readme.strip():
        return ["README.md is missing or empty."]
    sections = readme_sections(readme)
    found = {}
    for key, pattern in README_SECTIONS.items():
        match = next((title for title in sections if re.search(pattern, title, re.IGNORECASE)), None)
        if match is None:
            problems.append(f"README needs a '{key}' section, for example '{README_SECTION_EXAMPLES[key]}'.")
        elif _words(sections[match]) < MIN_SECTION_WORDS:
            problems.append(f"README section '{match}' is too thin to be useful.")
        else:
            found[key] = sections[match]
    if "```" not in readme:
        problems.append("README needs at least one concrete input/output example in a fenced code block.")
    relevant = [path for path in files if _extension(path) in CODE_EXTENSIONS or _extension(path) == ".html"]
    mentioned = [
        path for path in relevant
        if path in readme or posixpath.basename(path) in readme
    ]
    if relevant and len(mentioned) < 0.6 * len(relevant):
        problems.append("README project-structure section must describe the project's modules and tests by name.")
    verification = found.get("verification", "")
    if verification and not ENVIRONMENT_LIMITATION.search(verification):
        problems.append(
            "README verification section must state that tests cannot run inside CareerGrid "
            "and explain where they would run (for example CI or a local environment)."
        )
    if RUNS_IN_WORKSPACE.search(readme):
        problems.append("README must not claim tests can run in the CareerGrid workspace.")
    deliverables = found.get("deliverables", "")
    task_deliverables = task.get("deliverables") or []
    if deliverables and task_deliverables:
        readme_tokens = _significant_tokens(deliverables)
        aligned = sum(bool(_significant_tokens(item) & readme_tokens) for item in task_deliverables)
        if aligned < (len(task_deliverables) + 1) // 2:
            problems.append("README deliverables section must match the deliverables in the task email.")
    return problems


def _check_depth(files: dict[str, str]) -> list[str]:
    problems = []
    sources = {
        path: content for path, content in files.items()
        if _extension(path) in CODE_EXTENSIONS and not is_test_file(path)
    }
    tests = {
        path: content for path, content in files.items()
        if _extension(path) in CODE_EXTENSIONS and is_test_file(path)
    }
    substantive = [path for path, content in sources.items() if _definitions(path, content) >= 1]
    total_definitions = sum(_definitions(path, content) for path, content in sources.items())
    if len(substantive) < 3:
        problems.append("The project needs at least three source modules with real responsibilities.")
    if total_definitions < 8:
        problems.append("The source modules contain too little existing behaviour to investigate and preserve.")
    edges = project_edges(files)
    source_edges = {edge for edge in edges if edge[0] in sources or _extension(edge[0]) == ".html"}
    if len({target for _, target in source_edges if target in sources}) < 2:
        problems.append("Modules must be connected (imports or script references) so behaviour has to be traced across files.")
    for path in unused_modules(files):
        problems.append(f"{path} is not imported or loaded by any other file; connect it to the project or leave it out.")
    if not tests:
        problems.append("The project needs existing tests that demonstrate current behaviour.")
    else:
        usable = [
            path for path, content in tests.items()
            if _test_cases(path, content) >= 2 and any(source == path and target in sources for source, target in edges)
        ]
        if not usable:
            problems.append("Existing tests must import the project code and contain at least two test cases.")
    return problems


def _check_evidence(public: dict[str, Any], readme: str) -> list[str]:
    problems = []
    resources = [item for item in public.get("resources", []) if isinstance(item, dict)]
    useful = [
        item for item in resources
        if len([line for line in str(item.get("content", "")).splitlines() if line.strip()]) >= 4
        or _words(str(item.get("content", ""))) >= 40
    ]
    if len(useful) < 2:
        problems.append("Provide at least two useful evidence resources (logs, tickets, sample requests, fixtures, or messages).")
    task_text = f"{public['task'].get('body', '')} {readme}"
    if resources and not any(
        str(item.get("name", "")) in task_text or str(item.get("id", "")) in task_text for item in resources
    ):
        problems.append("The task email or README must point the participant to the evidence resources.")
    return problems


def _check_assignment(public: dict[str, Any], corpus: str, kinds: list[str] | None = None) -> list[str]:
    problems = []
    task = public["task"]
    requirements = [str(item) for item in task.get("requirements") or []]
    criteria = [str(item) for item in task.get("acceptance_criteria") or []]
    if len(requirements) < 3:
        problems.append("The assignment needs at least three related requirements.")
    if GENERIC_TITLE.match(str(public.get("title") or "")):
        problems.append("The title must name the work (for example 'Reject overlapping clinic bookings'), not the role.")
    delivery = " ".join(requirements + criteria + [str(item) for item in task.get("deliverables") or []] + [str(task.get("body") or "")])
    if PR_ONLY.search(delivery):
        problems.append(
            "Do not require a pull request: participants may deliver through a pull request or a push to main, "
            "and hand over in the reply email."
        )
    joined = " ".join(requirements + criteria)
    # Paired drafts declare each requirement's kind; keywords are the fallback.
    kinds = set(kinds or [])
    if "edge_case" not in kinds and not EDGE_CASE_TERMS.search(joined):
        problems.append("Requirements or acceptance criteria must include explicit edge cases.")
    if "preserve" not in kinds and not PRESERVE_TERMS.search(joined):
        problems.append("Requirements must state existing behaviour that has to be preserved.")
    corpus_tokens = _significant_tokens(corpus)
    for requirement in requirements:
        if not _significant_tokens(requirement) & corpus_tokens:
            problems.append(f"Requirement is not grounded in the project or evidence: {requirement[:80]}")
    return problems


def _check_solution_disclosure(public: dict[str, Any], private: dict[str, Any]) -> list[str]:
    """Reject public text that hands over the fix: a diff, or the exact code a
    correct solution adds. Naming files, modules, or endpoints is allowed, as
    real tickets do; only the change itself is private."""

    task = public.get("task") or {}
    texts = {
        "the task email": " ".join([str(task.get("body") or ""), *[str(item) for item in task.get("requirements") or []],
                                    *[str(item) for item in task.get("acceptance_criteria") or []]]),
        **{f"evidence {item.get('name')}": str(item.get("content") or "") for item in public.get("resources") or []},
        **{
            item["path"]: str(item.get("content") or "")
            for item in (public.get("project") or {}).get("files") or []
            if str(item.get("path") or "").endswith(".md")
        },
    }
    problems = [f"{where} contains a patch (diff); describe the expected behaviour instead."
                for where, text in texts.items() if DIFF_MARKERS.search(text)]
    solution_strings = set()
    for check in [*(private.get("starter_gap_checks") or []), *(private.get("patch_checks") or [])]:
        for condition in check.get("any_of") or [] if isinstance(check, dict) else []:
            for key in ("must_include_any", "must_include_all"):
                solution_strings.update(
                    value for value in condition.get(key) or []
                    if isinstance(value, str) and len(value) >= 8 and CODE_LIKE.search(value)
                )
    for where, text in texts.items():
        for value in sorted(solution_strings):
            if value in text:
                problems.append(f"{where} contains the exact code a solution adds ({value!r}); keep the fix private.")
                break
    return problems


def _check_backend_rubric(private: dict[str, Any], public: dict[str, Any], files: dict[str, str]) -> list[str]:
    problems = []
    requirement_count = len(public["task"].get("requirements") or [])
    covered: set[int] = set()
    for item in private.get("assessment_criteria") or []:
        if not isinstance(item, dict):
            continue
        paths = item.get("files")
        refs = item.get("requirement_refs")
        if not isinstance(paths, list) or not paths or any(path not in files and not is_test_file(path) for path in paths):
            problems.append(f"Assessment criterion '{item.get('id')}' must list existing project files.")
        if not isinstance(refs, list) or not refs or any(
            not isinstance(ref, int) or not 1 <= ref <= requirement_count for ref in refs
        ):
            problems.append(f"Assessment criterion '{item.get('id')}' must reference requirement numbers.")
        else:
            covered.update(refs)
    missing = set(range(1, requirement_count + 1)) - covered
    if missing:
        problems.append(f"Requirements {sorted(missing)} are not covered by any assessment criterion.")
    changes = [item for item in private.get("expected_changes") or [] if isinstance(item, dict)]
    changed_paths = {item.get("path") for item in changes}
    if len(changed_paths) < 2:
        problems.append("The assignment should need coordinated changes in at least two files.")
    if not any(is_test_file(str(path)) for path in changed_paths):
        problems.append("Expected changes must include adding or updating regression tests.")
    problems += _check_starter_gaps(private.get("starter_gap_checks"), files, changed_paths)
    return problems


def _check_starter_gaps(checks: Any, files: dict[str, str], changed_paths: set) -> list[str]:
    if not isinstance(checks, list) or len(checks) < 2:
        return ["Private context needs at least two starter_gap_checks."]
    problems = []
    for check in checks:
        if not isinstance(check, dict) or not isinstance(check.get("any_of"), list) or not check["any_of"]:
            problems.append("Every starter gap check needs any_of conditions.")
            continue
        conditions = check["any_of"]
        if any(not isinstance(condition, dict) or condition.get("file") not in files for condition in conditions):
            problems.append(f"Starter gap check '{check.get('id')}' refers to a missing file.")
            continue
        if not any(condition.get("file") in changed_paths for condition in conditions):
            problems.append(f"Starter gap check '{check.get('id')}' must target a file the assignment changes.")
        if not any(
            condition.get("must_include_all") or condition.get("must_include_any") or condition.get("must_not_include")
            for condition in conditions
        ):
            problems.append(f"Starter gap check '{check.get('id')}' has no patterns.")
        elif check_passes(check, files):
            found = "; ".join(
                f"{condition.get('file')} already contains one of "
                f"{list(condition.get('must_include_any') or condition.get('must_include_all') or [])[:3]}"
                for condition in conditions
            )
            problems.append(
                f"The starter project already satisfies '{check.get('id')}' ({found}). Either the starter already "
                "meets that requirement, or the check needs strings that only a correct solution adds."
            )
    return problems


def _check_frontend_rubric(private: dict[str, Any], files: dict[str, str]) -> list[str]:
    checks = private.get("patch_checks") or []
    failing = [check for check in checks if isinstance(check, dict) and not check_passes(check, files)]
    if len(failing) < 2:
        return ["At least two patch checks must fail on the starter project, so the work is substantive."]
    return []


def assignment_quality_problems(scenario: dict[str, dict[str, Any]], *, kind: str) -> list[str]:
    """Return every substantive quality problem in a scenario (empty if fine)."""

    public = scenario["public_scenario"]
    private = scenario["private_context"]
    files = {item["path"]: item["content"] for item in public["project"]["files"]}
    readme = files.get("README.md", "")
    corpus = " ".join(
        [*files.values(), *(str(item.get("content", "")) for item in public.get("resources", []))]
    )
    problems = []
    problems += _check_readme(readme, files, public["task"])
    problems += _check_depth(files)
    problems += _check_evidence(public, readme)
    problems += _check_assignment(public, corpus, private.get('requirement_kinds'))
    problems += _check_solution_disclosure(public, private)
    if kind == "backend":
        problems += _check_backend_rubric(private, public, files)
    else:
        problems += _check_frontend_rubric(private, files)
    return problems


def quality_signals(scenario: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Describe a scenario's size and shape for review (not a pass/fail gate)."""

    public = scenario["public_scenario"]
    files = {item["path"]: item["content"] for item in public["project"]["files"]}
    sources = [path for path in files if _extension(path) in CODE_EXTENSIONS and not is_test_file(path)]
    tests = [path for path in files if _extension(path) in CODE_EXTENSIONS and is_test_file(path)]
    return {
        "files": len(files),
        "source_modules": len(sources),
        "definitions": sum(_definitions(path, files[path]) for path in sources),
        "module_links": len(project_edges(files)),
        "test_cases": sum(_test_cases(path, files[path]) for path in tests),
        "readme_sections": list(readme_sections(files.get("README.md", ""))),
        "resources": len(public.get("resources", [])),
        "requirements": len(public["task"].get("requirements") or []),
    }
