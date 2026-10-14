# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

A Docker Compose–based local WordPress development environment. There is no build system, test suite, or package manager — the deliverable is the running WordPress site and any custom themes/plugins developed inside `wordpress/wp-content/`.

## Commands

All lifecycle commands run from the repo root against `docker-compose.yaml`:

```bash
docker compose up -d          # Start WordPress + MariaDB
docker compose down           # Stop (volumes/data persist)
docker compose logs -f wordpress
docker compose exec wordpress bash
```

- **Site URL**: http://localhost:3080 (host port 3080 → container 80)
- **Database access**: port 3306 is `expose`d, not published — host tools cannot connect. Use:
  `docker compose exec db mariadb -u wordpress -pwordpress wordpress` (root password: `root`)
- **WP-CLI**: the `wordpress:latest` image does not bundle WP-CLI. Run it as a one-off container:
  `docker run -it --rm --volumes-from wordpress-wordpress-1 --network container:wordpress-wordpress-1 wordpress:cli wp plugin list`
  (adjust the container name to match `docker compose ps` output)

## Architecture

- `docker-compose.yaml` defines two services: `db` (MariaDB `lts-ubi10`) and `wordpress` (`wordpress:latest`). DB credentials live here (`wordpress`/`wordpress`, root `root`) — change them here and via `WORDPRESS_DB_*` env vars, not in `wp-config.php`.
- `wordpress/` is a **full WordPress core checkout bind-mounted to `/var/www/html`** — edits on the host are live in the container immediately; there is no build or deploy step. It is currently stock core (bundled twentytwentythree–twentytwentyfive themes, akismet, hello.php); no custom code exists yet.
- `mysql/` is the **live MariaDB data directory** bind-mounted to `/var/lib/mysql`. Never edit its contents, and exclude both `mysql/` and `wordpress/` from version control if this repo is ever put under git.
- `wordpress/wp-config.php` is the Docker variant: every setting is read from environment variables via `getenv_docker()`. Add custom constants *after* the env-driven block; don't convert the env lookups to hard-coded values.

## Project Rule Documents

The three `engineering-*.md` files at the repo root are expert persona/rule documents that define this project's standards. **Consult the relevant one before doing that kind of work** — they contain detailed deliverable templates, checklists, and anti-patterns:

- `engineering-cms-developer.md` — theme/plugin development, content architecture
- `engineering-wordpress-performance.md` — caching, query optimization, Core Web Vitals
- `engineering-wordpress-shopping-cart.md` — WooCommerce / e-commerce work

Cross-cutting rules from these documents that apply to all work here:

1. **Never edit WordPress or WooCommerce core.** Customize through hooks (actions/filters) in a child theme or custom plugin.
2. **Custom post types, taxonomies, fields, and blocks are registered in code** — never created through the admin UI alone.
3. **Child themes or custom themes only** — never modify a bundled/parent theme.
4. **Configuration that affects behavior belongs in code** (`wp-config.php` constants, plugin files), not in database settings.
5. **Payment credentials and secrets go in env vars / `wp-config.php` constants**, never in committed code or plaintext DB settings.
6. **Cart, checkout, and account pages must never be page-cached** if caching is introduced.
