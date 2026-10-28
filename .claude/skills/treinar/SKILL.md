---
name: treinar
description: Grava as correções do dono sobre uma análise de vídeo para que as próximas análises saiam do jeito dele. Use quando o usuário discordar, corrigir ou complementar uma análise ("não, o gancho foi…", "você esqueceu…", "sempre olhe…"), quando aprovar uma análise ("ficou perfeita", "aprovada") ou pedir para revisar o método.
---

# Treinar o método

O "treino" é texto: correções viram lições em `metodo/LICOES.md`, e lições que valem sempre
viram regras em `metodo/METODO.md` → **Regras do dono**. As próximas análises leem os dois.

## Quando o dono corrige
1. Entenda a correção. Se for ambígua, pergunte **uma** coisa antes de gravar.
2. Corrija o `analise.md` daquela pasta e mude o status para `revisada`.
3. Adicione no topo de `metodo/LICOES.md`:
   ```
   ## AAAA-MM-DD — analises/<pasta>
   - **Eu disse:** <o que estava na análise>
   - **O certo é:** <o que o dono disse, com as palavras dele>
   - **Regra geral:** <o que fazer nos próximos vídeos; generalize sem perder o sentido>
   ```
4. Promova para **Regras do dono** em `METODO.md` quando:
   - o dono usar "sempre", "nunca", "toda vez", ou pedir explicitamente; ou
   - a mesma lição aparecer pela segunda vez.
   Marque a lição como `→ promovida`.
5. Se a correção mostrar que uma lente do método está errada ou faltando, proponha a mudança
   no texto do método (mostre o antes/depois) e só altere depois do "ok".
6. Commit e push (`treino: <resumo da lição>`). Responda em 2–3 linhas o que foi aprendido.

## Quando o dono aprova
- Mude o status da análise para `aprovada ⭐` e marque ⭐ no `analises/INDICE.md`.
  Análises aprovadas servem de exemplo de nível para as próximas.
- **Roteiro aprovado:** mude o status do roteiro para `aprovado ⭐`, grave como lição o que os ajustes
  ensinaram (se ainda não gravou), commit e push, depois **abra um pull request para a `main` e faça o
  merge** (regra do `CLAUDE.md`). Responda com o link do PR.

## Revisar o método ("o que você já aprendeu?")
- Resuma as Regras do dono e as lições não promovidas.
- Aponte lições que se contradizem ou se repetem e proponha uma versão consolidada.
