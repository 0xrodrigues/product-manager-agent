import re

from app.models.story import RefinedStory


def number_items(items: list[str], prefix: str) -> list[str]:
    """Prefixa cada item com RF-01, RN-02, CA-03... ignorando itens já prefixados."""
    has_prefix = re.compile(rf"^{re.escape(prefix)}-\d+", re.IGNORECASE)
    numbered, counter = [], 1
    for item in items:
        if has_prefix.match(item):
            numbered.append(item)
        else:
            numbered.append(f"{prefix}-{counter:02d}: {item}")
            counter += 1
    return numbered


def format_story(story: RefinedStory) -> RefinedStory:
    """Retorna uma cópia da história com RF/RN/CA numerados sequencialmente."""
    return story.model_copy(update={
        "functional_requirements": number_items(story.functional_requirements, "RF"),
        "business_rules": number_items(story.business_rules, "RN"),
        "acceptance_criteria": number_items(story.acceptance_criteria, "CA"),
    })


def build_jira_description(story: RefinedStory) -> str:
    """Monta a descrição textual do ticket Jira a partir de uma história refinada."""
    formatted = format_story(story)
    return (
        formatted.user_story
        + "\n\nFunctional Requirements:\n"
        + "\n".join(f"- {fr}" for fr in formatted.functional_requirements)
        + "\n\nBusiness Rules:\n"
        + "\n".join(f"- {br}" for br in formatted.business_rules)
        + "\n\nAcceptance Criteria:\n"
        + "\n".join(f"- {ac}" for ac in formatted.acceptance_criteria)
    )
