---
name: analisar-video
description: Analisa um vídeo curto (Instagram Reels, TikTok, Shorts) a partir de um link ou arquivo — gancho, cortes, efeitos visuais, música, estrutura, CTA — seguindo o método do dono. Use sempre que o usuário colar um link de vídeo ou enviar um vídeo, mesmo sem dizer "analise".
---

# Analisar vídeo

## 1. Preparar
Leia, nesta ordem, antes de olhar o vídeo:
1. `metodo/METODO.md` (principalmente **Regras do dono**)
2. `metodo/LICOES.md` inteiro
3. `analises/INDICE.md`; se houver análises ⭐ aprovadas, leia a mais recente delas como exemplo do nível esperado.

## 2. Extrair
```bash
scripts/setup.sh            # só se .venv não existir
.venv/bin/python scripts/analisar.py "<link ou caminho do arquivo>"
```
- A última linha da saída é a pasta da análise (`analises/AAAA-MM-DD-<id>/`).
- Se o download falhar (código 2), **não invente a análise**. Explique ao usuário as duas saídas
  que o script imprime (cookies do Instagram ou enviar o arquivo) e pare.
- Vídeo sem fala: o relatório diz isso; analise só imagem e som.
- Vídeo com muita transição suave e poucos cortes detectados: rode de novo com `--limiar 0.2`.

## 3. Assistir
1. Leia `relatorio_tecnico.md` da pasta.
2. Abra (Read) **todos** os `frames/gancho_*.jpg`, um por um.
3. Abra **todas** as `frames/linha_do_tempo_*.jpg` (1 frame por segundo, tempo no canto).
4. Abra os `frames/plano_*.jpg` necessários para entender cada plano; em vídeos com até 30 planos, abra todos.
5. Cruze: fala (transcrição com tempo) × cortes (tabela de planos) × picos de volume × o que aparece nos frames.
   Texto na tela você lê nos frames; transcreva-o.

## 4. Escrever
- Copie `templates/analise.md` para `<pasta>/analise.md` e preencha todas as seções seguindo as
  10 lentes do método. Status: `rascunho`.
- Toda observação com tempo (`[02.4s]`). Hipóteses marcadas como _hipótese_.
- Seção "O que não deu para confirmar" é obrigatória (ex.: efeito que acontece entre dois frames).
- Adicione a linha no topo da tabela de `analises/INDICE.md`.

## 5. Entregar
- Commit e push (`git add analises && git commit -m "análise: <autor> — <tema>"`).
- No chat, mostre: resumo em 3 linhas, a tabela do gancho, o esqueleto replicável e as notas.
  Diga onde está a análise completa.
- Termine com duas perguntas:
  1. "Alguma coisa que eu vi diferente de você?" (as respostas viram treino → skill `treinar`)
  2. "Quer um roteiro nessa estrutura? Me diga o tema." (→ skill `criar-roteiro`)
