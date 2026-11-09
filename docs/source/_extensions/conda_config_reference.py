# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""Sphinx directive ``conda-config-reference`` for the configuration reference.

The directive renders every documented setting of ``conda.base.context.context``
as a native ``confval`` entry, grouped by category, preceded by a summary table
per category. Facts that come from code (type, default, aliases, environment
variables, description) are generated; hand-written additions (examples, notes,
version history, legacy anchors) live in ``config_overrides.yml`` next to this
extension.

Descriptions in ``Context.get_descriptions()`` are treated as Markdown.

Usage::

    .. conda-config-reference::
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

if TYPE_CHECKING:
    from typing import Any

    from docutils import nodes
    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata

log = logging.getLogger(__name__)

HIDDEN_CATEGORIES = ("CLI-only", "Hidden and Undocumented")
OVERRIDES_PATH = Path(__file__).with_name("config_overrides.yml")
SUMMARY_MAX_DEFAULT_LENGTH = 40
SUMMARY_MAX_LENGTH = 160

OVERRIDE_KEYS = {
    "summary",
    "example",
    "notes",
    "added_in",
    "changed_in",
    "deprecated",
    "labels",
    "seealso",
}


@dataclass
class SettingRecord:
    """Everything the page needs to know about one setting."""

    name: str
    category: str
    kind: str
    type_label: str
    default: str
    aliases: tuple[str, ...]
    env_vars: tuple[str, ...]
    string_delimiter: str | None
    expandvars: bool
    description: str
    override: dict[str, Any] = field(default_factory=dict)

    @property
    def deprecated(self) -> bool:
        return "deprecated" in self.override

    @property
    def settable_from_env(self) -> bool:
        return self.kind != "map"

    @property
    def summary(self) -> str:
        return self.override.get("summary") or first_sentence(self.description)


def first_sentence(text: str, max_length: int = SUMMARY_MAX_LENGTH) -> str:
    """Return the first sentence of the first paragraph, on a single line."""
    paragraph = " ".join(text.strip().split("\n\n", 1)[0].split())
    # sentence ends at a period followed by whitespace; avoids "e.g." / "i.e."
    match = re.search(r"(?<!\be\.g)(?<!\bi\.e)\.(?=\s|$)", paragraph)
    sentence = paragraph[: match.end()] if match else paragraph
    if len(sentence) > max_length:
        sentence = sentence[: max_length - 1].rstrip() + "…"
    return sentence


def format_default(value: Any) -> str:
    """Render a default value as it would be written in a ``.condarc`` file."""
    if isinstance(value, Enum):
        return str(value.value)
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (tuple, list)):
        return "[" + ", ".join(format_default(item) for item in value) + "]"
    if isinstance(value, Mapping):
        if not value:
            return "{}"
        return (
            "{" + ", ".join(f"{k}: {format_default(v)}" for k, v in value.items()) + "}"
        )
    if isinstance(value, str):
        return f'"{value}"' if value == "" or value != value.strip() else value
    return str(value)


def load_overrides(path: Path = OVERRIDES_PATH) -> dict[str, dict[str, Any]]:
    """Load curated per-setting additions; empty if the file does not exist."""
    if not path.is_file():
        return {}
    from ruamel.yaml import YAML

    data = YAML(typ="safe").load(path.read_text()) or {}
    return dict(data)


def build_records(
    context: Any | None = None,
    overrides: dict[str, dict[str, Any]] | None = None,
) -> dict[str, list[SettingRecord]]:
    """Build the documented settings grouped by category (in display order).

    Args:
        context: Object providing ``category_map``, ``describe_parameter``,
            ``describe_parameter_sources`` and ``get_descriptions``. Defaults to
            ``conda.base.context.context``.
        overrides: Curated additions keyed by setting name. Defaults to the
            contents of ``config_overrides.yml``.

    Returns:
        Mapping of category to its records; deprecated settings sort last within
        each category, the rest alphabetically. Hidden categories are skipped.
    """
    if context is None:
        from conda.base.context import context
    if overrides is None:
        overrides = load_overrides()

    descriptions = context.get_descriptions()
    grouped: dict[str, list[SettingRecord]] = {}
    for category, names in context.category_map.items():
        if category in HIDDEN_CATEGORIES:
            continue
        records = []
        for name in names:
            details = context.describe_parameter(name)
            sources = context.describe_parameter_sources(name)
            records.append(
                SettingRecord(
                    name=details["name"],
                    category=category,
                    kind=details["parameter_type"],
                    type_label=sources["value_type"],
                    default=format_default(details["default_value"]),
                    aliases=tuple(details["aliases"]),
                    env_vars=tuple(sources["env_vars"]),
                    string_delimiter=sources.get("string_delimiter"),
                    expandvars=sources["expandvars"],
                    description=descriptions.get(details["name"], "").strip(),
                    override=dict(overrides.get(details["name"], {})),
                )
            )
        records.sort(key=lambda r: (r.deprecated, r.name))
        grouped[category] = records
    return grouped


