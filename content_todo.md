# Content TODO

A page-by-page read-through of everything currently live on the site, flagging stubs, gaps, broken links, and sentences that need a pass. Organized by page; a final section covers orphaned/duplicate files that aren't reachable from navigation but still sit in the repo.

## index.qmd (home page)

- [x] **Typo**: "NSF iCorps Entrepeneurial Lead" → "Entrepreneurial" (Resume → Professional Experience → Data Scientist, Neuroscience).
- [x] **Missing org name**: the "Data Scientist, Neuroscience" resume entry has no company/lab listed, unlike the other two Professional Experience entries (Syntouch Inc; Woods Hole Oceanographic Institution). Either add one or confirm it's meant to stay generic.
- [x] **"Get in touch!" section has no way to actually get in touch** — it's just the sentence "Think there might be an idea we could collaborate on? Get in touch!" with no email link, contact form, or repeated social links. Needs an actual call-to-action (mailto link at minimum).
- [x] **Real content sitting commented-out and invisible**: a whole Teaching section (USC + Columbia + Workshops) is HTML-commented out entirely. Same for Community Involvement (Pangeo-Forge, PaleoBooks Library, Demerara Rise Cruise Blog) and a Software Development list. Either restore these somewhere on the site or confirm they're intentionally retired — right now they're dead content nobody sees.
- [x] **Naming mismatch**: the commented-out Software Development list says "Developer, PaleoBeasts (2023–present)" — is PaleoBeasts an old name for ClimateCritters (the actual current package name used everywhere else), or a separate project? Worth reconciling before this section is ever un-commented.

## subpages/overview.qmd (portfolio cards, included on the home page)

- [x] **Broken link**: the "Extra Science" card links to `/misc.html` — `misc.qmd` no longer exists in the repo. This card is currently dead on the live homepage.
- [x] **Broken anchor**: "Climate Critters" links to `/software.html#climatecrittes` — typo (missing "r"); the real heading id is `#climatecritters`. Even setting the typo aside, this points at the orphaned `software.qmd` rather than the current `software/linkedearth.qmd` page (see Orphaned Files below).
- [x] Same issue for the "Pyleoclim" and "Cedarkit" links just below it — both point to `/software.html#...` anchors on the stale, unlinked page instead of `/software/linkedearth.html` and `/software/ccm.html`.
- [x] **Empty stub heading**: "##### Carbon Cycle" has no content under it at all — just a bare heading before the section closes.
- [x] Minor inconsistency: image `src` attributes here are root-absolute (`/assets/img/...`) but the lightbox `[+](...)` links right next to them use relative paths (`assets/img/...`). Works today since this file is only ever included into the root-level `index.qmd`, but worth normalizing to root-absolute for consistency with the rest of the site.

## science/nonlin_causality.qmd

- [x] **Grammatical error**: "I tested whether solar variability had a discernible influence surface temperature over the Holocene." — missing "on" before "surface temperature."
- [x] **Garbled sentence**: "...we approached the project as a parameter sweep and interpretted the results as evidence of solar influence may exist on multiple time scales." Reads like two sentences fused together, and "interpretted" has a typo. Likely meant something like "...interpreted the results as evidence that solar influence may exist on multiple time scales."
- [ ] **"The Pleistocene: Orbital Forcing and the 100,000-Year Problem" section is just an opening hook** — two paragraphs setting up the question, then nothing: no methodology, findings, or references section like every other topic on this page has. Needs either the rest of the writeup or an explicit "in progress" note so it doesn't read as accidentally cut off.
- [x] **Inconsistent lightbox grouping**: in the figure banner under "The Holocene...", three images share `data-gallery="holoceneCcmGallery"` but the embedding-windows image uses `data-gallery="methodGallery"` — it won't cycle together with its neighbors in the lightbox. Likely just needs to match the other three.

## science/etc.qmd

- [ ] **"Radiocarbon" section has no body text at all** — it goes straight from the `## Radiocarbon` heading to a bare References list, with no paragraph describing what the work was (unlike "Watermass Geometry" right above it, which has full Methodology/Proof of Concept prose). Needs at least a short descriptive paragraph.

## software.qmd, software/ccm.qmd, software/linkedearth.qmd

- [x] **Broken link**: `[website]()` for CedarKit is empty — no URL at all. Appears identically on both `software.qmd` and `software/ccm.qmd`.
- [x] **Stub**: "### PapertrailCM (coming soon)" — placeholder heading, no content. Same on both files.
- [x] **Stub**: "### Misc Tools" (in `linkedearth.qmd` and `software.qmd`) — heading with nothing underneath.
- [x] **Missing description**: the Pyleoclim entry has documentation/GitHub links but no descriptive paragraph, while Climate Critters right below it does. Inconsistent completeness.

## openscience_edu.qmd

- [x] **Stub**: "## Climate Dynamics Curriculum {#geol351}" is just `[coming soon!]`.
- [x] Everything else on this page (PaleoBooks section) reads complete and well-written — no issues.

## favorite_figures.qmd

- [x] No issues found — reads complete, all images/PDFs verified to exist.

## pres_pub.qmd + subpages/*.qmd (citation lists)

- [x] No content issues — these were already reworked this session (author formatting, brace-stripping, LaTeX cleanup). Verified consistent.

## Orphaned / duplicate files (not linked from navigation, but still in the repo)

These don't show up anywhere on the live site, but they're sitting in the source tree and are worth a decision — restore/link them, or delete them so they don't cause confusion later:

- [x] **`about.qmd`** — not the real About page (that content lives inline in `index.qmd`). This is generic leftover Quarto scaffolding — a "Simple Lightbox Example" referencing `mv-1.jpg`/`mv-2.jpg`/`mv-3.jpg`, which don't exist in the repo. Safe to delete.
- [x] **`software.qmd`** — a stale, near-duplicate of `software/ccm.qmd` + `software/linkedearth.qmd` combined (same CedarKit/Pyleoclim/ClimateCritters content, same broken `[website]()` link, same empty stubs). Nothing currently links to it, but `subpages/overview.qmd`'s portfolio-card links (see above) still point at it instead of the real pages. Recommend deleting it and repointing those links.
- [ ] **`open_science/geol351.qmd`** — a second, completely empty stub for Climate Dynamics Curriculum (just a title, no body), separate from the "[coming soon!]" stub already in `openscience_edu.qmd`. Not linked anywhere.
- [ ] **`open_science/paleobooks.qmd`** — a second, completely empty stub for PaleoBooks (just a title, no body) — while the real, finished PaleoBooks writeup already lives inline in `openscience_edu.qmd`. Not linked anywhere.

## Site-structure notes (not content per se, but adjacent)

- [ ] `content/sidebar_nav.yml`'s second nav section lists "Favorite Figures" twice — once nested under the Science category, once as a flat top-level link in the last section. Not broken, just redundant; worth trimming to one.
