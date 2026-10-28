# CLAUDE.md — Analisador de vídeos

Ferramenta pessoal: o dono cola o link de um vídeo (Reels, TikTok, Shorts), o Claude analisa
como o dono analisaria e depois cria roteiros na mesma estrutura. O método é treinável.

## O que fazer em cada caso
| O usuário… | Skill |
|---|---|
| cola um link de vídeo ou envia um vídeo | `analisar-video` |
| corrige, discorda, complementa ou aprova uma análise | `treinar` |
| pede roteiro / "faz um assim sobre X" / responde com um tema | `criar-roteiro` |

## Regras
- **pt-BR** em tudo que o usuário lê. Código em inglês ou português, como já está.
- **Nunca invente o que não viu.** Se o download falhar, pare e explique; não analise só pela legenda.
  Cada observação tem tempo; hipóteses são marcadas.
- **O método manda**: `metodo/METODO.md` (Regras do dono primeiro) e `metodo/LICOES.md` são lidos
  antes de toda análise. Correções do dono sempre viram lição (skill `treinar`).
- Vídeos, áudio e frames **não vão para o git** (`.gitignore`). Vão: `analise.md`,
  `relatorio_tecnico.md`, `metadados.json`, roteiros e o método.
- Ao terminar uma análise, um treino ou um roteiro: commit e push.
- **Roteiro aprovado = vai para a `main`.** Antes de aprovar, o dono sempre ajusta o roteiro e ensina
  como trabalha (isso vira lição/regra). Quando ele aprovar ("aprovado", "pode subir", "fechou"),
  marque o roteiro como `aprovado ⭐`, faça commit e push, abra um pull request da branch de trabalho
  para a `main` e faça o merge — sem pedir nova confirmação. Assim a próxima sessão já começa com
  tudo que foi aprendido. Nada vai para a `main` antes da aprovação.
- `cookies.txt` nunca é commitado nem mostrado no chat.

## Estrutura
- `scripts/analisar.py` — baixa (yt-dlp), detecta cortes (ffmpeg), extrai frames, mede o áudio,
  transcreve (faster-whisper), tenta reconhecer a música (Shazam) e escreve `relatorio_tecnico.md`.
  Só mede; a interpretação é do Claude.
- `scripts/setup.sh` — cria `.venv` com as dependências (roda no início de cada sessão).
- `metodo/` — `METODO.md` (as 10 lentes + Regras do dono), `LICOES.md`, `MEU-PERFIL.md`.
- `templates/` — `analise.md`, `roteiro.md`, `prancheta.html`.
- `marca/` — design system da Nexus (`MARCA.md`, `tokens.css`, logo e símbolo). Todo material visual usa a marca.
- `analises/` — uma pasta por vídeo + `INDICE.md`. `roteiros/` — roteiros gerados.
