# Plotting and evidence standard

- Plot only finite, validated structured columns.
- Preserve original values; transformations must create new columns or explicit metadata.
- State units, normalization, zero/reference, broadening, interpolation, smoothing, aggregation, and uncertainty.
- Use readable labels and a restrained, consistent style. Do not encode scientific status only by color.
- Save a machine-readable plot metadata JSON with input hash, columns, labels, limits, style, output hash, and command.
- Validate output existence and nonzero size. For important figures, render and inspect visually.
- Never use smoothing or axis limits to hide discontinuities, imaginary modes, missing data, or failed ranges.
- A visual trend is a hypothesis until a script-backed numerical statistic supports it.
- After visual QA, embed every completed figure in the user response from its absolute local path and show the exact source-data route used to produce it.
- Display the associated numerical result table or summary alongside the figure. Do not substitute a plot for source provenance or numerical validation.
