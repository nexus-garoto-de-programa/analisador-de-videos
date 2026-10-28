# Analisador de vídeos

Cole o link de um Reels (ou TikTok/Shorts) numa sessão do Claude Code neste repositório.
O Claude:

1. **baixa e "assiste"** o vídeo: cortes detectados, frames do gancho a cada 0,5 s, um frame por
   segundo, transcrição com tempo por palavra, picos de volume, BPM e reconhecimento da música;
2. **analisa com o seu método** (`metodo/METODO.md`): gancho em 4 camadas (visual, fala, texto, som),
   retenção, estrutura, efeitos de edição, som, gatilhos, CTA e um **esqueleto replicável**;
3. **cria um roteiro** com a mesma estrutura, sobre o tema que você quiser, no seu tom.

## Como usar

Abra uma sessão nova do Claude Code com este repositório e escreva, por exemplo:

- `https://www.instagram.com/reel/XXXX/` → análise completa
- `o gancho não foi a pergunta, foi o corte seco no rosto` → o Claude corrige e **aprende**
- `aprovada` → vira exemplo de referência
- `faz um roteiro nessa estrutura sobre degradê navalhado` → roteiro cena a cena
- `o que você já aprendeu?` → resumo das regras que você ensinou

## Como o treino funciona

Não há modelo sendo re-treinado: o "algoritmo" é o seu método, escrito em texto e lido antes de
cada análise.

- Cada correção vira uma lição em `metodo/LICOES.md` (o que eu disse × o certo × regra geral).
- Lições que você diz que valem "sempre", ou que se repetem, sobem para **Regras do dono** em
  `metodo/METODO.md`, que tem prioridade sobre todo o resto.
- Análises que você aprova (⭐) viram exemplo do nível esperado.
- Preencha `metodo/MEU-PERFIL.md` (ou deixe o Claude perguntar no primeiro roteiro).

Tudo fica versionado no git; dá para ver como o método evoluiu e desfazer uma lição ruim.

## Cookies do Instagram

O Instagram costuma bloquear downloads sem login vindos de servidores. Se o download falhar:

1. No computador, logado no Instagram (de preferência uma conta secundária), exporte os cookies
   no formato Netscape com uma extensão como "Get cookies.txt LOCALLY".
2. Ou coloque o conteúdo na variável de ambiente `INSTAGRAM_COOKIES` do ambiente do Claude Code
   (configurações do ambiente na nuvem), ou salve como `cookies.txt` na raiz do repositório
   (já está no `.gitignore`, nunca é commitado).

Alternativa sem cookies: baixe o vídeo no celular, envie o arquivo para a sessão e peça
para analisar o arquivo.

## Rodar na mão

```bash
scripts/setup.sh
.venv/bin/python scripts/analisar.py "https://www.instagram.com/reel/XXXX/"
.venv/bin/python scripts/analisar.py ~/Downloads/video.mp4 --modelo medium
```

Opções: `--modelo` (tiny/base/small/medium/large-v3; padrão small), `--idioma auto`,
`--limiar 0.2` (pega transições mais suaves), `--sem-musica`, `--cookies arquivo.txt`.

Requer Python 3.10+ e ffmpeg.

## Limites

- O Claude vê frames (até 2 por segundo no gancho, 1 por segundo no resto), não o vídeo contínuo:
  efeitos muito rápidos entre frames podem passar. A análise lista o que não deu para confirmar.
- Reconhecimento de música usa o Shazam por uma biblioteca não oficial; pode falhar, e música
  original/voz por cima não é reconhecida. O Instagram às vezes informa o áudio nos metadados.
- BPM é estimado e serve só de pista.
