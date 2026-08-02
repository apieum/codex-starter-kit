<div align="center">
  <img src="assets/avatar-round.png" alt="Codex Starter Kit" width="112" height="112">

  <h1>Codex Starter Kit</h1>

  <p><strong>Готовый стартовый набор для OpenAI Codex CLI: агенты, skills, hooks, MCP, plugins и глобальный AGENTS.md.</strong></p>

  <p>
    Установите один раз, перезапустите Codex и получите рабочую базу для разработки, ревью, QA, DevOps, дизайна, продукта, данных и безопасности.
  </p>

  <p>
    <a href="README.md">English</a>
    ·
    <a href="README-RU.md">Русская версия</a>
  </p>

  <p>
    <a href="https://github.com/VKirill/codex-starter-kit">GitHub Repository</a>
    ·
    <a href="https://t.me/pomogay_marketing">Telegram: @pomogay_marketing</a>
  </p>

  <p>
    <img alt="OpenAI Codex CLI" src="https://img.shields.io/badge/OpenAI-Codex%20CLI-111111">
    <img alt="Agents" src="https://img.shields.io/badge/62-Custom%20Agents-2563eb">
    <img alt="Skills" src="https://img.shields.io/badge/101-Skills-7c3aed">
    <img alt="MCP" src="https://img.shields.io/badge/MCP-Context7%20%7C%20Vue%20%7C%20Nuxt-16a34a">
    <img alt="Hooks" src="https://img.shields.io/badge/Hooks-Safety%20Guard-f97316">
    <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-059669">
  </p>
</div>

## Что Это

`codex-starter-kit` превращает чистый Codex CLI в готовую рабочую среду.

Внутри уже лежат:

- 62 кастомных Codex-агента в `agents/*.toml`
- 101 reusable skill в `skills/*/SKILL.md`
- глобальные правила работы Codex в `templates/AGENTS.md`
- безопасный shell hook против опасных команд
- правила автоматического одобрения безопасных команд в `rules/default.rules`
- базовый `~/.codex/config.toml` с GitHub и bundled local Superpowers/Claude Companion plugins
- публичные docs MCP: Context7, Vue, Nuxt UI, Nuxt
- рекомендованные локальные MCP-маршруты для Serena, GitNexus, Postgres, Open Design и claude-mem
- bundled fork `VKirill/superpowers` в `plugins/superpowers`
- repo-local прототип Claude Companion plugin в `plugins/claude-companion` для ревью через interactive Claude Code в tmux
- установщик с `--dry-run`, backup-режимом и валидацией

Главная идея простая: вы не собираете рабочий Codex-процесс с нуля. Вы ставите базу, проверяете ее и дальше настраиваете под свои проекты через локальные `AGENTS.md`.

## Быстрый Путь

Если вы хотите, чтобы Codex сам сделал установку, откройте Codex на нужной машине и вставьте prompt из следующего блока.

