REPO         := $(CURDIR)
CLAUDE_SKILL := $(HOME)/.claude/skills/figurinha
SCRIPT       := $(REPO)/skill/scripts/figurinha.sh

.PHONY: help install status uninstall espaco limpar

## help: Exibe esta ajuda
help:
	@echo "Targets disponíveis:"
	@grep "^## " $(MAKEFILE_LIST) | sed 's/^## /  /'

## install: Symlink de ~/.claude/skills/figurinha para skill/
install:
	@mkdir -p $(dir $(CLAUDE_SKILL))
	@if [ -L "$(CLAUDE_SKILL)" ]; then \
		echo "  skip (symlink já existe): $(CLAUDE_SKILL)"; \
	elif [ -e "$(CLAUDE_SKILL)" ]; then \
		echo "  AVISO: $(CLAUDE_SKILL) já existe (não é symlink), pulando"; \
	else \
		ln -s "$(REPO)/skill" "$(CLAUDE_SKILL)" && echo "  + figurinha"; \
	fi

## status: Exibe o estado do symlink e o espaço do ambiente
status:
	@if [ -L "$(CLAUDE_SKILL)" ]; then echo "  ok  figurinha -> $$(readlink $(CLAUDE_SKILL))"; \
	elif [ -e "$(CLAUDE_SKILL)" ]; then echo "  !   figurinha (arquivo real, não symlink)"; \
	else echo "  --  figurinha (não instalada)"; fi
	@$(SCRIPT) espaco

## uninstall: Remove o symlink (o ambiente em ~/.cache/figurinhas fica; veja limpar)
uninstall:
	@[ -L "$(CLAUDE_SKILL)" ] && rm "$(CLAUDE_SKILL)" && echo "  - figurinha" || true

## espaco: Quanto o ambiente de recorte ocupa
espaco:
	@$(SCRIPT) espaco

## limpar: Apaga o ambiente e o modelo (~1,2 GB); voltam sozinhos no próximo uso
limpar:
	@$(SCRIPT) limpar
