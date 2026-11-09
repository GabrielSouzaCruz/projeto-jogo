"""
Primitivas geométricas construídas por código.

Cada objeto é descrito em COORDENADAS LOCAIS (centrado na própria origem) com:
  - posições dos vértices
  - normais (para a iluminação)
  - coordenadas de textura (u, v)

As faces são enviadas ao OpenGL como GL_TRIANGLES (3 vértices) ou GL_QUADS
(4 vértices) e gravadas em uma display list, para desenhar rápido a cada quadro.
O posicionamento no mundo é feito depois, com glTranslate/glRotate/glScale.
"""
import math

from OpenGL.GL import (
    GL_COMPILE, GL_LINES, GL_QUADS, GL_TRIANGLES, glBegin, glCallList, glEnd,
    glEndList, glGenLists, glNewList, glNormal3f, glTexCoord2f, glVertex3f,
)


# ---------------------------------------------------------------------------
# Álgebra vetorial mínima
# ---------------------------------------------------------------------------
def _soma(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _normalizar(a):
    n = math.sqrt(_dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n) if n > 1e-12 else (0.0, 1.0, 0.0)


def _normal_newell(pontos):
    """Normal geométrica de um polígono (método de Newell; robusto a vértices repetidos)."""
    nx = ny = nz = 0.0
    for i, p in enumerate(pontos):
        q = pontos[(i + 1) % len(pontos)]
        nx += (p[1] - q[1]) * (p[2] + q[2])
        ny += (p[2] - q[2]) * (p[0] + q[0])
        nz += (p[0] - q[0]) * (p[1] + q[1])
    return (nx, ny, nz)


# ---------------------------------------------------------------------------
# Malha
# ---------------------------------------------------------------------------
class Malha:
    """Conjunto de faces (triângulos e quadriláteros) com normais e UVs."""

    # Quando True, desenhar() mostra as normais (tecla N) em vez das faces.
    modo_normais = False

    def __init__(self, nome="malha"):
        self.nome = nome
        self.triangulos = []
        self.quads = []
        self._lista = None
        self._lista_normais = None

    def face(self, pontos, normais, uvs=None):
        """Adiciona uma face. Garante sentido anti-horário visto pelo lado da normal,
        para o back-face culling (GL_CULL_FACE) funcionar corretamente."""
        if uvs is None:
            uvs = [(0.0, 0.0)] * len(pontos)
        normal_media = (sum(n[0] for n in normais), sum(n[1] for n in normais),
                        sum(n[2] for n in normais))
        if _dot(_normal_newell(pontos), normal_media) < 0:
            pontos, normais, uvs = pontos[::-1], normais[::-1], uvs[::-1]
        destino = self.triangulos if len(pontos) == 3 else self.quads
        destino.append(list(zip(pontos, normais, uvs)))
        return self

    def _emitir(self, modo, faces):
        if not faces:
            return
        glBegin(modo)
        for face in faces:
            for p, n, uv in face:
                glNormal3f(*n)
                glTexCoord2f(*uv)
                glVertex3f(*p)
        glEnd()

    def compilar(self):
        self._lista = glGenLists(1)
        glNewList(self._lista, GL_COMPILE)
        self._emitir(GL_TRIANGLES, self.triangulos)
        self._emitir(GL_QUADS, self.quads)
        glEndList()

    def desenhar(self):
        if Malha.modo_normais:
            self.desenhar_normais()
            return
        if self._lista is None:
            self.compilar()
        glCallList(self._lista)

    def desenhar_normais(self, comprimento=0.3):
        """Desenha cada normal como um segmento (primitiva GL_LINES)."""
        if self._lista_normais is None:
            self._lista_normais = glGenLists(1)
            glNewList(self._lista_normais, GL_COMPILE)
            glBegin(GL_LINES)
            for face in self.triangulos + self.quads:
                for p, n, _ in face:
                    glVertex3f(*p)
                    glVertex3f(*_soma(p, _mul(n, comprimento)))
            glEnd()
            glEndList()
        glCallList(self._lista_normais)


# ---------------------------------------------------------------------------
# Geradores de formas
# ---------------------------------------------------------------------------
def grade(origem, eixo_u, eixo_v, normal, nu, nv, rep_u=1.0, rep_v=1.0, nome="grade"):
    """Retângulo subdividido em nu x nv quadriláteros.

    Ponto(s, t) = origem + s*eixo_u + t*eixo_v, com s, t em [0, 1].
    UV = (s*rep_u, t*rep_v): valores acima de 1 fazem a textura REPETIR (GL_REPEAT).
    """
    m = Malha(nome)

    def ponto(s, t):
        return _soma(origem, _soma(_mul(eixo_u, s), _mul(eixo_v, t)))

    for i in range(nu):
        for j in range(nv):
            s0, s1 = i / nu, (i + 1) / nu
            t0, t1 = j / nv, (j + 1) / nv
            pts = [ponto(s0, t0), ponto(s1, t0), ponto(s1, t1), ponto(s0, t1)]
            uvs = [(s0 * rep_u, t0 * rep_v), (s1 * rep_u, t0 * rep_v),
                   (s1 * rep_u, t1 * rep_v), (s0 * rep_u, t1 * rep_v)]
            m.face(pts, [normal] * 4, uvs)
    return m


# Cada face do cubo: (normal, eixo u, eixo v), com u x v = normal
_FACES_CUBO = [
    ((1, 0, 0), (0, 0, -1), (0, 1, 0)),
    ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
    ((0, 1, 0), (1, 0, 0), (0, 0, -1)),
    ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
    ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
    ((0, 0, -1), (-1, 0, 0), (0, 1, 0)),
]


def _eixo(v):
    return next(k for k in range(3) if abs(v[k]) > 0.5)


def cubo(sx=1.0, sy=1.0, sz=1.0, subdiv=1, uv_por_unidade=None, nome="cubo"):
    """Paralelepípedo centrado na origem.

    uv_por_unidade=None -> cada face recebe a textura inteira (0..1).
    uv_por_unidade=k     -> UV proporcional ao tamanho real da face, evitando
                            esticar a textura em caixas não cúbicas.
    """
    m = Malha(nome)
    dims = (sx, sy, sz)
    for normal, eu, ev in _FACES_CUBO:
        tu, tv = dims[_eixo(eu)], dims[_eixo(ev)]
        centro = tuple(normal[k] * dims[k] / 2 for k in range(3))
        origem = _soma(centro, _soma(_mul(eu, -tu / 2), _mul(ev, -tv / 2)))
        ru = tu * uv_por_unidade if uv_por_unidade else 1.0
        rv = tv * uv_por_unidade if uv_por_unidade else 1.0
        g = grade(origem, _mul(eu, tu), _mul(ev, tv), normal, subdiv, subdiv, ru, rv)
        m.quads.extend(g.quads)
    return m


def octaedro(raio=0.35, altura=0.6, nome="octaedro"):
    """Cristal de 8 triângulos com normais planas (uma por face)."""
    m = Malha(nome)
    topo, base = (0.0, altura, 0.0), (0.0, -altura, 0.0)
    eq = [(raio * math.cos(a), 0.0, raio * math.sin(a))
          for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)]
    for i in range(4):
        a, b = eq[i], eq[(i + 1) % 4]
        for apice in (topo, base):
            pts = [apice, a, b]
            n = _normalizar(_normal_newell(pts))
            centro = _mul(_soma(_soma(apice, a), b), 1 / 3)
            if _dot(n, centro) < 0:
                n = _mul(n, -1)
            m.face(pts, [n] * 3, [(0.5, 1.0), (0.0, 0.0), (1.0, 0.0)])
    return m