```text
Ты должен установить Codex Starter Kit для OpenAI Codex CLI и проверить, что установка безопасна.

Репозиторий:
https://github.com/VKirill/codex-starter-kit

Цель:
- сделать этот starter kit базовой настройкой Codex на этой машине
- установить глобальный ~/.codex/AGENTS.md из templates/AGENTS.md
- установить кастомных агентов в ~/.codex/agents
- установить skills в ~/.agents/skills
- установить safety hooks в ~/.codex/hooks и ~/.codex/hooks.json
- установить правила одобрения безопасных команд в ~/.codex/rules
- установить рекомендуемый ~/.codex/config.toml из templates/config.recommended.toml
- включить GitHub плюс bundled local Superpowers и Claude Companion plugin entries через config.toml
- включить public docs MCP servers для Context7, Vue, Nuxt UI и Nuxt
- проверить и описать recommended local MCP/plugin routes для Serena, GitNexus, Postgres, Open Design и claude-mem
- выполнить полную локальную самонастройку workflow, когда это безопасно: Serena, GitNexus и claude-mem
- включить Claude Companion только если Claude Code CLI уже установлен; не устанавливать Claude или tmux автоматически
- добавить GitHub/source links для каждого включенного plugin и recommended MCP/plugin route
- сохранить старые файлы через timestamped .bak-* backups

Работай пошагово:
1. Если репозитория еще нет, клонируй его в ~/projects/codex-starter-kit.
2. Если репозиторий уже есть, перейди в него и проверь текущее состояние git.
3. Прочитай README.md, README-RU.md, install.py и templates/config.recommended.toml.
4. Запусти проверку пакета:
   python3 scripts/validate-pack.py
5. Запусти dry run:
   ./install.sh --dry-run
6. Покажи мне, какие пути будут заменены, и отдельно посчитай агентов и skills.
7. Если dry run выглядит безопасно, запусти установку с backup-режимом:
   ./install.sh
8. Проверь, что ~/.codex/config.toml содержит GitHub, superpowers@codex-starter-kit и claude-companion@codex-starter-kit plugins, а также MCP servers context7, vue-docs, nuxt-ui-remote и nuxt-remote.
9. Сообщи, что Serena, GitNexus, Postgres, Open Design и claude-mem — recommended local/plugin routes для полноценного starter-kit workflow.
10. Для каждого включенного plugin и recommended MCP/plugin route покажи GitHub/source link из README.md или templates/config.recommended.toml.
11. Запусти полный local workflow preflight:
   - определи OS и package manager: apt, dnf, pacman, zypper, brew или none
   - проверь команды: tmux, claude, uv, uvx, node, npm, npx, gitnexus
   - проверь Codex runtime: codex, `codex plugin marketplace upgrade`, `codex mcp list`
   - перед установкой чего-либо покажи, каких tools не хватает
12. Если Claude Code CLI отсутствует, не устанавливай Claude и не устанавливай tmux для Claude Companion. Сообщи, что Claude Companion отключён на этой машине, пока пользователь сам не установит и не авторизует Claude Code.
13. Если Claude Code CLI есть, проверь `claude --version`. Затем проверь tmux. Если tmux отсутствует, не устанавливай его автоматически; покажи manual install command для найденного package manager:
   - Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y tmux`
   - Fedora/RHEL: `sudo dnf install -y tmux`
   - Arch: `sudo pacman -S --needed tmux`
   - openSUSE: `sudo zypper install -y tmux`
   - macOS: `brew install tmux`
14. Не читай, не копируй, не парси, не печатай и не переноси Claude credentials. Используй только собственный auth flow Claude Code. Если Claude установлен, но не авторизован, открой интерактивную `claude`-сессию и попроси пользователя выполнить `/login`; затем перепроверь. Не инспектируй `~/.claude/.credentials.json`, cookies, keychains, bearer tokens или API keys.
15. Если uv/uvx отсутствует и Serena нужна или не установлена, установи uv после подтверждения через официальный Astral installer или системный package manager. Затем установи и инициализируй Serena:
   `uv tool install -p 3.13 serena-agent@latest --prerelease=allow`
   `serena init`
   Проверь, что `serena` доступна в PATH. Не записывай private ports или bearer tokens в публичные starter-kit файлы.
16. Если GitNexus отсутствует, установи или используй его после подтверждения:
   `npm install -g gitnexus`
   или для одноразового MCP-запуска:
   `npx -y gitnexus@latest mcp`
   Затем выполни безопасные проверки: `gitnexus --help`, `gitnexus status` в текущем repo, если применимо. Перед индексацией больших репозиториев спроси подтверждение. Если пользователь разрешит индексировать этот starter-kit repo, запусти `gitnexus analyze` из repo root.
17. Если claude-mem отсутствует и пользователь хочет memory continuity, установи его после подтверждения:
   `npx claude-mem@latest install`
   Затем перезапусти Codex и проверь доступные MCP/tools, если это безопасно. Если install падает или выглядит нестабильно, сообщи ошибку и оставь его выключенным.
18. Если recommended local MCP/plugin routes уже установлены и их безопасно проверить, проверь через `codex mcp list` или их read-only status-команды. Не записывай private ports, local paths, bearer tokens или database credentials в публичные starter-kit файлы.
19. Если команда codex доступна, запусти:
   codex plugin marketplace upgrade
   codex mcp list
20. Проверь установленных агентов:
   ./install.sh --validate-only
