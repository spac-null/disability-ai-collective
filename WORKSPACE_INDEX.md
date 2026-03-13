# Workspace Index

Quick reference for all Python scripts and data files.

## Image Generators

| File | Role |
|------|------|
| `scene_image_generator.py` | **PRIMARY** — scene-based pixel art renderer. 8 scene types (transit_hub, urban_street, office_interior, theater, campus, library, open_air, data_center). Qwen3.5-guided direction + optional vision validation. Use `validate=False` in cron. |
| `intelligent_image_generator.py` | Abstract wave/pattern generator — backup if scene generator fails |
| `generate_sophisticated_art_simple.py` | Original wave generator — acoustic_chaos, visual_hierarchy, accessibility_flow |
| `real_world_aware_generator.py` | Older real-world renderer (superseded by scene_image_generator) |
| `enhanced_image_generator.py` | Earlier enhanced generator (superseded) |
| `ai_image_generator.py` | Prompt-based image generator stub |

## Automation

| File | Role |
|------|------|
| `automation/production_orchestrator.py` | Daily automation runner — picks topic from DB, generates article + images, commits + pushes. Entry point for cron at 16:00 UTC. |
| `automation/cron_article_orchestrator_with_discovery.py` | Article metadata + content generator with topic discovery |
| `rss_disability_crawler.py` | RSS crawler — discovers disability/AI articles, writes to `disability_findings.db` |
| `disability_discovery_crawler.py` | DuckDuckGo-based topic discovery crawler |
| `smart_disability_search.py` | Smart search fallback crawler |
| `run_discovery_crawler.py` | Discovery crawler runner script |

## Data

| File | Role |
|------|------|
| `disability_findings.db` | Primary SQLite findings DB (used by production_orchestrator) |
| `rss_disability_findings.db` | RSS-specific findings DB |

## Cron Schedule

| Time (UTC) | Script | Purpose |
|------------|--------|---------|
| 08:00 | discovery crawler | Fills `disability_findings.db` |
| 16:00 | production_orchestrator | Generates article + images, publishes via git push |

## Qwen Integration

- Endpoint: `http://vision-gateway:8080` (qwen3.5:9b)
- Prefix: `/no_think` for fast responses (~8s vs ~42s with thinking)
- scene_image_generator: text direction + optional vision validation
- Use `validate=False` from orchestrator to skip vision scoring in cron runs
