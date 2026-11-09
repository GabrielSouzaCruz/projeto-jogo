"""
Gera as texturas do jogo proceduralmente (desenhadas por código com pygame).

Origem das imagens: criadas pelo próprio projeto, sem uso de imagens de terceiros.
Execute diretamente para recriar os arquivos em assets/texturas/:

    python ferramentas/gerar_texturas.py
"""
import os
import random

import pygame


def _limitar(v):
    return max(0, min(255, v))


def _ruido(superficie, intensidade, semente):
    rnd = random.Random(semente)
    w, h = superficie.get_size()
    for y in range(h):
        for x in range(w):
            r, g, b, a = superficie.get_at((x, y))
            d = rnd.randint(-intensidade, intensidade)
            superficie.set_at((x, y), (_limitar(r + d), _limitar(g + d), _limitar(b + d), a))


def piso_metal(tam=128):
    """Placa de piso metálica antiderrapante. Feita para repetir sem emendas visíveis."""
    s = pygame.Surface((tam, tam))
    s.fill((64, 70, 80))
    _ruido(s, 6, 1)
    passo = 16
    for gy in range(passo, tam - passo, passo):
        for gx in range(passo, tam - passo, passo):
            cx, cy = gx + passo // 2, gy + passo // 2
            if (gx // passo + gy // passo) % 2 == 0:
                a, b = (cx - 4, cy - 4), (cx + 4, cy + 4)
            else:
                a, b = (cx - 4, cy + 4), (cx + 4, cy - 4)
            pygame.draw.line(s, (34, 37, 44), (a[0] + 1, a[1] + 1), (b[0] + 1, b[1] + 1), 3)
            pygame.draw.line(s, (112, 120, 132), a, b, 2)
    # junta entre placas
    pygame.draw.rect(s, (22, 24, 29), (0, 0, tam, tam), 3)
    pygame.draw.line(s, (108, 116, 128), (3, 3), (tam - 4, 3))
    pygame.draw.line(s, (108, 116, 128), (3, 3), (3, tam - 4))
    # rebites
    for x, y in [(9, 9), (tam - 10, 9), (9, tam - 10), (tam - 10, tam - 10)]:
        pygame.draw.circle(s, (30, 32, 38), (x + 1, y + 1), 4)
        pygame.draw.circle(s, (150, 158, 170), (x, y), 3)
        pygame.draw.circle(s, (200, 206, 214), (x - 1, y - 1), 1)
    return s


def caixa(tam=128):
    """Caixa de manutenção com faixas de perigo e símbolo de energia."""
    s = pygame.Surface((tam, tam))
    s.fill((22, 22, 24))
    largura = 12
    for k in range(-tam, 2 * tam, 2 * largura):
        pygame.draw.polygon(s, (232, 182, 34),
                            [(k, 0), (k + largura, 0), (k + largura - tam, tam), (k - tam, tam)])
    m = 14
    interno = pygame.Rect(m, m, tam - 2 * m, tam - 2 * m)
    pygame.draw.rect(s, (196, 102, 30), interno)
    # reforços em X
    pygame.draw.line(s, (130, 64, 18), interno.topleft, interno.bottomright, 8)
    pygame.draw.line(s, (130, 64, 18), interno.topright, interno.bottomleft, 8)
    pygame.draw.line(s, (224, 132, 52), interno.topleft, interno.bottomright, 3)
    pygame.draw.line(s, (224, 132, 52), interno.topright, interno.bottomleft, 3)
    # símbolo central (raio)
    c = tam // 2
    pygame.draw.circle(s, (34, 30, 28), (c, c), 20)
    pygame.draw.circle(s, (232, 182, 34), (c, c), 20, 3)
    pygame.draw.polygon(s, (240, 196, 50),
                        [(c + 3, c - 14), (c - 7, c + 2), (c - 1, c + 2),
                         (c - 4, c + 14), (c + 7, c - 3), (c + 1, c - 3)])
    pygame.draw.rect(s, (90, 46, 14), interno, 3)
    pygame.draw.rect(s, (12, 12, 14), (0, 0, tam, tam), 3)
    _ruido(s, 8, 2)
    return s


def parede_painel(tam=128):
    """Painel de parede com faixa de luz e ventilação."""
    s = pygame.Surface((tam, tam))
    s.fill((36, 42, 54))
    p = pygame.Rect(6, 6, tam - 12, tam - 12)
    pygame.draw.rect(s, (56, 64, 80), p)
    pygame.draw.line(s, (86, 96, 116), p.topleft, p.topright, 2)
    pygame.draw.line(s, (86, 96, 116), p.topleft, p.bottomleft, 2)
    pygame.draw.line(s, (22, 26, 34), p.bottomleft, p.bottomright, 2)
    pygame.draw.line(s, (22, 26, 34), p.topright, p.bottomright, 2)
    # faixa de luz (perto do topo da parede)
    pygame.draw.rect(s, (40, 110, 130), (6, 20, tam - 12, 10))
    pygame.draw.rect(s, (90, 220, 240), (6, 23, tam - 12, 4))
    # ventilação
    for i in range(6):
        pygame.draw.rect(s, (18, 20, 26), (24 + i * 14, 92, 8, 18))
        pygame.draw.line(s, (80, 88, 104), (24 + i * 14, 110), (31 + i * 14, 110))
    # parafusos
    for x, y in [(12, 40), (tam - 13, 40), (12, tam - 13), (tam - 13, tam - 13)]:
        pygame.draw.circle(s, (110, 118, 132), (x, y), 2)
    pygame.draw.line(s, (16, 18, 24), (0, 0), (0, tam), 2)
    _ruido(s, 5, 3)
    return s


TEXTURAS = {
    "piso_metal.png": piso_metal,
    "caixa.png": caixa,
    "parede_painel.png": parede_painel,
}


def gerar_todas(pasta):
    os.makedirs(pasta, exist_ok=True)
    for nome, funcao in TEXTURAS.items():
        pygame.image.save(funcao(), os.path.join(pasta, nome))


if __name__ == "__main__":
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    destino = os.path.join(raiz, "assets", "texturas")
    gerar_todas(destino)
    print("Texturas geradas em", destino)
