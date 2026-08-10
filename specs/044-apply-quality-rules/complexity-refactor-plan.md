# Plano de Refatoramento por Complexidade

**Objetivo:** reduzir a complexidade ciclomática (CCN) dos blocos acima do
limiar de bloqueio do quality gate: `xenon --max-absolute=B` (CCN ≤ 10).

**Métrica final desejada:** Nenhum bloco acima de B (CCN ≤ 10), média ≤ A/B.

**Status (após Fases 1 e 2 concluídas):** todos os blocos D/E/F foram
eliminados; média geral **B (8.52)**; suite completa **1219 passed**. O gate
ainda falha por **48 blocos rank-C** (`--max-absolute=B`) e pelo teto de 20
módulos rank-B (`--max-modules=20`). Esses 48 blocos ficam para a **Fase 3**.

## Mapa de progresso das fases

| Fase | Escopo | Status |
| ---- | ------ | ------ |
| Fase 1 (P0) | Blocos 1–6 (graus F/E) | ✅ Concluída |
| Fase 2 (P1) | Blocos 7–13 (graus D) | ✅ Concluída |
| Fase 2.5 (P2) | Blocos 14–17 (graus D) | ✅ Concluída |
| Fase 3 | 48 blocos C remanescentes | ⏳ A iniciar |

---

## Priorização e Estratégia

O conjunto de candidatos (com CCN real):

| Bloco | Arquivo:linha | CCN | Prioridade |
| ----- | -------------- | --- | ---------- |
| `PipelineOrchestrator._build_stage_entities` | `specmetrics/application/orchestrator.py:414` | F (64) | **P0** |
| `RulePackValidator._validate_config_by_type` | `specmetrics/plugins/rule_pack/validator.py:139` | F (41) | **P0** |
| `RuleApplicator.apply` | `specmetrics/plugins/rule_pack/applicator.py:47` | E (39) | **P0** |
| `format_text_result` | `specmetrics/cli/formatters.py:14` | E (38) | **P0** |
| `SFPCounter.count` | `specmetrics/plugins/measurement/sfp/counter.py:32` | E (34) | **P0** |
| `SNAPAssessor.assess` | `specmetrics/plugins/measurement/snap/assessor.py:40` | E (31) | **P0** |
| `PipelineOrchestrator._build_stage_results` | `specmetrics/application/orchestrator.py:672` | D (30) | **P1** |
| `PipelineOrchestrator._build_stage_details` | `specmetrics/application/orchestrator.py:814` | D (28) | **P1** |
| `RulePackLoader.load` | `specmetrics/kernel/engine_rule.py:81` | D (25) | **P1** |
| `run_measure` | `specmetrics/cli/measure.py:131` | D (25) | **P1** |
| `CfmSerializer.load` | `specmetrics/infrastructure/serialization/cfm_serializer.py:73` | D (23) | **P1** |
| `compare_explanations` | `specmetrics/kernel/explanation/comparison.py:42` | D (23) | **P1** |
| `calculate` (storypoints) | `specmetrics/plugins/measurement/storypoints/calculator.py:375` | D (23) | **P1** |
| `EvidenceGraphStage.handle` | `specmetrics/kernel/evidence_graph_stage.py:149` | D (22) | **P2** |
| `calculate` (token_points) | `specmetrics/plugins/measurement/token_points/calculator.py:81` | D (22) | **P2** |
| `run` (export_commands) | `specmetrics/cli/export_commands.py:77` | D (22) | **P2** |
| `PipelineEngine.run` | `specmetrics/kernel/pipeline_engine.py:56` | D (21) | **P2** |

## Padrões de Refatoração (aplicados a todos)

Cada bloco será reduzido usando **Extract Method** + **Strategy / Dispatch table**
+ **Guard clauses**. Sem mudança de comportamento (refatoração pura), validada
por testes existentes:

```
ANTES:  def big(self, x):
            if cond1: ...
            elif cond2: ...
            elif cond3: ...
            ...  # 40 nós

DEPOIS: def big(self, x):
            return self._branch1(x)  # <10 CCN cada
```

