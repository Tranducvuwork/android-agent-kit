# Reading a Figma design

Used by `mold` step 2 when the input is a Figma link. Classify what you fetch with the table in SKILL.md.

From a Figma link `https://www.figma.com/design/<fileKey>/...?node-id=12-34`, the node id is `12:34`.

## Choose the access

Use the first one available, and tell the user which:

1. **Figma MCP** (a connected Figma tool).
2. **Figma REST API** with `$FIGMA_TOKEN` from the environment.
3. Neither: ask the user to connect one, or to export screenshots of the frames.

The two can be combined: MCP for structure, screenshots, and variables; the REST API for prototype flow
when MCP does not return it and `$FIGMA_TOKEN` is set.

## Token rules

- Only ever use the token as `$FIGMA_TOKEN` inside a command, e.g.
  `curl -s -H "X-Figma-Token: $FIGMA_TOKEN" ...`. Never print it, echo it, or write it to a file.
- Check it with `[ -n "$FIGMA_TOKEN" ]`. If it is missing, tell the user to set it in their shell profile,
  macOS Keychain, or `.claude/settings.local.json` `env` (gitignored), restart the session, and stop.
  Never ask for the token in chat.
- If the user pastes a token in chat anyway, don't use it; tell them to revoke it and set a new one in the
  environment.
- 403: token expired or lacks `file_content:read`. 404: wrong link or no access to the file.

## Figma MCP

Tool names differ between the desktop (Dev Mode) and remote servers and change between versions, so pick
tools by role; the names below are examples.
- **Structure first**: a metadata / structure tool (e.g. `get_metadata`) on the link's node lists frames
  with ids, names, and sizes. Use it to find the screen frames before anything else.
- **Details per screen frame only**: a design-context / code tool (e.g. `get_design_context`, `get_code`)
  returns a lot of tokens. Call it on one screen frame at a time (one id per call), never on a whole page
  or section, and take only what the templates need: text, components, styles. Ignore the generated code.
- **Screenshots**: a screenshot tool (e.g. `get_screenshot`), one frame per call; save each image into
  `screens/`.
- **Tokens**: a variables tool (e.g. `get_variable_defs`) gives the exact color / typography / spacing names.
- **Assets**: when the tools return asset URLs or files, download them into `assets/`.
- **Flow**: if no tool returns prototype interactions, get them from the REST API when `$FIGMA_TOKEN` is
  set; otherwise fall back to arrows drawn on the canvas.

## Figma REST API

- **Structure**: `GET /v1/files/<fileKey>/nodes?ids=<ids>&depth=<n>`. Save the raw response outside the
  repo (scratch or `$TMPDIR`), then filter it with `jq` or a short script down to name, type, size, text,
  style names, and interactions before reading it. Never read the raw JSON into context.
  Ask for details one screen frame at a time (`ids=` holds a single frame id); only the first structure
  call may list several ids. Space the calls out and on a 429 wait before retrying instead of repeating them.
- **Screenshots**: `GET /v1/images/<fileKey>?ids=<one frame id>&format=png&scale=2` per frame, then download
  the returned URL into `screens/`.
- **Assets**: the same endpoint with `format=svg` (vectors) or `png` (photos), download into `assets/`.
- **Flow**: prototype interactions on nodes (`interactions`, or the legacy `transitionNodeID`).
