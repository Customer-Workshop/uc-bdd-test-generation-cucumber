"""Gherkin feature file writer.

Renders TestFeature objects into properly formatted .feature files
compatible with the Spring Cucumber REST API BDD framework.
"""

from pathlib import Path

from .strategy import TestFeature, TestScenario


class GherkinWriter:
    """Writes TestFeature objects to Gherkin .feature files."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_feature(self, feature: TestFeature) -> Path:
        filename = self._feature_name_to_filename(feature.name)
        filepath = self.output_dir / filename
        content = self.render_feature(feature)
        filepath.write_text(content, encoding="utf-8")
        return filepath

    def write_all(self, features: list[TestFeature]) -> list[Path]:
        return [self.write_feature(feature) for feature in features]

    def render_feature(self, feature: TestFeature) -> str:
        lines: list[str] = []

        if feature.tags:
            lines.append(" ".join(feature.tags))

        lines.append(f"Feature: {feature.name}")
        if feature.description:
            lines.append(f"  {feature.description}")
        lines.append("")

        if feature.background_steps:
            lines.append("  Background:")
            for step in feature.background_steps:
                lines.append(f"    {step['keyword']} {step['text']}")
            lines.append("")

        for i, scenario in enumerate(feature.scenarios):
            lines.extend(self._render_scenario(scenario))
            if i < len(feature.scenarios) - 1:
                lines.append("")

        lines.append("")
        return "\n".join(lines)

    def _render_scenario(self, scenario: TestScenario) -> list[str]:
        lines: list[str] = []

        if scenario.tags:
            lines.append(f"  {' '.join(scenario.tags)}")

        lines.append(f"  Scenario: {scenario.name}")
        if scenario.description:
            lines.append(f"    # {scenario.description}")

        for step in scenario.steps:
            text = step["text"]
            if "\n" in text:
                first_line, rest = text.split("\n", 1)
                lines.append(f"    {step['keyword']} {first_line}")
                for sub_line in rest.split("\n"):
                    lines.append(f"    {sub_line}")
            else:
                lines.append(f"    {step['keyword']} {text}")

        return lines

    def _feature_name_to_filename(self, name: str) -> str:
        safe = (
            name.lower()
            .replace(" - ", "-")
            .replace(" ", "-")
            .replace("/", "-")
        )
        safe = "".join(c for c in safe if c.isalnum() or c in "-_")
        if len(safe) > 80:
            safe = safe[:80]
        return f"{safe}.feature"