def validate_records(
    grouped: dict[str, list[SettingRecord]],
    overrides: dict[str, dict[str, Any]],
) -> list[str]:
    """Return human-readable problems (empty list when everything is consistent)."""
    problems = []
    names = [r.name for records in grouped.values() for r in records]
    for name in sorted({n for n in names if names.count(n) > 1}):
        problems.append(f"setting '{name}' appears in more than one category")
    known = set(names)
    labels: dict[str, str] = {}
    for records in grouped.values():
        for record in records:
            if not record.description:
                problems.append(f"setting '{record.name}' has no description")
            for label in record.override.get("labels", ()):
                if label in labels:
                    problems.append(
                        f"label '{label}' is used by both '{labels[label]}' "
                        f"and '{record.name}'"
                    )
                labels[label] = record.name
    for name, override in overrides.items():
        if name not in known:
            problems.append(f"override for unknown setting '{name}'")
        for key in set(override) - OVERRIDE_KEYS:
            problems.append(f"override for '{name}' has unknown key '{key}'")
    return problems


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def render_rst_literal(text: str) -> str:
    return f"``{text}``"


def render_setting(record: SettingRecord) -> list[str]:
    """Render one setting as RST source lines (a ``confval`` entry)."""
    lines = [
        f".. confval:: {record.name}",
        f"   :type: {render_rst_literal(record.type_label)}",
        f"   :default: {render_rst_literal(record.default)}",
        "",
    ]
    body: list[str] = []

    deprecated = record.override.get("deprecated")
    if deprecated:
        version, _, note = str(deprecated).partition(" ")
        body += [f".. deprecated:: {version}", ""]
        if note:
            body += [f"   {note}", ""]
    for key, directive in (
        ("added_in", "versionadded"),
        ("changed_in", "versionchanged"),
    ):
        for entry in _as_list(record.override.get(key)):
            version, _, note = str(entry).partition(" ")
            body += [f".. {directive}:: {version}"]
            if note:
                body += ["", f"   {note}"]
            body += [""]

    fields = []
    if record.aliases:
        fields.append(
            ":Aliases: " + ", ".join(render_rst_literal(a) for a in record.aliases)
        )
    if record.settable_from_env:
        env = ", ".join(render_rst_literal(v) for v in record.env_vars)
        if record.string_delimiter:
            env += (
                f" (items separated by {render_rst_literal(record.string_delimiter)})"
            )
        fields.append(f":Environment variable: {env}")
    else:
        fields.append(":Environment variable: not supported")
    if record.expandvars:
        fields.append(":Variable expansion: ``${VAR}`` is expanded in values")
    body += [*fields, ""]

    body += _markdown_block(record.description)

    example = record.override.get("example")
    if example:
        body += [".. code-block:: yaml", ""]
        body += [
            f"   {line}" if line else "" for line in str(example).rstrip().splitlines()
        ]
        body += [""]
    notes = record.override.get("notes")
    if notes:
        body += _markdown_block(str(notes))
    for target in _as_list(record.override.get("seealso")):
        body += [f".. seealso:: {target}", ""]

    lines += [f"   {line}" if line else "" for line in body]
    for label in record.override.get("labels", ()):
        lines += ["", f".. _{label}:"]
    return lines


def _markdown_block(text: str) -> list[str]:
    """RST lines embedding ``text`` (Markdown) through the private directive."""
    if not text.strip():
        return []
    return [".. conda-config-markdown::", "", *_indent(text.strip()), ""]


def _indent(text: str, prefix: str = "   ") -> list[str]:
    return [f"{prefix}{line}" if line else "" for line in text.splitlines()]


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


class ConfigMarkdown(SphinxDirective):
    """Private directive: parse its body as Markdown with the project's MyST config."""

    has_content = True

    def run(self) -> list[nodes.Node]:
        from docutils.utils import new_document
        from myst_parser.parsers.sphinx_ import MystParser

        document = new_document(
            self.state.document["source"], self.state.document.settings
        )
        document.settings.env = self.env
        MystParser().parse("\n".join(self.content), document)
        return list(document.children)


class ConfigReference(SphinxDirective):
    has_content = False
    required_arguments = 0
    optional_arguments = 0

    def run(self) -> list[nodes.Node]:
        overrides = load_overrides()
        grouped = build_records(overrides=overrides)
        for problem in validate_records(grouped, overrides):
            log.warning(
                "conda-config-reference: %s", problem, location=self.get_location()
            )

        lines = []
        for category, records in grouped.items():
            lines += [
                f".. _config-category-{slug(category)}:",
                "",
                category,
                "-" * len(category),
                "",
                *self._summary_table(records),
                "",
            ]
            for record in records:
                lines += [*render_setting(record), ""]
        return self.parse_text_to_nodes("\n".join(lines), allow_section_headings=True)

    def _summary_table(self, records: list[SettingRecord]) -> list[str]:
        lines = [
            ".. list-table::",
            "   :header-rows: 1",
            "   :widths: 25 15 20 40",
            "",
            "   * - Setting",
            "     - Type",
            "     - Default",
            "     - Summary",
        ]
        for record in records:
            default = record.default
            if len(default) > SUMMARY_MAX_DEFAULT_LENGTH:
                default = default[: SUMMARY_MAX_DEFAULT_LENGTH - 1].rstrip() + "…"
            lines += [
                f"   * - :confval:`{record.name}`",
                f"     - {render_rst_literal(record.type_label)}",
                f"     - {render_rst_literal(default)}",
                f"     - {_plain_inline(record.summary)}",
            ]
        return lines


def _plain_inline(text: str) -> str:
    """Make a Markdown summary safe to embed as RST inline text."""
    text = text.replace("`", "")
    return re.sub(r"([\\*|_])", r"\\\1", text)


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_directive("conda-config-reference", ConfigReference)
    app.add_directive("conda-config-markdown", ConfigMarkdown)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
