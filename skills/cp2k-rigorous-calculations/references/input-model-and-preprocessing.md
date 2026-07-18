# CP2K input model and preprocessing

Read this file when an input contains variables, conditional preprocessing, includes, external coordinates, multiple force evaluators, or restart-generated input.

## Source routing

Resolve `input-reference`, `global`, `force-eval`, `subsys`, `topology`, `ext-restart`, and every decisive child section against the executable version. Use the cached snapshot only when its manifest version and hashes pass; otherwise perform a live check.

## Treat the final expanded deck as the calculation definition

CP2K preprocessing can change values and include external text before the program interprets sections. Preserve separately:

- the user-facing root input hash;
- every included file hash and safe role;
- explicitly supplied preprocessor variables;
- the fully expanded input hash, when a trusted parser can produce it;
- the CP2K version/XML definition used for validation.

Do not compare two campaigns by root input alone when includes or variables can differ.

## Bundled parser boundary

The bundled parser accepts a conservative, already expanded deck. It blocks:

- `@INCLUDE`, `@SET`, `@IF`, variable expansion and multiple statements;
- more than one `FORCE_EVAL`;
- ambiguous or unbalanced section nesting;
- topology/coordinate indirection that has not been supplied as explicit evidence;
- arbitrary unit expressions outside its tested numeric subset.

A block is not evidence that CP2K would reject the input. It means the bundled parser cannot prove what CP2K will execute.

## Optional official-community validator

The `cp2k-input-tools` project provides `cp2klint`, `fromcp2k`, `cp2kget`, preprocessing support, and an input-definition XML. Follow [tool-adapters.md](tool-adapters.md) before invoking it.

- Match the XML definition to the audited CP2K version.
- Constrain include resolution to an inventoried case root.
- Treat its successful parse as syntax/schema evidence, not scientific validity.
- Hash the expanded representation and tool/XML versions.
- Keep the bundled fail-closed scientific profiles after external parsing.

## Required comparison record

For every input comparison record:

- root input SHA-256;
- expanded input SHA-256 or `unresolved`;
- include/data/restart evidence hashes;
- CP2K version and input-definition revision;
- normalized section/keyword summary;
- parser/tool versions and limitations;
- protocol id, comparability group and intended observable.
