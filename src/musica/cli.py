"""Command-line interface for Musica."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from musica.instruments import list_instruments, ENSEMBLES


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s | %(name)s | %(message)s",
        stream=sys.stderr,
    )


@click.command()
@click.argument("url")
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    default=Path("output"),
    show_default=True,
    help="Output directory for the generated MusicXML.",
)
@click.option(
    "-i", "--instrument",
    type=str,
    default=None,
    help=(
        "Target instrument (e.g. cello, violin, guitar). "
        "If omitted, all detected stems are assigned default instruments."
    ),
)
@click.option(
    "-e", "--ensemble",
    type=str,
    multiple=True,
    help=(
        "Instruments for an ensemble score. Repeat for each part, e.g. "
        "-e violin -e violin -e viola -e cello. "
        "Or use --preset for named ensembles."
    ),
)
@click.option(
    "--preset",
    type=click.Choice(sorted(ENSEMBLES.keys()), case_sensitive=False),
    default=None,
    help="Use a named ensemble preset (e.g. string_quartet).",
)
@click.option(
    "-t", "--title",
    type=str,
    default=None,
    help="Title for the score. Defaults to 'Untitled'.",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    default=False,
    help="Enable debug-level logging.",
)
@click.option(
    "--list-instruments",
    "show_instruments",
    is_flag=True,
    default=False,
    help="Print available instruments and exit.",
)
@click.option(
    "--list-ensembles",
    "show_ensembles",
    is_flag=True,
    default=False,
    help="Print available ensemble presets and exit.",
)
def main(
    url: str,
    output: Path,
    instrument: str | None,
    ensemble: tuple[str, ...],
    preset: str | None,
    title: str | None,
    verbose: bool,
    show_instruments: bool,
    show_ensembles: bool,
) -> None:
    """Musica — generate MuseScore partitures from a YouTube URL.

    URL is a YouTube video link (or path to a local .mp4/.wav file).

    \b
    Examples:
      musica "https://youtube.com/watch?v=abc123"
      musica "https://youtube.com/watch?v=abc123" -i cello
      musica "https://youtube.com/watch?v=abc123" -e violin -e viola -e cello
      musica "https://youtube.com/watch?v=abc123" --preset string_quartet
    """
    if show_instruments:
        click.echo("Available instruments:")
        for name in list_instruments():
            click.echo(f"  {name}")
        return

    if show_ensembles:
        click.echo("Available ensemble presets:")
        for name, parts in sorted(ENSEMBLES.items()):
            click.echo(f"  {name}: {', '.join(parts)}")
        return

    _setup_logging(verbose)

    # Resolve ensemble from preset or explicit flags
    ensemble_list: list[str] | None = None
    if preset:
        from musica.instruments import ENSEMBLES as ens
        ensemble_list = ens[preset]
    elif ensemble:
        ensemble_list = list(ensemble)

    if instrument and ensemble_list:
        raise click.UsageError(
            "Cannot use --instrument together with --ensemble/--preset. Choose one."
        )

    from musica.pipeline import run

    result = run(
        url=url,
        output_dir=output,
        instrument=instrument,
        ensemble=ensemble_list,
        title=title,
    )

    click.echo(f"\nPartiture written to: {result}")
    click.echo("Open it in MuseScore to view, edit, and print.")


if __name__ == "__main__":
    main()