Quando a complexidade vem de um grande `if/elif` por tipo (caso mais comum nos
blocos listados), usar **dicionário de despacho** (Strategy):

```
_HANDLERS = {"discover": _h_discover, "extract": _h_extract, ...}
result = _HANDLERS[stage_name](ctx)
```

---

## Bloco P0 — Fase 1 ✅ concluída

### 1. `PipelineOrchestrator._build_stage_entities` (F=64) — `orchestrator.py:414`

> ✅ Resolvido → A (5).

O pior bloco. É um grande `if/elif` por `stage_name` com as etapas:
`discover`, `extract`, `graph`, `csm`, `cfm`, `rule`, `measure`, `export`.

**Ação:**
1. Extrair cada ramo para um método privado:
   - `_entities_for_discover(ctx)` → list[dict]
   - `_entities_for_extract(ctx)` → list[dict]
   - `_entities_for_graph(ctx)` → list[dict]
   - `_entities_for_csm(ctx)` → list[dict]
   - `_entities_for_cfm(ctx)` → list[dict]
   - `_entities_for_rule(ctx)` → list[dict]
   - `_entities_for_measure(ctx)` → list[dict]
   - `_entities_for_export(ctx, export_path)` → list[dict]
2. Substituir o `elif` em cadeia por um dict de despacho `_STAGE_ENTITY_BUILDERS`.
3. `_build_stage_entities` reduz para ~5 CCN (loop + chamada de dispatch).

**Impacto:** é a maior redução da média; resolve também `_build_stage_results`
e `_build_stage_details` (P1) se o mesmo padrão for aplicado (mesmos stage_names).

---

### 2. `RulePackValidator._validate_config_by_type` (F=41) — `rule_pack/validator.py:139`

> ✅ Resolvido → A (2).

Ação: o método valida tipos de config com um `switch` por `config_type`.
- Extrair um validador por tipo (`_validate_functional`, `_validate_snap`,
  `_validate_cognitive`, ...).
- Despachar por dicionário `type → validator`.

---

### 3. `RuleApplicator.apply` (E=39) — `rule_pack/applicator.py:47`

> ✅ Resolvido → B (7).

Aplicação de regras por tipo. Mesmo tratamento:
- Extrair `_apply_<tipo>` métodos.
- Unificar estrutura com o helper já existente `_apply_complexity_overrides`
  (C=12) e `_apply_weight_overrides` (B=10).

---

### 4. `format_text_result` (E=38) — `cli/formatters.py:14`

> ✅ Resolvido → A (3).

Formatas a saída por métrica com `switch` grande.
- Extrair `_format_<metric>` por métrica.
- Dict `metric → formatter`.
- Confirma que `_format_metric` (C=13) cobre parte.

---

### 5. `SFPCounter.count` (E=34) — `sfp/counter.py:32`

> ✅ Resolvido → A (4).

Contador com muitas ramificações por tipo de componente.
- Extrair contadores por componente (`_count_client_visible`,
  `_count_transactional`, ...).
- Unificar com padronização de `FPACounter.count` (C=13), já baixo.

---

### 6. `SNAPAssessor.assess` (E=31) — `snap/assessor.py:40`

Avaliação SNAP por categoria. Extrair `_assess_<category>` e despacho por dict.

> ✅ Resolvido → ≤ B.

---

## Bloco Fase 2 — ✅ concluída

> ✅ Todos resolvidos:
> 7. `_build_stage_results` → B (7)
> 8. `_build_stage_details` → B (7)
> 9. `RulePackLoader.load` → A (3)
> 10. `run_measure` → B (10)
> 11. `CfmSerializer.load` → B (8)
> 12. `compare_explanations` → B (7)
> 13. `calculate` storypoints → B (7)

### 7. `PipelineOrchestrator._build_stage_results` (D=30) — `orchestrator.py:672`
### 8. `PipelineOrchestrator._build_stage_details` (D=28) — `orchestrator.py:814`

