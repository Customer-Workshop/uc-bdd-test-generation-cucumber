"""CLI entry point for the Test Case Generator Agent."""

import sys
from pathlib import Path

import click

from .gherkin_writer import GherkinWriter
from .parser import OpenAPIParser
from .strategy import TestStrategyEngine


@click.command()
@click.argument("spec_path", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    default="generated-tests",
    help="Output directory for generated .feature files.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print generated features to stdout without writing files.",
)
@click.option(
    "--tag-filter",
    default=None,
    help="Only generate tests for endpoints with this tag.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output.",
)
def main(
    spec_path: str,
    output: str,
    dry_run: bool,
    tag_filter: str | None,
    verbose: bool,
) -> None:
    """Generate Gherkin BDD test cases from an OpenAPI/Swagger specification.

    SPEC_PATH is the path to the OpenAPI/Swagger spec file (JSON or YAML).
    """
    click.echo(f"Parsing specification: {spec_path}")

    try:
        parser = OpenAPIParser(spec_path=spec_path)
    except Exception as e:
        click.echo(f"Error parsing specification: {e}", err=True)
        sys.exit(1)

    api_title = parser.get_title()
    endpoints = parser.get_endpoints()
    click.echo(f"API: {api_title}")
    click.echo(f"Found {len(endpoints)} endpoints")

    if verbose:
        for ep in endpoints:
            click.echo(f"  {ep.method:6s} {ep.path}")

    engine = TestStrategyEngine(parser)
    features = engine.generate_features()

    if tag_filter:
        features = [
            f for f in features if any(tag_filter in t for t in f.tags)
        ]

    total_scenarios = sum(len(f.scenarios) for f in features)
    click.echo(f"Generated {total_scenarios} test scenarios across {len(features)} features")

    writer = GherkinWriter(output_dir=output)

    if dry_run:
        for feature in features:
            click.echo("\n" + "=" * 60)
            click.echo(writer.render_feature(feature))
    else:
        paths = writer.write_all(features)
        click.echo(f"\nFeature files written to: {Path(output).resolve()}")
        for p in paths:
            click.echo(f"  {p.name}")

    click.echo("\nDone!")


if __name__ == "__main__":
    main()