21. В конце кратко напиши, что изменилось, где лежат backups, какие tools установлены, какие recommended MCP/plugin routes активны или отсутствуют, где ещё нужен ручной login и что нужно перезапустить Codex.

Правила безопасности:
- не удаляй ~/.codex, ~/.agents или существующие agents/skills без backup
- не используй --force и --no-backup без моего явного разрешения
- не копируй secrets, bearer tokens, приватные MCP настройки и локальные database credentials
- не устанавливай Claude Code или tmux автоматически; Claude Companion работает только на машинах, где Claude уже установлен
- не читай Claude credentials напрямую; всегда делегируй authentication самому Claude Code
- спрашивай подтверждение перед sudo, package-manager installs, global npm installs, `curl | sh`, индексацией больших repo, запуском daemons или изменением services
- перед mutation предпочитай read-only проверки; если install падает, остановись и предложи самый маленький безопасный fix
- если команда требует повышенного доступа или сетевого разрешения, сначала объясни зачем
- если проверка падает, остановись, покажи ошибку и предложи самый маленький безопасный fix
```

## Ручная Установка

Клонируйте репозиторий:

```bash
git clone https://github.com/VKirill/codex-starter-kit ~/projects/codex-starter-kit
cd ~/projects/codex-starter-kit
```

Проверьте пакет:

```bash
python3 scripts/validate-pack.py
```

Посмотрите, что установщик собирается заменить:

```bash
./install.sh --dry-run
```

Установите baseline с backup-режимом:

```bash
./install.sh
```

Проверьте установленных агентов:

```bash
./install.sh --validate-only
```

После установки перезапустите Codex. Без перезапуска глобальные инструкции, agents, skills, hooks и plugins могут не подхватиться.

## Что Будет Установлено

| Путь | Что туда попадет | Зачем |
| --- | --- | --- |
| `~/.codex/AGENTS.md` | глобальные рабочие правила | единое поведение Codex во всех проектах |
| `~/.codex/agents/` | 62 кастомных subagents | роли для разработки, ревью, QA, DevOps, продукта, дизайна и копирайтинга |
| `~/.agents/skills/` | 101 skill | reusable инструкции для задач и доменов |
| `~/.codex/hooks/` | safety и handoff hook scripts | классификация пользовательских prompts, блокировка опасных shell-команд, автоодобрение известных безопасных permission prompts и подсказки верификации после install/failure |
| `~/.codex/hooks.json` | hook config | подключение UserPromptSubmit, PermissionRequest, PreToolUse и PostToolUse hooks к Codex |
| `~/.codex/rules/` | правила одобрения команд | автоодобрение частых read-only команд для разработки, Linux-диагностики, package metadata и infra inspection |
| `~/.codex/config.toml` | baseline config | plugins, MCP servers, approvals, docs discovery |

По умолчанию установщик заменяет managed paths и сначала переносит старые файлы в `.bak-*` backups.

## Карта Агентов

Агенты лежат в `agents/*.toml`. Каждый агент имеет узкую роль, свой `model_reasoning_effort`, варианты nickname и ограниченный набор skills.

| Категория | Когда выбирать | Агенты |
| --- | --- | --- |
| <img alt="Orchestration" src="https://img.shields.io/badge/Flow-Orchestration-0f172a"> | handoff intake scoring, task ledger, планирование, workflow, координация | `agents_orchestrator`, `project_manager_senior`, `specialized_workflow_architect`, `automation_governance_architect` |
| <img alt="Engineering" src="https://img.shields.io/badge/Build-Engineering-2563eb"> | backend, frontend, mobile, CMS, архитектура, код | `engineering_backend_architect`, `engineering_frontend_developer`, `engineering_senior_developer`, `engineering_software_architect`, `engineering_minimal_change_engineer`, `engineering_rapid_prototyper`, `engineering_mobile_app_builder`, `engineering_cms_developer`, `engineering_codebase_onboarding_engineer`, `engineering_code_reviewer`, `engineering_technical_writer`, `engineering_git_workflow_master`, `lsp_index_engineer`, `terminal_integration_specialist`, `specialized_mcp_builder`, `specialized_developer_advocate` |
| <img alt="Data and AI" src="https://img.shields.io/badge/Data-AI%20%26%20Pipelines-7c3aed"> | ML, data pipelines, databases, email/audio intelligence | `engineering_ai_engineer`, `engineering_ai_data_remediation_engineer`, `engineering_data_engineer`, `engineering_database_optimizer`, `engineering_email_intelligence_engineer`, `engineering_voice_ai_integration_engineer`, `specialized_model_qa` |
| <img alt="Ops and Security" src="https://img.shields.io/badge/Ops-Security%20%26%20Reliability-dc2626"> | infrastructure, incidents, security, compliance | `engineering_devops_automator`, `engineering_sre`, `engineering_security_engineer`, `engineering_threat_detection_engineer`, `engineering_incident_response_commander`, `engineering_autonomous_optimization_architect`, `compliance_auditor` |
| <img alt="Testing" src="https://img.shields.io/badge/Proof-Testing%20%26%20QA-16a34a"> | проверки, evidence, accessibility, performance | `testing_api_tester`, `testing_evidence_collector`, `testing_accessibility_auditor`, `testing_performance_benchmarker`, `testing_reality_checker`, `testing_tool_evaluator`, `testing_test_results_analyzer`, `testing_workflow_optimizer` |
| <img alt="Product" src="https://img.shields.io/badge/Product-Delivery%20%26%20Research-f97316"> | roadmap, feedback, sprint, эксперименты, delivery | `product_manager`, `product_feedback_synthesizer`, `product_trend_researcher`, `product_sprint_prioritizer`, `product_behavioral_nudge_engine`, `project_management_project_shepherd`, `project_management_experiment_tracker`, `project_management_jira_workflow_steward`, `project_management_studio_operations`, `project_management_studio_producer` |
| <img alt="Design" src="https://img.shields.io/badge/Design-UX%20%26%20Brand-ec4899"> | UI, UX, brand, визуалы, research | `design_ui_designer`, `design_ux_architect`, `design_ux_researcher`, `design_brand_guardian`, `design_visual_storyteller`, `design_image_prompt_engineer`, `design_inclusive_visuals_specialist`, `design_whimsy_injector` |
| <img alt="Knowledge" src="https://img.shields.io/badge/Knowledge-Notes%20%26%20Systems-0891b2"> | knowledge base, notes, cross-domain reasoning | `zk_steward` |

## Skills По Смыслу

Skills находятся в `skills/`. Они ставятся в `~/.agents/skills` и помогают агентам работать точнее.

| Группа | Примеры |
| --- | --- |
| Process | `planning-methodology`, `task-decomposition`, `testing-patterns`, `bug-hunter`, `code-review-checklist` |
| Frontend | `frontend-developer`, `react-patterns`, `nextjs-best-practices`, `vue-developer`, `ui-designer`, `playwright-skill` |
| Backend | `nodejs-expert`, `fastify-pro`, `fastapi-pro`, `api-patterns`, `auth-implementation-patterns`, `graphql` |
| Data | `postgresql`, `database-design`, `prisma-expert`, `drizzle-orm-expert`, `redis-patterns`, `data-engineer` |
| Ops | `docker-expert`, `terraform-specialist`, `linux-sysadmin`, `github-actions-templates`, `server-management` |
| Security | `security-audit`, `backend-security-coder`, `find-bugs`, `incident-responder` |
| Product and Docs | `copywriter`, `ru-text`, `roadmap-methodology`, `goal-achievement-review`, `software-architecture` |

Subagents use role-based allowlist emulation through `[[skills.config]] enabled = false`, so each role sees a focused skill menu instead of the whole library.

## Safety Model

Installer работает в baseline mode: он делает этот starter kit главным набором Codex-настроек.

Защита по умолчанию:

- `./install.sh --dry-run` показывает будущие замены без записи
- старые managed paths уходят в timestamped `.bak-*` backups
- agent TOML проверяется после установки
- `skills.config` paths переписываются под ваш home directory
- `codex plugin marketplace upgrade` и `codex mcp list` запускаются только если `codex` есть в `PATH`
- локальный plugin marketplace `codex-starter-kit` регистрируется динамически из install path, а bundled plugins вроде `superpowers@codex-starter-kit` и `claude-companion@codex-starter-kit` включаются, если их metadata есть в репозитории
- bundled local plugins также копируются в Codex plugin cache, поэтому их skills видны в новых Codex sessions без отдельной ручной установки
- `rules/default.rules` снижает количество запросов подтверждения для read-only команд: package metadata checks, Linux inspection, service status, Docker/Kubernetes/Terraform inspection и GitHub CLI view/list
- Baseline использует `approval_policy = "on-request"` с sandbox `workspace-write` и без исходящего shell-сетевого доступа по умолчанию. Внешние действия, повышение привилегий и мутации вне curated read-only allowlist требуют подтверждения.
- Recoverable deletion через `gio trash <path>` одобряется автоматически. Permanent deletion команды вроде `rm`, `rmdir` и `unlink` остаются заблокированы.
- `cp` автоматически одобряется для autonomous handoff file-copy workflows; sandbox scope и safety hooks всё равно ограничивают, куда команда может писать.
- `printf`, `python`, `python3` и broad `pnpm` автоматически одобряются для autonomous handoff workflows; критические mutations вроде package publish/deploy/release всё равно блокируются safety hook.
- npm workspace формы (`npm --workspace`, `npm -w`, `npm --workspaces`, `npm --prefix`) и pnpm workspace формы (`pnpm --filter`, `pnpm -F`, `pnpm --recursive`, `pnpm -r`, `pnpm --dir`, `pnpm -C`) одобрены для handoff development workflow
- `hooks/handoff-intake-classifier.py` классифицирует user prompts на `UserPromptSubmit` только если существует `~/.codex/private/handoff-classifier.env`. При наличии этого private-файла он без сети работает через deterministic fallback и использует LLM как основной classifier, если там заданы `OPENAI_API_KEY` и `HANDOFF_CLASSIFIER_MODEL`. LLM path запрашивает строгий Responses API Structured Outputs (`text.format` JSON Schema) и нормализует typed booleans вроде `should_edit`, `requires_release_flow`, `requires_worktree_gate` и `requires_gitnexus_impact`; plain JSON parsing оставлен только как compatibility fallback. Итоговый hook context рендерится компактно на английском.
- Для implementation prompts classifier добавляет normalized engineering brief с профессиональным архитектурным словарем и, если Codex передал рабочую директорию, компактный repo profile из root и nearest-workspace `package.json`, `AGENTS.md`, runtime engines, типичных monorepo-сигналов и allowlist архитектурно значимых dependency versions: frameworks, build tools, test tools, ORM, databases, queues, contract libraries, UI kits и observability libraries.
- Короткие follow-up prompts вроде `доработай`, `продолжай`, `ещё`, `тогда` или `сделай так` могут использовать предыдущий локальный hook context перед вызовом LLM. State хранится в `~/.codex/private/handoff-classifier-state.json`, если путь доступен для записи, иначе в `~/.codex/memories/handoff-classifier-state.json`; путь можно переопределить через `HANDOFF_CLASSIFIER_STATE_PATH`. State ограничен по размеру, хранится с правами `0600`, по возможности scoped по session/repo и редактирует распространённые API keys/tokens перед повторным использованием.
- `hooks/handoff-permission-request.py` автоматически одобряет безопасные PermissionRequest prompts для MCP calls и команд, уже описанных в `rules/default.rules`; это помогает текущим сессиям продолжать работу, если обычные rules ещё не перезагрузились
- `hooks/handoff-permission-request.py` автоматически одобряет только команды из curated read-only allowlist. MCP tools и service controls следуют политике одобрения Codex.
- safety hook продолжает блокировать разрушительные или мутирующие варианты: `git reset --hard`, `git clean`, force push, `npm audit fix`, `go env -w`, `journalctl --vacuum-*`, а также mutating `curl`/`wget` requests
- persistent host/service mutations вроде `systemctl disable`, `systemctl mask`, `systemctl kill`, Docker volume deletion, container prune и host reboot/shutdown всё ещё блокируются или требуют явного подтверждения
- сообщения hook'а сразу подсказывают Codex, какие read-only проверки выполнить дальше; часть Git cleanup/restore команд проходит один раз после свежей проверки `git status` плюс `git diff` или `git clean -nd` в той же рабочей директории
- `hooks/handoff-post-tool-use.py` добавляет follow-up context после package installs, failed shell commands, `git diff` и verification commands, чтобы Codex проверял diff/tests, связывал результат с task ledger или исправлял конкретную ошибку перед повтором команды
- MCP servers в starter kit используют `default_tools_approval_mode = "prompt"`; database и local-machine MCP всё равно должны использоваться read-only, если пользователь явно не просил mutation.
- `templates/AGENTS.md` содержит handoff intake scoring и task-ledger правила. Для нетривиальных implementation tasks теперь по умолчанию предполагается proactive subagent authorization, а вопросы, planning-only задачи, one-file fixes и явные inline-only requests остаются inline. Одобренные Superpowers plans могут автоматически использовать описанный worker split, а implementation plans должны включать review checkpoints после секций и финальный code-review/verification pass.
- Claude Companion встроен в `templates/AGENTS.md`, `agents_orchestrator`, planning methodology и code review skills как advisory second-opinion reviewer. Если доступны `claude` и `tmux`, high-risk plans, completed Superpowers stages/worker groups, broad changes, data/security reviews и release readiness checks должны запускаться через `$claude:*` plugin commands вроде `$claude:code-review`, `$claude:security-review` или `$claude:release-readiness-review` с plan path, changed files, scope, verification и конкретными вопросами. Runner добавляет компактную senior-review methodology для каждого режима; Codex всё равно обязан классифицировать и проверять каждую рекомендацию перед применением.

Опциональная классификация prompts и LLM fallback:

```bash
mkdir -p ~/.codex/private
chmod 700 ~/.codex/private
printf 'OPENAI_API_KEY=...\nHANDOFF_CLASSIFIER_MODEL=gpt-5.4-nano\nHANDOFF_CLASSIFIER_LLM=auto\nHANDOFF_CLASSIFIER_TIMEOUT=6.0\n' > ~/.codex/private/handoff-classifier.env
chmod 600 ~/.codex/private/handoff-classifier.env
```

`HANDOFF_CLASSIFIER_LLM=off` включает deterministic-only offline mode. `auto` и `always` используют модель при наличии credentials; deterministic classification остаётся fallback для API errors, timeouts или unsupported structured output.

Опасный режим:

```bash
./install.sh --force
```

Используйте его только если точно хотите заменить managed files без backups.

## Config, Plugins, MCP

Baseline config лежит здесь:

```text
templates/config.recommended.toml
```

Установщик записывает его сюда:

```text
~/.codex/config.toml
```

В config включены:

- GitHub plugin entry: https://github.com/openai/plugins/tree/main/plugins/github
- bundled Superpowers fork plugin from https://github.com/VKirill/superpowers
- bundled Claude Companion plugin from `plugins/claude-companion`
- project docs discovery defaults
- agent concurrency defaults
- public remote docs MCP servers для Context7, Vue, Nuxt UI и Nuxt

## MCP Coverage

Starter kit разделяет переносимые MCP defaults и recommended local integrations. Локальные entries входят в рекомендованный full setup, но остаются commented в public baseline, потому что им нужны local daemons, paths, ports, bearer tokens, plugin state или database credentials.

| MCP или plugin | Статус в репозитории | Source | Почему |
| --- | --- | --- | --- |
| `github@openai-curated` | включен в `templates/config.recommended.toml` | https://github.com/openai/plugins/tree/main/plugins/github | GitHub repositories, issues, pull requests и review workflow |
| `superpowers@codex-starter-kit` | bundled local plugin, включается `install.py` через local marketplace | https://github.com/VKirill/superpowers | forked planning, TDD, debugging, verification и development workflow skills |
| `context7` | включен в `templates/config.recommended.toml` | https://github.com/upstash/context7 | публичный docs server, локальный daemon не нужен |
| `vue-docs` | включен в `templates/config.recommended.toml` | https://github.com/joelbarmettlerUZH/vue-mcp | публичная документация Vue ecosystem |
| `nuxt-ui-remote` | включен в `templates/config.recommended.toml` | https://github.com/nuxt/ui | публичная документация Nuxt UI |
| `nuxt-remote` | включен в `templates/config.recommended.toml` | https://github.com/nuxt/nuxt | публичная документация Nuxt |
| `serena` | recommended local MCP; commented example в `templates/config.recommended.toml`; упоминается в `templates/AGENTS.md` и agents | https://github.com/oraios/serena | semantic code navigation, references и targeted edits |
| `gitnexus` | recommended local MCP; commented example в `templates/config.recommended.toml`; упоминается в `templates/AGENTS.md` и многих agents | https://github.com/abhigyanpatwari/GitNexus | code graph, impact analysis, route maps, execution flows и repo context |
| `postgres` | recommended local MCP; commented example в `templates/config.recommended.toml`; упоминается в `templates/AGENTS.md` и data/API agents | https://github.com/modelcontextprotocol/servers | local database inspection; tool calls автоодобрены для handoff, но agents должны оставаться read-only без явной задачи на mutation |
| `open-design` | recommended local MCP для design workspaces | https://github.com/nexu-io/open-design | local design artifacts, design-system context и visual handoff |
| `claude-mem` | recommended local plugin/runtime для memory continuity | https://github.com/thedotmack/claude-mem | durable cross-session memory в `~/.claude-mem` и `mcp-search` tools |

`templates/AGENTS.md` намеренно просит Codex использовать Serena, GitNexus, Context7, framework docs MCP, Open Design MCP, claude-mem и database MCP, когда они доступны. Baseline config по умолчанию включает только переносимые public docs servers; recommended local integrations нужно включать после установки их daemons/plugins.

Для claude-mem используйте его собственный installer/runtime flow, например:

```bash
npx claude-mem@latest install
```

После настройки перезапустите Codex и проверьте, что видит runtime:

```bash
codex mcp list
```

Ручная проверка runtime-интеграции:

```bash
codex plugin marketplace upgrade
codex mcp list
```

Ручное добавление MCP, если вы не используете baseline config:

```bash
codex mcp add context7 --url https://mcp.context7.com/mcp
codex mcp add vue-docs --url https://mcp.vue-mcp.org/mcp
codex mcp add nuxt-ui-remote --url https://ui.nuxt.com/mcp
codex mcp add nuxt-remote --url https://nuxt.com/mcp
```

## Настройка Путей

Другой Codex home:

```bash
./install.sh --codex-home /path/to/.codex
```

Другой skills home:

```bash
./install.sh --skills-home /path/to/skills
```

Установить не все части:

```bash
./install.sh --skip-hooks
./install.sh --skip-rules
./install.sh --skip-skills
./install.sh --skip-agents
./install.sh --skip-config
./install.sh --skip-global-agents-md
./install.sh --skip-runtime-refresh
```

## Структура Репозитория

```text
codex-starter-kit/
├── agents/                     # Custom Codex subagents (*.toml)
├── skills/                     # Skills copied to ~/.agents/skills
├── hooks/                      # Shell safety hook and hook template
├── rules/                      # Codex command approval rules
├── templates/
│   ├── AGENTS.md               # Global project-agnostic Codex instructions
│   └── config.recommended.toml # Baseline ~/.codex/config.toml
├── prompts/
│   └── bootstrap-codex-starter-kit.md
├── scripts/
│   └── validate-pack.py
├── install.py
└── install.sh
```

## Разработка

Проверить пакет:

```bash
python3 scripts/validate-pack.py
```

Проверить dry run:

```bash
./install.sh --dry-run
```

Проверить установленных агентов:

```bash
./install.sh --validate-only
```

## Что Не Делать

- Не коммитьте secrets, bearer tokens и private MCP config.
- Не кладите project-specific правила в global `AGENTS.md`.
- Не запускайте `--force`, если вам нужны backups.
- Не добавляйте local-only MCP ports в public baseline config.

Project-specific инструкции держите в `AGENTS.md` конкретного репозитория.

## GitHub Topics

```text
openai-codex
codex-cli
codex-agents
codex-skills
agents-md
ai-coding-agents
mcp
subagents
developer-tools
coding-agent
```

Search keywords: OpenAI Codex agents, Codex CLI agents, Codex skills, Codex subagents, AGENTS.md template, Codex MCP setup, Codex hooks, AI coding agents, custom Codex agents and skills, Codex developer workflow, coding agent starter kit.

## License

MIT