def esfera(raio=1.0, fatias=20, pilhas=12, hemisferio=False, nome="esfera"):
    """Esfera (ou hemisfério superior) com normais suaves = posição normalizada."""
    m = Malha(nome)
    phi_max = math.pi / 2 if hemisferio else math.pi

    def vert(i, j):
        phi = phi_max * i / pilhas
        th = 2 * math.pi * j / fatias
        n = (math.sin(phi) * math.cos(th), math.cos(phi), math.sin(phi) * math.sin(th))
        return _mul(n, raio), n, (j / fatias, 1 - i / pilhas)

    for i in range(pilhas):
        for j in range(fatias):
            vs = [vert(i, j), vert(i + 1, j), vert(i + 1, j + 1), vert(i, j + 1)]
            m.face([v[0] for v in vs], [v[1] for v in vs], [v[2] for v in vs])
    return m


def toro(raio_maior=1.0, raio_menor=0.2, seg_maior=40, seg_menor=12, nome="toro"):
    """Anel no plano XY (furo voltado para o eixo Z)."""
    m = Malha(nome)

    def vert(i, j):
        u = 2 * math.pi * i / seg_maior
        v = 2 * math.pi * j / seg_menor
        n = (math.cos(v) * math.cos(u), math.cos(v) * math.sin(u), math.sin(v))
        centro = (raio_maior * math.cos(u), raio_maior * math.sin(u), 0.0)
        return _soma(centro, _mul(n, raio_menor)), n, (i / seg_maior, j / seg_menor)

    for i in range(seg_maior):
        for j in range(seg_menor):
            vs = [vert(i, j), vert(i + 1, j), vert(i + 1, j + 1), vert(i, j + 1)]
            m.face([v[0] for v in vs], [v[1] for v in vs], [v[2] for v in vs])
    return m


def cilindro(raio=1.0, altura=1.0, segmentos=24, tampas=True, nome="cilindro"):
    """Cilindro de y=0 até y=altura. Lateral em quads, tampas em triângulos."""
    m = Malha(nome)
    for i in range(segmentos):
        a0 = 2 * math.pi * i / segmentos
        a1 = 2 * math.pi * (i + 1) / segmentos
        n0 = (math.cos(a0), 0.0, math.sin(a0))
        n1 = (math.cos(a1), 0.0, math.sin(a1))
        p00, p10 = _mul(n0, raio), _mul(n1, raio)
        p01 = (p00[0], altura, p00[2])
        p11 = (p10[0], altura, p10[2])
        u0, u1 = i / segmentos, (i + 1) / segmentos
        m.face([p00, p10, p11, p01], [n0, n1, n1, n0], [(u0, 0), (u1, 0), (u1, 1), (u0, 1)])
        if tampas:
            m.face([(0.0, altura, 0.0), p01, p11], [(0, 1, 0)] * 3)
            m.face([(0.0, 0.0, 0.0), p10, p00], [(0, -1, 0)] * 3)
    return m
