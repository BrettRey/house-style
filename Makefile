.PHONY: claude-rules check-claude-rules help

help:
	@echo "Targets:"
	@echo "  claude-rules         Regenerate .claude/rules/*.md from style-guide.md"
	@echo "  check-claude-rules   Verify .claude/rules/*.md are up to date (fails if stale)"

claude-rules:
	python3 scripts/generate-claude-rules.py

check-claude-rules:
	@TMPDIR=$$(mktemp -d) && \
	cp -R ../.claude/rules "$$TMPDIR/rules-backup" && \
	python3 scripts/generate-claude-rules.py >/dev/null && \
	if diff -rq "$$TMPDIR/rules-backup" ../.claude/rules >/dev/null 2>&1; then \
		echo "✓ .claude/rules/ is up to date"; \
		rm -rf "$$TMPDIR"; \
	else \
		echo "✗ .claude/rules/ is STALE — run 'make -C .house-style claude-rules' to regenerate"; \
		diff -r "$$TMPDIR/rules-backup" ../.claude/rules || true; \
		rm -rf "$$TMPDIR"; \
		exit 1; \
	fi
