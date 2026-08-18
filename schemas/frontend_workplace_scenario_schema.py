from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class FrontendEmail(BaseModel):
    id: str
    sender_name: str
    sender_title: str
    sender_email: str
    subject: str
    body: str
    priority: Literal["critical", "high", "medium", "low"]
    linked_ticket_id: str | None = None


class FrontendProjectFile(BaseModel):
    path: str
    content: str = Field(max_length=20_000)

    @field_validator("path")
    @classmethod
    def safe_path(cls, value: str) -> str:
        normalized = value.replace("\\", "/").strip()
        if not normalized or normalized.startswith("/") or ".." in normalized.split("/"):
            raise ValueError("Project paths must be safe relative paths.")
        if not normalized.endswith((".html", ".css", ".js", ".json", ".md")):
            raise ValueError("Unsupported frontend project file type.")
        return normalized


class FrontendProject(BaseModel):
    display_name: str
    name: str
    archive_name: str
    default_branch: Literal["main"] = "main"
    files: list[FrontendProjectFile] = Field(min_length=4, max_length=10)

    @model_validator(mode="after")
    def unique_paths(self):
        paths = [item.path for item in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError("Project file paths must be unique.")
        if not {"index.html", "styles.css", "product.js", "package.json"}.issubset(paths):
            raise ValueError("Frontend project is missing required files.")
        return self


class FrontendTaskDefinition(BaseModel):
    step: int = Field(ge=1, le=5)
    application: Literal["mail", "browser", "vscode", "testing", "github"]
    title: str
    instructions: str
    required_actions: list[str] = Field(min_length=1)


class FrontendPublicScenario(BaseModel):
    scenario_id: str
    scenario_kind: Literal["frontend_workplace"] = "frontend_workplace"
    issue_id: str
    title: str
    company_name: str
    fictional_company_notice: str
    advisor: dict
    task: dict
    background_emails: list[FrontendEmail] = Field(min_length=4, max_length=4)
    inbox_emails: list[FrontendEmail] = Field(min_length=5, max_length=5)
    project: FrontendProject
    resources: list[dict]
    skill_targets: list[str]
    frontend_tasks: list[FrontendTaskDefinition] = Field(min_length=5, max_length=5)
    allowed_terminal_commands: list[Literal["help", "clear", "npm test", "npm run lint", "npm run build", "git diff"]]
    viewport_presets: dict[str, int]

    @model_validator(mode="after")
    def coherent_scenario(self):
        if [task.step for task in self.frontend_tasks] != [1, 2, 3, 4, 5]:
            raise ValueError("Frontend tasks must contain ordered steps 1 through 5.")
        if len({email.id for email in self.inbox_emails}) != 5:
            raise ValueError("Inbox email IDs must be unique.")
        urgent = [email for email in self.inbox_emails if email.priority == "critical"]
        if len(urgent) != 1 or urgent[0].linked_ticket_id != self.issue_id:
            raise ValueError("Exactly one critical email must reference the scenario issue.")
        return self


class FrontendPrivateContext(BaseModel):
    root_cause: str
    expected_patch: dict[str, str]
    acceptable_alternatives: list[str]
    verification_expectations: list[str]
    scoring_notes: dict[str, str]

    @field_validator("expected_patch")
    @classmethod
    def firebase_safe_patch_keys(cls, value: dict[str, str]) -> dict[str, str]:
        forbidden = {".", "#", "$", "/", "[", "]"}
        if any(not key or any(character in key for character in forbidden) for key in value):
            raise ValueError("Expected-patch identifiers must be Firebase-safe keys.")
        return value


class FrontendWorkplaceScenario(BaseModel):
    public_scenario: FrontendPublicScenario
    private_context: FrontendPrivateContext