Mesmos stage_names de `_build_stage_entities` → reutilizar same dispatch table.

### 9. `RulePackLoader.load` (D=25) — `kernel/engine_rule.py:81`
- Extrair carregamento por forma (dict, lista, string/YAML).

### 10. `run_measure` (D=25) — `cli/measure.py:131`
- Extrair parse de opções e fluxos de exportação por flag.

### 11. `CfmSerializer.load` (D=25) — `serialization/cfm_serializer.py:73`
- Extrair parsing de cada seção do CFM (actors, processos, regras, ...).

### 12. `compare_explanations` (D=23) — `explanation/comparison.py:42`
- Extrair compare de cada campo (`_compare_element_fields` já existe, estender).

### 13. `calculate` storypoints (D=23) — `storypoints/calculator.py:375`
- Extrair as funções de computação por fator/categoria.

---

## Bloco Fase 2.5 — ✅ concluída (P2)

> ✅ Todos resolvidos:
> 14. `EvidenceGraphStage.handle` → A (5)
> 15. `calculate` token_points → A (3)
> 16. `run` export_commands → B (9)
> 17. `PipelineEngine.run` → B (6)

---

## Bloco Fase 3 — 48 blocos C remanescentes (a iniciar)

Após eliminar todos os D/E/F, o gate ainda falha em **48 blocos rank-C**
(`--max-absolute=B`) e no teto de **20 módulos rank-B** (`--max-modules=20`).
Ordem por prioridade: concentrar nos blocos com maior impacto e nos arquivos
com mais ocorrências (kernel primeiro, depois plugins de medição, depois CLI).

| # | Bloco | Arquivo:linha | CCN |
| - | ----- | -------------- | --- |
| 1 | `DeterministicSemanticEngine` | `kernel/deterministic_engine.py:69` | C |
| 2 | `DeterministicSemanticEngine._load_rules` | `kernel/deterministic_engine.py:86` | C |
| 3 | `_match_rule_against_observation` | `kernel/deterministic_engine.py:158` | C |
| 4 | `_execute_rules` | `kernel/deterministic_engine.py:197` | C |
| 5 | `_load_framework_packs` | `kernel/deterministic_engine.py:287` | C |
| 6 | `ListVisitor` / `ListVisitor.visit` | `kernel/engine_visitors.py:81` | C |
| 7 | `TableVisitor` / `TableVisitor.visit` | `kernel/engine_visitors.py:117` | C |
| 8 | `LinkVisitor` / `LinkVisitor.visit` | `kernel/engine_visitors.py:305` | C |
| 9 | `match` (engine_patterns) | `kernel/engine_patterns.py:45` | C |
| 10 | `complete` (llm_gateway) | `kernel/llm_gateway.py:395` | C |
| 11 | `build` (cfm/builder) | `kernel/cfm/builder.py:98` | C |
| 12 | `_build_functional_processes` | `kernel/cfm/builder.py:244` | C |
| 13 | `build` (csm/builder) | `kernel/csm/builder.py:47` | C |
| 14 | `load` (graph_persistence) | `kernel/graph_persistence.py:53` | C |
| 15 | `register` (plugin_registry) | `kernel/plugin_registry.py:39` | C |
| 16 | `validate` (plugin_validation) | `kernel/plugin_validation.py:53` | C |
| 17 | `run` (validation/pipeline) | `kernel/validation/pipeline.py:123` | C |
| 18 | `constitution_engaged` | `kernel/validation/rules/constitutional.py:49` | C |
| 19 | `explain` (explanation/service) | `kernel/explanation/service.py:231` | C |
| 20 | `trace_element` | `kernel/explanation/evidence_tracer.py:34` | C |
| 21 | `_format_metric` | `kernel/explanation/formatters/text.py:29` | C |
| 22 | `count` (fpa/counter) | `plugins/measurement/fpa/counter.py:31` | C |
| 23 | `validate_rule_pack` (snap) | `plugins/measurement/snap/rule_applicator.py:13` | C |
| 24 | `score_factor` (storypoints) | `plugins/measurement/storypoints/factor_scorer.py:19` | C |
| 25 | `StoryPointsCalibrationProfile` | `plugins/measurement/storypoints/calibrator.py:47` | C |
| 26 | `_build_cfm_non_fp_items` | `plugins/measurement/storypoints/calculator.py:220` | C |
| 27 | `measure` (sfp/plugin) | `plugins/measurement/sfp/plugin.py:84` | C |
| 28 | `aggregate` (cognitive_points) | `plugins/measurement/cognitive_points/models.py:127` | C |
| 29 | `_process_csm` | `plugins/measurement/cognitive_points/calculator.py:230` | C |
| 30 | `_measure` (bcp/plugin) | `plugins/measurement/bcp/plugin.py:131` | C |
| 31 | `calculate` (bcp/sdk_adapter) | `plugins/measurement/bcp/sdk_adapter.py:90` | C |
| 32 | `generate_story` (bcp) | `plugins/measurement/bcp/story_generator.py:8` | C |
| 33 | `merge_calibration_data` | `plugins/calibration/loader.py:34` | C |
| 34 | `export` (xml_exporter) | `plugins/exporter/xml_exporter.py:29` | C |
| 35 | `__init__` / `extract` (llm_provider) | `plugins/semantic/llm_provider.py:106` | C |
| 36 | `_scan_with_result` (speckit) | `plugins/adapter/speckit/plugin.py:129` | C |
| 37 | `_scan_with_result` (openspec) | `plugins/adapter/openspec/plugin.py:118` | C |
| 38 | `compute_retention` | `infrastructure/runs/cleaner.py:80` | C |
| 39 | `_run_auto_export` | `cli/measure.py:51` | C |
| 40 | `_parse_metrics` | `cli/measure.py:101` | C |
| 41 | `_run_pipeline_export` | `cli/export_commands.py:248` | C |
| 42 | `llm_set` / `llm_test` | `cli/config_commands.py:182/322` | C |
| 43 | `validate` | `cli/commands/validate.py:40` | C |
| 44 | `_validate_tool_params` | `mcp/server.py:212` | C |

