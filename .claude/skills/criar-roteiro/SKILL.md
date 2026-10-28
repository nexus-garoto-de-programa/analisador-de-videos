---
name: criar-roteiro
description: Cria um roteiro de vídeo curto com a mesma estrutura de um vídeo já analisado, adaptado ao tema e ao perfil do dono. Use quando o usuário pedir roteiro, script, "faz um vídeo assim sobre X", ou responder com um tema depois de uma análise.
---

# Criar roteiro

## Entradas
1. **Análise de base**: a da conversa atual, ou a que o usuário indicar (procure em `analises/INDICE.md`).
   Pode ser mais de uma ("gancho do vídeo A + estrutura do B").
2. **Tema**: o que o usuário quer falar. Se não disse, pergunte.
3. `metodo/MEU-PERFIL.md`: se faltar algo essencial (nicho, público, tom, objetivo), pergunte só
   o que falta, **grave as respostas no arquivo** e siga.
4. Regras do dono em `metodo/METODO.md` que falem de roteiro.

## Como escrever
- Parta do **Esqueleto replicável** da análise: mesmos blocos, mesma duração aproximada de cada
  bloco, mesmo tipo de gancho, mesmo ritmo de cortes, mesmo tipo de CTA.
- Troque o tema, nunca a mecânica. Não copie frases do original; recrie com a voz do dono.
- 3 opções de gancho de tipos diferentes, com fala + visual + texto na tela. Recomende uma.
- Cena a cena com tempo, fala, visual, texto na tela, efeito e som. A fala tem que caber no tempo
  (use a velocidade em palavras/min do original como referência).
- Tudo gravável com o que o perfil diz que o dono tem (sozinho, celular, editor).
- Preencha `templates/roteiro.md` e salve em `roteiros/AAAA-MM-DD-<tema>.md`.

## Entregar
- Commit e push (`roteiro: <tema>`).
- No chat: as 3 opções de gancho e a tabela cena a cena. Pergunte se quer ajustar algo; ajustes
  de gosto sobre roteiros também viram lição (skill `treinar`).
