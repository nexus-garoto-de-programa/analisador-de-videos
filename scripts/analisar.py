#!/usr/bin/env python3
"""Extrai tudo que dá para medir de um vídeo curto (Reels/TikTok/Shorts).

Uso:
    .venv/bin/python scripts/analisar.py <link-ou-arquivo> [--saida DIR] [--cookies cookies.txt]

Gera, na pasta de saída:
    video.mp4              o vídeo (não vai para o git)
    metadados.json         título, legenda, autor, métricas, música (quando o Instagram informa)
    cortes.json            cada plano (início, fim, duração) detectado por mudança de cena
    audio.json             energia ao longo do tempo, picos, silêncios, BPM estimado
    transcricao.{json,srt,txt}  fala com tempo por palavra
    musica.json            reconhecimento da música (Shazam), quando possível
    frames/                frames do gancho (0–3 s), um frame por plano, folhas de contato
    relatorio_tecnico.md   resumo de tudo acima, para o Claude ler antes de assistir aos frames

O script só mede. Quem interpreta (gancho, efeitos, estrutura) é o Claude, seguindo metodo/METODO.md.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
import os
import re
import shutil
import subprocess
import sys
import wave
from dataclasses import dataclass
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Limiar de mudança de cena do ffmpeg (0–1). 0.3 pega cortes secos sem confundir
# movimento de câmera; vídeos com muita transição suave podem pedir 0.2.
LIMIAR_CENA_PADRAO = 0.3
GANCHO_S = 3.0
GANCHO_PASSO_S = 0.5
MAX_FRAMES_PLANOS = 60
LARGURA_FRAME = 480
LARGURA_MINIATURA = 216


def log(msg: str) -> None:
    print(f"› {msg}", flush=True)


def rodar(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def eh_link(origem: str) -> bool:
    return re.match(r"^https?://", origem) is not None


def slug(texto: str, limite: int = 40) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", texto.lower()).strip("-")
    return s[:limite].strip("-") or "video"


def id_do_link(url: str) -> str:
    m = re.search(r"/(?:reel|reels|p|tv|shorts|video)/([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else slug(url)


# ---------------------------------------------------------------- download


def baixar(url: str, pasta: Path, cookies: Path | None) -> dict:
    import yt_dlp

    opcoes = {
        "outtmpl": str(pasta / "video.%(ext)s"),
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    if cookies:
        opcoes["cookiefile"] = str(cookies)
    with yt_dlp.YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(url, download=True)
    if info.get("_type") == "playlist" and info.get("entries"):
        info = info["entries"][0]
    campos = [
        "id", "title", "description", "uploader", "uploader_id", "channel",
        "upload_date", "duration", "view_count", "like_count", "comment_count",
        "track", "artist", "webpage_url", "extractor", "width", "height", "fps",
    ]
    return {c: info.get(c) for c in campos if info.get(c) is not None}


def achar_video(pasta: Path) -> Path:
    for ext in ("mp4", "mkv", "webm", "mov"):
        p = pasta / f"video.{ext}"
        if p.exists():
            return p
    raise SystemExit("Download terminou mas o arquivo de vídeo não apareceu.")


# ---------------------------------------------------------------- ffprobe


@dataclass
class InfoVideo:
    duracao: float
    largura: int
    altura: int
    fps: float
    tem_audio: bool


def sondar(video: Path) -> InfoVideo:
    r = rodar([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(video),
    ])
    dados = json.loads(r.stdout)
    v = next(s for s in dados["streams"] if s["codec_type"] == "video")
    num, den = (v.get("avg_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den) if float(den) else 0.0
    largura, altura = int(v["width"]), int(v["height"])
    rot = int((v.get("tags") or {}).get("rotate", 0) or 0)
    for sd in v.get("side_data_list", []):
        rot = int(sd.get("rotation", rot) or rot)
    if abs(rot) in (90, 270):
        largura, altura = altura, largura
    return InfoVideo(
        duracao=float(dados["format"]["duration"]),
        largura=largura,
        altura=altura,
        fps=round(fps, 2),
        tem_audio=any(s["codec_type"] == "audio" for s in dados["streams"]),
    )


# ---------------------------------------------------------------- cortes


def detectar_cortes(video: Path, duracao: float, limiar: float) -> list[dict]:
    r = rodar([
        "ffmpeg", "-hide_banner", "-i", str(video),
        "-filter:v", f"select='gt(scene,{limiar})',showinfo",
        "-an", "-f", "null", "-",
    ])
    tempos = sorted({round(float(t), 3) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)})
    # Cortes a menos de 0.15 s um do outro são o mesmo corte (flash, transição).
    limpos: list[float] = []
    for t in tempos:
        if 0.15 < t < duracao - 0.05 and (not limpos or t - limpos[-1] >= 0.15):
            limpos.append(t)
    bordas = [0.0, *limpos, duracao]
    return [
        {"plano": i + 1, "inicio": round(a, 3), "fim": round(b, 3), "duracao": round(b - a, 3)}
        for i, (a, b) in enumerate(zip(bordas, bordas[1:]))
    ]


# ---------------------------------------------------------------- frames


def extrair_frame(video: Path, t: float, destino: Path, largura: int = LARGURA_FRAME) -> bool:
    r = rodar([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", f"{max(t, 0):.3f}", "-i", str(video),
        "-frames:v", "1", "-vf", f"scale={largura}:-2", "-q:v", "3", str(destino),
    ])
    return r.returncode == 0 and destino.exists()


def extrair_frames(video: Path, info: InfoVideo, planos: list[dict], pasta: Path) -> dict:
    frames = pasta / "frames"
    frames.mkdir(exist_ok=True)

    gancho = []
    t = 0.0
    while t <= min(GANCHO_S, info.duracao - 0.05) + 1e-6:
        nome = frames / f"gancho_{t:04.1f}s.jpg"
        if extrair_frame(video, t if t > 0 else 0.03, nome):
            gancho.append(nome.name)
        t += GANCHO_PASSO_S

    escolhidos = planos
    if len(planos) > MAX_FRAMES_PLANOS:
        passo = len(planos) / MAX_FRAMES_PLANOS
        escolhidos = [planos[int(i * passo)] for i in range(MAX_FRAMES_PLANOS)]
    por_plano = []
    for p in escolhidos:
        meio = p["inicio"] + p["duracao"] / 2
        nome = frames / f"plano_{p['plano']:03d}_{meio:06.2f}s.jpg"
        if extrair_frame(video, meio, nome):
            por_plano.append({"plano": p["plano"], "t": round(meio, 2), "arquivo": nome.name})

    folhas = montar_folhas_de_contato(video, info, frames)
    return {"gancho": gancho, "planos": por_plano, "folhas_de_contato": folhas}


def montar_folhas_de_contato(video: Path, info: InfoVideo, frames: Path) -> list[str]:
    """Um frame por segundo, 4 colunas x 3 linhas por folha, com o tempo escrito."""
    from PIL import Image, ImageDraw, ImageFont

    tmp = frames / "_seg"
    tmp.mkdir(exist_ok=True)
    rodar([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
        "-vf", f"fps=1,scale={LARGURA_MINIATURA}:-2", "-q:v", "4", str(tmp / "s_%04d.jpg"),
    ])
    imagens = sorted(tmp.glob("s_*.jpg"))
    if not imagens:
        shutil.rmtree(tmp, ignore_errors=True)
        return []
    try:
        fonte = ImageFont.load_default(size=18)
    except TypeError:
        fonte = ImageFont.load_default()
    colunas, linhas = 4, 3
    por_folha = colunas * linhas
    w, h = Image.open(imagens[0]).size
    nomes = []
    for n, inicio in enumerate(range(0, len(imagens), por_folha), start=1):
        lote = imagens[inicio:inicio + por_folha]
        folha = Image.new("RGB", (w * colunas, h * math.ceil(len(lote) / colunas)), "black")
        for i, arq in enumerate(lote):
            img = Image.open(arq).convert("RGB")
            d = ImageDraw.Draw(img)
            rotulo = f"{inicio + i}s"
            d.rectangle([0, 0, 12 * len(rotulo) + 8, 24], fill="black")
            d.text((4, 2), rotulo, fill="yellow", font=fonte)
            folha.paste(img, ((i % colunas) * w, (i // colunas) * h))
        nome = f"linha_do_tempo_{n:02d}.jpg"
        folha.save(frames / nome, quality=80)
        nomes.append(nome)
    shutil.rmtree(tmp, ignore_errors=True)
    return nomes


# ---------------------------------------------------------------- áudio


def extrair_audio(video: Path, destino: Path) -> bool:
    r = rodar([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(destino),
    ])
    return r.returncode == 0 and destino.exists()


def ler_wav(wav: Path):
    import numpy as np

    with wave.open(str(wav)) as w:
        taxa = w.getframerate()
        amostras = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return amostras, taxa


def analisar_audio(wav: Path) -> dict:
    import numpy as np

    amostras, taxa = ler_wav(wav)

    janela = int(taxa * 0.5)
    energia = []
    for i in range(0, len(amostras), janela):
        bloco = amostras[i:i + janela]
        if len(bloco) == 0:
            break
        rms = float(np.sqrt(np.mean(bloco ** 2)) + 1e-9)
        energia.append({"t": round(i / taxa, 2), "db": round(20 * math.log10(rms), 1)})

    picos = [
        {"t": b["t"], "salto_db": round(b["db"] - a["db"], 1)}
        for a, b in zip(energia, energia[1:])
        if b["db"] - a["db"] >= 6 and b["db"] > -30
    ]
    silencios = []
    inicio = None
    for e in energia:
        if e["db"] < -45:
            inicio = e["t"] if inicio is None else inicio
        elif inicio is not None:
            if e["t"] - inicio >= 0.5:
                silencios.append({"inicio": inicio, "fim": e["t"]})
            inicio = None

    return {
        "energia_por_meio_segundo": energia,
        "picos_de_volume": picos,
        "silencios": silencios,
        "bpm_estimado": estimar_bpm(amostras, taxa),
    }


def estimar_bpm(amostras, taxa: int) -> float | None:
    """BPM aproximado por autocorrelação do fluxo espectral. Serve de pista, não de verdade."""
    import numpy as np

    if len(amostras) < taxa * 4:
        return None
    salto = 512
    n_fft = 1024
    quadros = 1 + (len(amostras) - n_fft) // salto
    if quadros < 50:
        return None
    idx = np.arange(n_fft)[None, :] + salto * np.arange(quadros)[:, None]
    espectro = np.abs(np.fft.rfft(amostras[idx] * np.hanning(n_fft), axis=1))
    fluxo = np.maximum(np.diff(np.log1p(espectro), axis=0), 0).sum(axis=1)
    fluxo = fluxo - fluxo.mean()
    if not fluxo.any():
        return None
    ac = np.correlate(fluxo, fluxo, mode="full")[len(fluxo) - 1:]
    qps = taxa / salto
    lag_min, lag_max = int(qps * 60 / 180), int(qps * 60 / 60)
    if lag_max >= len(ac):
        return None
    lag = lag_min + int(np.argmax(ac[lag_min:lag_max]))
    # Interpolação parabólica no pico: o lag inteiro erra alguns BPM.
    a, b, c = ac[lag - 1], ac[lag], ac[lag + 1]
    ajuste = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0.0
    return round(60 * qps / (lag + ajuste), 1)


# ---------------------------------------------------------------- transcrição


def transcrever(wav: Path, modelo: str, idioma: str | None) -> dict:
    from faster_whisper import WhisperModel

    m = WhisperModel(modelo, device="cpu", compute_type="int8")
    # Passa o áudio já decodificado (16 kHz mono): o decodificador do faster-whisper
    # depende da versão do PyAV e quebra com versões novas.
    amostras, _ = ler_wav(wav)
    segmentos, info = m.transcribe(
        amostras, language=idioma, word_timestamps=True, vad_filter=True, beam_size=5,
    )
    saida = []
    for s in segmentos:
        saida.append({
            "inicio": round(s.start, 2),
            "fim": round(s.end, 2),
            "texto": s.text.strip(),
            "palavras": [
                {"p": w.word.strip(), "inicio": round(w.start, 2), "fim": round(w.end, 2)}
                for w in (s.words or [])
            ],
        })
    return {"idioma": info.language, "prob_idioma": round(info.language_probability, 2), "segmentos": saida}


def srt(segmentos: list[dict]) -> str:
    def ts(t: float) -> str:
        ms = int(round(t * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    return "\n".join(
        f"{i}\n{ts(s['inicio'])} --> {ts(s['fim'])}\n{s['texto']}\n"
        for i, s in enumerate(segmentos, start=1)
    )


# ---------------------------------------------------------------- música


def reconhecer_musica(video: Path, pasta: Path, duracao: float) -> list[dict]:
    try:
        from shazamio import Shazam
    except ImportError:
        return []
    # O shazamio deixa sessões do aiohttp abertas e o asyncio reclama no stderr.
    for nome in ("asyncio", "aiohttp_retry"):
        logging.getLogger(nome).setLevel(logging.CRITICAL)

    pontos = sorted({0.0, max(0.0, duracao / 2 - 6)})
    resultados = []

    async def tentar(t: float) -> dict | None:
        trecho = pasta / f"_musica_{int(t)}.mp3"
        rodar([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.2f}",
            "-t", "12", "-i", str(video), "-vn", "-ac", "1", str(trecho),
        ])
        try:
            r = await asyncio.wait_for(Shazam().recognize(str(trecho)), timeout=30)
        finally:
            trecho.unlink(missing_ok=True)
        faixa = r.get("track") if isinstance(r, dict) else None
        if not faixa:
            return None
        return {
            "a_partir_de_s": round(t, 1),
            "titulo": faixa.get("title"),
            "artista": faixa.get("subtitle"),
            "link": faixa.get("url"),
        }

    for t in pontos:
        try:
            achado = asyncio.run(tentar(t))
        except Exception as e:  # rede, API fora do ar etc.: música é opcional
            log(f"reconhecimento de música falhou em {t:.0f}s: {e}")
            continue
        if achado and all(achado["titulo"] != r["titulo"] for r in resultados):
            resultados.append(achado)
    return resultados


# ---------------------------------------------------------------- relatório


def palavras_por_minuto(transcricao: dict) -> float | None:
    palavras = [p for s in transcricao["segmentos"] for p in s["palavras"]]
    if not palavras:
        return None
    falado = sum(s["fim"] - s["inicio"] for s in transcricao["segmentos"])
    return round(len(palavras) / (falado / 60), 0) if falado > 0 else None


def relatorio(pasta: Path, origem: str, meta: dict, info: InfoVideo, planos: list[dict],
              frames: dict, audio: dict | None, transcricao: dict | None, musica: list[dict]) -> str:
    dur = [p["duracao"] for p in planos]
    cortes_gancho = sum(1 for p in planos[1:] if p["inicio"] <= GANCHO_S)
    linhas = [
        f"# Relatório técnico — {meta.get('title') or pasta.name}",
        "",
        "> Dados medidos automaticamente. Não é a análise: é a matéria-prima dela.",
        "",
        "## Ficha",
        f"- Origem: {origem}",
        f"- Autor: {meta.get('uploader') or meta.get('channel') or '—'} (@{meta.get('uploader_id') or '—'})",
        f"- Publicado em: {meta.get('upload_date') or '—'}",
        f"- Duração: {info.duracao:.1f} s · {info.largura}x{info.altura} · {info.fps} fps"
        f" · {'vertical' if info.altura > info.largura else 'horizontal/quadrado'}",
        f"- Métricas: views {meta.get('view_count', '—')} · curtidas {meta.get('like_count', '—')}"
        f" · comentários {meta.get('comment_count', '—')}",
        f"- Áudio informado pela plataforma: {meta.get('track') or '—'} — {meta.get('artist') or '—'}",
        "",
        "### Legenda do post",
        "",
        (meta.get("description") or "—").strip(),
        "",
        "## Ritmo de edição",
        f"- Planos: {len(planos)} · cortes: {len(planos) - 1}",
        f"- Duração média do plano: {sum(dur) / len(dur):.2f} s · mais curto {min(dur):.2f} s · mais longo {max(dur):.2f} s",
        f"- Cortes por segundo: {(len(planos) - 1) / info.duracao:.2f}",
        f"- Cortes nos primeiros {GANCHO_S:.0f} s: {cortes_gancho}",
        "",
        "| Plano | Início | Fim | Duração |",
        "|---|---|---|---|",
        *[f"| {p['plano']} | {p['inicio']:.2f} | {p['fim']:.2f} | {p['duracao']:.2f} |" for p in planos],
        "",
    ]

    if transcricao:
        segs = transcricao["segmentos"]
        primeira = next((s["palavras"][0]["inicio"] for s in segs if s["palavras"]), None)
        linhas += [
            "## Fala",
            f"- Idioma: {transcricao['idioma']} ({transcricao['prob_idioma']})",
            f"- Primeira palavra em: {f'{primeira:.2f} s' if primeira is not None else 'sem fala'}",
            f"- Velocidade: {palavras_por_minuto(transcricao) or '—'} palavras/min",
            "",
            "### Transcrição com tempo",
            "",
            *[f"- `[{s['inicio']:05.2f}–{s['fim']:05.2f}]` {s['texto']}" for s in segs],
            "",
        ]
    else:
        linhas += ["## Fala", "- Sem fala detectada (ou vídeo sem áudio).", ""]

    if audio:
        linhas += [
            "## Som",
            f"- BPM estimado (pista, confira ouvindo a música): {audio['bpm_estimado'] or '—'}",
            "- Picos de volume (possíveis drops, efeitos sonoros, entrada da música): "
            + (", ".join(f"{p['t']:.1f}s (+{p['salto_db']} dB)" for p in audio["picos_de_volume"]) or "nenhum"),
            "- Silêncios ≥ 0,5 s: "
            + (", ".join(f"{s['inicio']:.1f}–{s['fim']:.1f}s" for s in audio["silencios"]) or "nenhum"),
            "",
        ]
    linhas += [
        "## Música reconhecida",
        *([f"- {m['titulo']} — {m['artista']} (trecho a partir de {m['a_partir_de_s']} s) {m['link'] or ''}" for m in musica]
          or ["- Não reconhecida (pode ser áudio original, voz por cima ou falha da consulta)."]),
        "",
        "## Frames para assistir (em `frames/`)",
        f"- Gancho, a cada {GANCHO_PASSO_S} s até {GANCHO_S:.0f} s: " + ", ".join(frames["gancho"]),
        "- Linha do tempo, 1 frame por segundo: " + ", ".join(frames["folhas_de_contato"]),
        f"- Um frame no meio de cada plano ({len(frames['planos'])} arquivos): `plano_NNN_<tempo>s.jpg`",
        "",
    ]
    return "\n".join(linhas)


# ---------------------------------------------------------------- principal


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("origem", help="link do Reels/TikTok/Shorts ou caminho de um arquivo de vídeo")
    ap.add_argument("--saida", type=Path, help="pasta de saída (padrão: analises/AAAA-MM-DD-<id>)")
    ap.add_argument("--cookies", type=Path, help="cookies.txt (formato Netscape) de uma conta logada")
    ap.add_argument("--modelo", default=os.environ.get("WHISPER_MODEL", "small"),
                    help="modelo do Whisper: tiny, base, small, medium, large-v3 (padrão: small)")
    ap.add_argument("--idioma", default="pt", help="idioma da fala; 'auto' para detectar (padrão: pt)")
    ap.add_argument("--limiar", type=float, default=LIMIAR_CENA_PADRAO, help="sensibilidade de corte (0–1)")
    ap.add_argument("--sem-musica", action="store_true", help="não tenta reconhecer a música")
    args = ap.parse_args()

    origem = args.origem.strip()
    nome = id_do_link(origem) if eh_link(origem) else slug(Path(origem).stem)
    pasta = (args.saida or RAIZ / "analises" / f"{date.today().isoformat()}-{nome}").resolve()
    pasta.mkdir(parents=True, exist_ok=True)

    cookies = args.cookies
    if cookies is None and (RAIZ / "cookies.txt").exists():
        cookies = RAIZ / "cookies.txt"
    if cookies is None and os.environ.get("INSTAGRAM_COOKIES"):
        cookies = pasta / "_cookies.txt"
        cookies.write_text(os.environ["INSTAGRAM_COOKIES"])

    meta: dict = {}
    if eh_link(origem):
        log("baixando o vídeo…")
        try:
            meta = baixar(origem, pasta, cookies)
        except Exception as e:
            print(
                "\nNão consegui baixar o vídeo.\n"
                f"Erro: {e}\n\n"
                "O Instagram costuma bloquear downloads sem login vindos de servidores. Saídas:\n"
                "  1. Coloque um cookies.txt de uma conta logada na raiz do repo (ou na variável\n"
                "     INSTAGRAM_COOKIES do ambiente). Veja o README, seção 'Cookies do Instagram'.\n"
                "  2. Baixe o vídeo no celular e envie o arquivo; rode o script com o caminho dele.\n",
                file=sys.stderr,
            )
            sys.exit(2)
        finally:
            if cookies and cookies.name == "_cookies.txt":
                cookies.unlink(missing_ok=True)
        video = achar_video(pasta)
    else:
        arquivo = Path(origem).expanduser().resolve()
        if not arquivo.exists():
            sys.exit(f"Arquivo não encontrado: {arquivo}")
        video = pasta / f"video{arquivo.suffix.lower() or '.mp4'}"
        if arquivo != video:
            shutil.copy2(arquivo, video)
        meta = {"title": arquivo.stem}
    (pasta / "metadados.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    info = sondar(video)
    log(f"{info.duracao:.1f}s, {info.largura}x{info.altura}, áudio: {'sim' if info.tem_audio else 'não'}")

    log("detectando cortes…")
    planos = detectar_cortes(video, info.duracao, args.limiar)
    (pasta / "cortes.json").write_text(json.dumps(planos, indent=2))

    log("extraindo frames…")
    frames = extrair_frames(video, info, planos, pasta)

    audio = transcricao = None
    musica: list[dict] = []
    if info.tem_audio:
        wav = pasta / "audio.wav"
        if extrair_audio(video, wav):
            log("medindo o áudio…")
            audio = analisar_audio(wav)
            (pasta / "audio.json").write_text(json.dumps(audio, indent=2))

            log(f"transcrevendo (Whisper {args.modelo})…")
            transcricao = transcrever(wav, args.modelo, None if args.idioma == "auto" else args.idioma)
            (pasta / "transcricao.json").write_text(json.dumps(transcricao, ensure_ascii=False, indent=2))
            (pasta / "transcricao.srt").write_text(srt(transcricao["segmentos"]))
            (pasta / "transcricao.txt").write_text("\n".join(s["texto"] for s in transcricao["segmentos"]))
            if not transcricao["segmentos"]:
                transcricao = None
            wav.unlink(missing_ok=True)

        if not args.sem_musica:
            log("tentando reconhecer a música…")
            musica = reconhecer_musica(video, pasta, info.duracao)
            (pasta / "musica.json").write_text(json.dumps(musica, ensure_ascii=False, indent=2))

    texto = relatorio(pasta, origem, meta, info, planos, frames, audio, transcricao, musica)
    (pasta / "relatorio_tecnico.md").write_text(texto)
    log("pronto")
    print(pasta)


if __name__ == "__main__":
    main()