Nota: também reduzir os módulos rank-B até `--max-modules=20` (o teto atual é
ultrapassado; idealmente todo o gate passa com 0 módulos B além do permitido).

Papeis de refatoração aplicáveis por padrão: **Extract Method** + **Strategy /
Dispatch table** + **Guard clauses**, preservando comportamento (ver seção
"Padrões de Refatoração").

---

## Validação por bloco

A cada bloco/marco:
1. `make test` (dev+cov e mutação não regridem)
2. `make complexity` → xenon deve passear para essas.
3. Rodar manualmente o comando c/ script cujo caminho foi tocado (ex.:
   `specmetrics measure` para `orchestrator`), comparar saída de demais requisições.
4. `make lint`.

**Regra para aceitação de cada inteiro:**
- CCN final do bloco ≤ 10 (grau ≤ B).
- Nenhuma mudança de assinatura pública nem de formato de saída (JSON/CSV/XML).
- Sem breaking-change; testes existentes verdes.

---

## Critério de conclusão

`make quality-gate` terminará com:
- xenon: nenhum `ERROR` de bloco (todos ≤ B) e ≤ 20 módulos rank-B
- MI warning: `>= 70`
- Média de complexidade (avg) < B.

## Ordem de execução recomendada (sequencial, incremental, commitável)

1. ~~Fase 1 P0 (blocos 1–6)~~ — ✅ concluída.
2. ~~Fase 2 (7–13)~~ — ✅ concluída.
3. ~~Fase 2.5 (14–17)~~ — ✅ concluída.
4. **Fase 3 (48 blocos C)** — por arquivo/prioridade: kernel →
   plugins de medição → CLI/MCP → adapters.
5. Validação final do gate em CI (`make quality-gate`).