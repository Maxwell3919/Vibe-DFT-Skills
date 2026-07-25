#!/usr/bin/env node
"use strict";

/*
 * Thin, fail-closed CLI adapter for helloworld-Co/html2md.
 *
 * The upstream project exposes its HTML-to-Markdown conversion in a Nuxt
 * component rather than as a command-line program. This adapter loads the
 * exact Turndown and GFM dependencies installed with that project and keeps
 * the same fenced-code/GFM conversion model. CP2K-specific preprocessing
 * remains in sync_official_manuals.py.
 */

const fs = require("fs");
const os = require("os");
const path = require("path");
const childProcess = require("child_process");

const ADAPTER_SCHEMA_VERSION = "1.0";
const EXPECTED_UPSTREAM_COMMIT =
  "ca08965af93e6565806a79087868daa439565ffc";
const UPSTREAM_URL = "https://github.com/helloworld-Co/html2md";

function fail(message) {
  process.stderr.write(`html2md adapter error: ${message}\n`);
  process.exit(2);
}

function parseArgs(argv) {
  const result = {
    identity: false,
    root:
      process.env.HTML2MD_ROOT ||
      path.join(os.homedir(), ".local", "share", "html2md"),
  };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--identity") {
      result.identity = true;
    } else if (value === "--html2md-root") {
      index += 1;
      if (index >= argv.length) {
        fail("--html2md-root requires a path");
      }
      result.root = path.resolve(argv[index]);
    } else {
      fail(`unknown argument: ${value}`);
    }
  }
  return result;
}

function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (error) {
    fail(`cannot read ${filePath}: ${error.message}`);
  }
}

function packageVersion(root, packageName) {
  return readJson(
    path.join(root, "node_modules", packageName, "package.json"),
  ).version;
}

function gitCommit(root) {
  try {
    return childProcess
      .execFileSync("git", ["-C", root, "rev-parse", "HEAD"], {
        encoding: "utf8",
        stdio: ["ignore", "pipe", "pipe"],
      })
      .trim();
  } catch (error) {
    fail(`cannot resolve html2md Git commit: ${error.message}`);
  }
}

function loadInstallation(root) {
  const packageJson = readJson(path.join(root, "package.json"));
  if (packageJson.name !== "hello-html2md") {
    fail("HTML2MD_ROOT is not a helloworld-Co/html2md checkout");
  }
  const commit = gitCommit(root);
  if (commit !== EXPECTED_UPSTREAM_COMMIT) {
    fail(
      `html2md commit ${commit} does not match pinned ` +
        EXPECTED_UPSTREAM_COMMIT,
    );
  }
  let TurndownService;
  let gfmPlugin;
  try {
    TurndownService = require(path.join(root, "node_modules", "turndown"));
    gfmPlugin = require(
      path.join(root, "node_modules", "turndown-plugin-gfm"),
    );
  } catch (error) {
    fail(`html2md dependencies are unavailable: ${error.message}`);
  }
  return {
    TurndownService,
    gfmPlugin,
    identity: {
      adapter_schema_version: ADAPTER_SCHEMA_VERSION,
      expected_upstream_commit: EXPECTED_UPSTREAM_COMMIT,
      git_commit: commit,
      project_name: packageJson.name,
      project_version: packageJson.version,
      upstream_url: UPSTREAM_URL,
      dependencies: {
        jsdom: packageVersion(root, "jsdom"),
        turndown: packageVersion(root, "turndown"),
        "turndown-plugin-gfm": packageVersion(
          root,
          "turndown-plugin-gfm",
        ),
      },
    },
  };
}

function longestBacktickRun(text) {
  let longest = 0;
  for (const match of text.matchAll(/`+/g)) {
    longest = Math.max(longest, match[0].length);
  }
  return longest;
}

function codeLanguage(node) {
  const candidates = [node, node.firstElementChild, node.parentElement];
  for (const candidate of candidates) {
    if (!candidate || !candidate.classList) {
      continue;
    }
    for (let index = 0; index < candidate.classList.length; index += 1) {
      const className = candidate.classList.item(index);
      if (className === "mermaid") {
        return "mermaid";
      }
      const match = className.match(/^(?:language|highlight)-([A-Za-z0-9_+-]+)$/);
      if (match && match[1] !== "default") {
        return match[1].toLowerCase();
      }
    }
  }
  return "";
}

function convert(html, installation) {
  const { TurndownService, gfmPlugin } = installation;
  const service = new TurndownService({
    bulletListMarker: "-",
    codeBlockStyle: "fenced",
    emDelimiter: "*",
    fence: "```",
    headingStyle: "atx",
    strongDelimiter: "**",
  });

  // Match the upstream application's GFM conversion path.
  service.use(gfmPlugin.gfm);
  service.use([gfmPlugin.tables, gfmPlugin.strikethrough]);

  // The upstream pre rule consumes already escaped child Markdown. Reading
  // textContent directly keeps CP2K input underscores, spacing, and symbols.
  service.addRule("cp2kExactPre", {
    filter: ["pre"],
    replacement(_content, node) {
      const code = node.textContent.replace(/\r\n?/g, "\n").replace(/\n$/, "");
      const fence = "`".repeat(Math.max(3, longestBacktickRun(code) + 1));
      const language = codeLanguage(node);
      return `\n\n${fence}${language}\n${code}\n${fence}\n\n`;
    },
  });

  // Sphinx stores TeX source directly in these nodes. Turndown's ordinary
  // escaping would change the TeX; preserve it byte-for-character after DOM
  // decoding.
  service.addRule("cp2kMath", {
    filter(node) {
      return Boolean(node.classList && node.classList.contains("math"));
    },
    replacement(_content, node) {
      const value = node.textContent.replace(/\r\n?/g, "\n").trim();
      return node.nodeName === "DIV" ? `\n\n${value}\n\n` : value;
    },
  });

  // GitHub Markdown has no native definition-list syntax. CP2K uses <dt> as
  // the visible signature for each keyword, so render it as a level-3 heading.
  service.addRule("cp2kDefinitionTerm", {
    filter: ["dt"],
    replacement(content) {
      return `\n\n### ${content.trim()}\n\n`;
    },
  });
  service.addRule("cp2kDefinitionDescription", {
    filter: ["dd"],
    replacement(content) {
      return `\n\n${content.trim()}\n\n`;
    },
  });

  // Keep typographic meaning that plain Markdown cannot represent.
  service.addRule("cp2kSubscriptSuperscript", {
    filter: ["sub", "sup"],
    replacement(content, node) {
      return `<${node.nodeName.toLowerCase()}>${content}</${node.nodeName.toLowerCase()}>`;
    },
  });

  const markdown = service
    .turndown(html)
    .replace(/\r\n?/g, "\n")
    // Turndown can retain presentation-only spaces at the ends of blank and
    // code-example lines. They are invisible content, break repository
    // whitespace checks, and are not required for indentation.
    .replace(/[ \t]+$/gm, "")
    .trim();
  if (!markdown) {
    fail("conversion produced empty Markdown");
  }
  return `${markdown}\n`;
}

const args = parseArgs(process.argv.slice(2));
const installation = loadInstallation(args.root);
if (args.identity) {
  process.stdout.write(`${JSON.stringify(installation.identity)}\n`);
  process.exit(0);
}

const input = fs.readFileSync(0, "utf8");
if (!input.trim()) {
  fail("stdin contains no HTML");
}
process.stdout.write(convert(input, installation));
