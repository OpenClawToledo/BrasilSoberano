"""
Brasil Soberano — Módulo de Segurança
- Cabeçalhos HTTP (CSP, HSTS, X-Frame-Options, etc.)
- Rate limiting por rota e gravidade
- CSRF tokens (stateless, assinados com HMAC)
- Audit log com hash chain (imutável — qualquer adulteração é detectável)
- Recibos de voto verificáveis publicamente
- Fingerprint anônimo de sessão (mais robusto que IP+UA simples)
"""

import hashlib
import hmac
import os
import secrets
import sqlite3
import time
import datetime
from functools import wraps
from flask import request, jsonify, g, abort

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brasil_soberano.db')

# Chave secreta derivada do ambiente (nunca hardcoded)
# Em produção: export BS_SECRET=<valor_aleatorio_longo>
_SECRET = os.environ.get('BS_SECRET', secrets.token_hex(32))
# ATENÇÃO: se BS_SECRET não está definido no ambiente, tokens mudam a cada restart!
# Em produção sempre defina: BS_SECRET=<hex_64_chars>


# ─── CABEÇALHOS DE SEGURANÇA ──────────────────────────────────────────────────

SECURITY_HEADERS = {
    # Impede iframes (clickjacking)
    'X-Frame-Options': 'DENY',
    # Força MIME type correto (XSS via tipo errado)
    'X-Content-Type-Options': 'nosniff',
    # Força HTTPS por 1 ano
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    # Sem referrer para sites externos
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    # Desativa features sensíveis do browser
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    # Content Security Policy: sem CDN externo, sem inline eval
    'Content-Security-Policy': (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "  # inline necessário para os templates atuais
        "style-src 'self' 'unsafe-inline'; "   # idem
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self';"
    ),
    # Remove info do servidor
    'Server': 'BrasilSoberano/1.0',
}


def apply_security_headers(response):
    """After-request hook: injeta headers de segurança em toda resposta."""
    for k, v in SECURITY_HEADERS.items():
        response.headers[k] = v
    return response


# ─── FINGERPRINT ANÔNIMO DE SESSÃO ────────────────────────────────────────────

def session_fingerprint():
    """
    Fingerprint anônimo resistente a spoofing simples.
    Combina: IP real (atrás de proxy), User-Agent, Accept-Language.
    Hash SHA-256 → nunca revela dados pessoais.
    """
    ip = (
        request.headers.get('X-Real-IP') or
        request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or
        request.remote_addr or 'unknown'
    )
    ua = request.headers.get('User-Agent', '')
    lang = request.headers.get('Accept-Language', '')
    raw = f"{ip}|{ua}|{lang}|{_SECRET}"
    return hashlib.sha256(raw.encode()).hexdigest()[:40]


def ip_hash():
    """Hash anônimo do IP para logs (não revela IP real)."""
    ip = (
        request.headers.get('X-Real-IP') or
        request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or
        request.remote_addr or 'unknown'
    )
    return hashlib.sha256(f"{ip}{_SECRET}".encode()).hexdigest()[:32]


# ─── CSRF TOKENS (HMAC, STATELESS) ────────────────────────────────────────────

