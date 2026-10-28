# Marca Nexus — design system

Fonte única das cores e dos elementos da marca. Todo material gerado (prancheta, páginas, roteiros
visuais) usa isto. Os tokens prontos para CSS estão em `marca/tokens.css`.

## Cores
| Token | Hex | Uso |
|---|---|---|
| `--nx-roxo` | `#7463EA` | cor principal: destaques, títulos em destaque, links, **destaque das legendas nos vídeos** |
| `--nx-escuro` | `#14121C` | texto, logo em fundo claro, segunda cor de etiquetas |
| `--nx-claro` | `#E8E8E8` | fundo de página, logo em fundo escuro |
| `--nx-roxo-claro` | `#A397F3` | roxo sobre fundo escuro (marcações no visor da câmera); derivado, não está no logo |

Neutros (derivados, puxados para o roxo): texto secundário `#6A6778`, linhas `#DEDCE6`, fundo suave `#F3F2F8`.

## Logo e símbolo (`marca/`)
| Arquivo | Quando usar |
|---|---|
| `nexus-logo-escuro.png` | logo completo em fundo claro (padrão dos documentos) |
| `nexus-logo-claro.png` | logo completo em fundo escuro |
| `nexus-simbolo-roxo.png` | símbolo sozinho, cor principal (marca d'água, ícone) |
| `nexus-simbolo-escuro.png` / `nexus-simbolo-claro.png` | símbolo em uma cor, fundo claro / escuro |

## Elemento gráfico
- **Cantos cortados na diagonal** (como o símbolo: corte no canto de cima à esquerda e no de baixo à
  direita). Usado em selos de destaque e etiquetas: `clip-path: polygon(.32em 0, 100% 0, 100% calc(100% - .32em), calc(100% - .32em) 100%, 0 100%, 0 .32em)`.
- Símbolo grande e bem transparente (~6%) saindo pelo canto de baixo à direita das folhas.

## Tipografia
- **Plus Jakarta Sans** (Google Fonts) — títulos 800 e texto 400–700. **Provisória:** escolhida por ser
  parecida com a do logo; troque aqui quando o dono informar a fonte oficial.
- **JetBrains Mono** — tempos, etiquetas pequenas, rodapés.