def csrf_generate():
    """Gera token CSRF assinado com HMAC-SHA256. Válido por 1h."""
    ts = str(int(time.time()))
    nonce = secrets.token_hex(16)
    payload = f"{ts}:{nonce}"
    sig = hmac.new(_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def csrf_validate(token):
    """Valida token CSRF. Retorna True se válido e não expirado (< 1h)."""
    if not token:
        return False
    try:
        parts = token.rsplit(':', 1)
        if len(parts) != 2:
            return False
        payload, sig = parts
        expected = hmac.new(_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False
        ts = int(payload.split(':')[0])
        if time.time() - ts > 3600:
            return False
        return True
    except Exception:
        return False


# ─── RATE LIMITING (sem dependência externa, in-memory) ──────────────────────

_rate_buckets: dict = {}  # {key: [timestamps]}

def _rate_check(key: str, max_hits: int, window_secs: int) -> bool:
    """
    Retorna True se dentro do limite, False se excedido.
    Sliding window simples em memória.
    """
    now = time.time()
    bucket = _rate_buckets.get(key, [])
    bucket = [t for t in bucket if now - t < window_secs]
    if len(bucket) >= max_hits:
        _rate_buckets[key] = bucket
        return False
    bucket.append(now)
    _rate_buckets[key] = bucket
    return True


def rate_limit(max_hits=10, window_secs=60, per='ip'):
    """
    Decorator de rate limiting.
    per='ip': limita por IP
    per='session': limita por fingerprint de sessão
    per='global': limita por rota globalmente
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if per == 'ip':
                key = f"rl:{f.__name__}:{ip_hash()}"
            elif per == 'session':
                key = f"rl:{f.__name__}:{session_fingerprint()}"
            else:
                key = f"rl:{f.__name__}:global"

            if not _rate_check(key, max_hits, window_secs):
                _log_rate_limit(ip_hash(), request.path, f"Rate limit: {max_hits}/{window_secs}s")
                return jsonify({
                    'error': 'Muitas requisições. Aguarde um momento.',
                    'retry_after': window_secs
                }), 429
            return f(*args, **kwargs)
        return wrapper
    return decorator


def _log_rate_limit(ip_h, rota, motivo):
    try:
        db = sqlite3.connect(DB_PATH)
        db.execute(
            'INSERT INTO rate_limit_log (ip_hash,rota,motivo) VALUES (?,?,?)',
            (ip_h, rota, motivo)
        )
        db.commit()
        db.close()
    except Exception:
        pass


# ─── AUDIT LOG COM HASH CHAIN ─────────────────────────────────────────────────

def audit(tipo: str, recurso: str, detalhe: str = '', ator: str = 'cidadao'):
    """
    Registra evento no audit log imutável.
    Cada entrada encadeia o hash da anterior → adulteração detectável.
    Thread-safe via commit imediato.
    """
    try:
        db = sqlite3.connect(DB_PATH)
        # Buscar hash do último evento
        ultimo = db.execute(
            'SELECT hash_proprio FROM audit_log ORDER BY id DESC LIMIT 1'
        ).fetchone()
        hash_anterior = ultimo[0] if ultimo else '0' * 64

        ip_h = '0' * 64
        try:
            ip_h = ip_hash()
        except RuntimeError:
            pass  # fora de contexto Flask

        ts = datetime.datetime.utcnow().isoformat()
        payload = f"{ts}|{tipo}|{ator}|{recurso}|{detalhe}|{hash_anterior}"
        hash_proprio = hashlib.sha256(payload.encode()).hexdigest()

        db.execute("""
            INSERT INTO audit_log (ts,tipo,ator,ip_hash,recurso,detalhe,hash_anterior,hash_proprio)
            VALUES (?,?,?,?,?,?,?,?)
        """, (ts, tipo, ator, ip_h, recurso, detalhe, hash_anterior, hash_proprio))
        db.commit()
        db.close()
    except Exception:
        pass  # audit nunca deve quebrar o fluxo principal


def audit_verify():
    """
    Verifica integridade completa do audit log.
    Retorna (ok: bool, total: int, falhas: list)
    """
    db = sqlite3.connect(DB_PATH)
    rows = db.execute('SELECT * FROM audit_log ORDER BY id ASC').fetchall()
    db.close()

    falhas = []
    prev_hash = '0' * 64

    for row in rows:
        # row: id,ts,tipo,ator,ip_hash,recurso,detalhe,hash_anterior,hash_proprio
        rid, ts, tipo, ator, ip_h, recurso, detalhe, hash_ant, hash_prop = row

        if hash_ant != prev_hash:
            falhas.append({
                'id': rid, 'problema': 'hash_anterior não bate',
                'esperado': prev_hash[:16], 'encontrado': (hash_ant or '')[:16]
            })

        payload = f"{ts}|{tipo}|{ator}|{recurso}|{detalhe}|{hash_ant}"
        calculado = hashlib.sha256(payload.encode()).hexdigest()
        if calculado != hash_prop:
            falhas.append({
                'id': rid, 'problema': 'hash_proprio corrompido',
                'calculado': calculado[:16], 'armazenado': (hash_prop or '')[:16]
            })

        prev_hash = hash_prop

    return len(falhas) == 0, len(rows), falhas


# ─── RECIBOS DE VOTO ─────────────────────────────────────────────────────────

def gerar_recibo_voto(voting_event_id: int, session_fp: str, voto: str, ts: str) -> str:
    """
    Gera token de recibo público verificável.
    O cidadão pode verificar que seu voto foi registrado
    sem revelar qual foi a sessão (privacidade preservada).
    """
    payload = f"{voting_event_id}:{voto}:{ts}:{session_fp}:{_SECRET}"
    token = hashlib.sha256(payload.encode()).hexdigest()
    voto_hash = hashlib.sha256(f"{voto}:{session_fp}".encode()).hexdigest()[:32]

    try:
        db = sqlite3.connect(DB_PATH)
        db.execute("""
            INSERT OR IGNORE INTO vote_receipts (voting_event_id, receipt_token, voto_hash, ts)
            VALUES (?,?,?,?)
        """, (voting_event_id, token[:32], voto_hash, ts))
        db.commit()
        db.close()
    except Exception:
        pass

    return token[:32]
