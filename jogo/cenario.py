"""
Cenário fixo: piso, paredes, céu estrelado, marcador da luz e limites da arena.
"""
import math
import random

from OpenGL.GL import (
    GL_FOG, GL_LINE_LOOP, GL_LINES, GL_POINTS, glBegin, glColor4f, glDepthMask,
    glDisable, glEnable, glEnd, glLineWidth, glPointSize, glPopMatrix, glPushMatrix,
    glTranslatef, glVertex3f,
)

from . import config, texturas
from .iluminacao import com_iluminacao, material, sem_iluminacao
from .primitivas import cilindro, cubo, esfera, grade


class Cenario:
    def __init__(self, tex):
        self.tex = tex
        m = config.ARENA_MEIA
        h = config.ALTURA_PAREDE
        rep = config.REPETICOES_PISO
        n = config.SUBDIVISOES_PISO

        # Piso: UV de 0 a 14 -> textura repetida 14x14 (GL_REPEAT)
        self.piso = grade((-m, 0, m), (2 * m, 0, 0), (0, 0, -2 * m), (0, 1, 0),
                          n, n, rep, rep, nome="piso")

        # Paredes com normais apontando para dentro da arena
        ru = 2 * m / config.TAMANHO_PAINEL_PAREDE
        rv = h / config.TAMANHO_PAINEL_PAREDE
        defs = [
            ((-m, 0, -m), (2 * m, 0, 0), (0, 0, 1)),     # fundo  (z = -m)
            ((m, 0, m), (-2 * m, 0, 0), (0, 0, -1)),     # frente (z = +m)
            ((-m, 0, m), (0, 0, -2 * m), (1, 0, 0)),     # esquerda
            ((m, 0, -m), (0, 0, 2 * m), (-1, 0, 0)),     # direita
        ]
        self.paredes = [grade(o, u, (0, h, 0), nrm, 24, 4, ru, rv, nome="parede")
                        for o, u, nrm in defs]
        self.trilho_x = cubo(2 * m + 0.6, 0.3, 0.3, subdiv=2)
        self.trilho_z = cubo(0.3, 0.3, 2 * m + 0.6, subdiv=2)
        self.plataforma = cilindro(1.4, 0.06, 32)
        self.marcador_luz = esfera(0.25, 16, 10)

        rnd = random.Random(7)
        self.estrelas = []
        for _ in range(700):
            th = rnd.uniform(0, 2 * math.pi)
            y = rnd.uniform(0.08, 1.0)
            r = math.sqrt(1 - y * y)
            self.estrelas.append((90 * r * math.cos(th), 90 * y, 90 * r * math.sin(th),
                                  rnd.uniform(0.3, 1.0)))

    def desenhar_ceu(self):
        sem_iluminacao()
        texturas.nenhuma()
        glDisable(GL_FOG)
        glDepthMask(False)
        glPointSize(2.0)
        glBegin(GL_POINTS)                       # primitiva: pontos
        for x, y, z, b in self.estrelas:
            glColor4f(b, b, b * 1.1, 1.0)
            glVertex3f(x, y, z)
        glEnd()
        glDepthMask(True)
        glEnable(GL_FOG)
        com_iluminacao()

    def desenhar(self, luz_ligada):
        m = config.ARENA_MEIA
        h = config.ALTURA_PAREDE

        # piso metálico texturizado, com um leve especular
        texturas.usar(self.tex["piso_metal"])
        material((0.9, 0.92, 1.0), especular=(0.35, 0.35, 0.4), brilho=24)
        self.piso.desenhar()

        texturas.usar(self.tex["parede_painel"])
        material((0.9, 0.92, 1.0), especular=(0.2, 0.2, 0.25), brilho=16)
        for p in self.paredes:
            p.desenhar()
        texturas.nenhuma()

        material((0.25, 0.27, 0.32), especular=(0.6, 0.6, 0.6), brilho=40)
        for z in (-m, m):
            glPushMatrix()
            glTranslatef(0, h + 0.15, z)
            self.trilho_x.desenhar()
            glPopMatrix()
        for x in (-m, m):
            glPushMatrix()
            glTranslatef(x, h + 0.15, 0)
            self.trilho_z.desenhar()
            glPopMatrix()

        # plataforma de início
        material((0.2, 0.25, 0.32), especular=(0.6, 0.6, 0.6), brilho=50,
                 emissao=(0.0, 0.05, 0.08))
        glPushMatrix()
        glTranslatef(config.DRONE_INICIO[0], 0.0, config.DRONE_INICIO[1])
        self.plataforma.desenhar()
        glPopMatrix()

        # marcador da posição da luz
        lx, ly, lz, _ = config.LUZ_POSICAO
        if luz_ligada:
            material((1, 1, 0.8), emissao=(1.0, 0.92, 0.6))
        else:
            material((0.2, 0.2, 0.2), especular=(0.5, 0.5, 0.5), brilho=30)
        glPushMatrix()
        glTranslatef(lx, ly, lz)
        self.marcador_luz.desenhar()
        glPopMatrix()

    def desenhar_efeitos(self, luz_ligada):
        lim = config.ARENA_MEIA - 0.4
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)                    # limite de movimentação no chão
        glColor4f(1.0, 0.6, 0.1, 0.35)
        for x, z in [(-lim, -lim), (lim, -lim), (lim, lim), (-lim, lim)]:
            glVertex3f(x, 0.02, z)
        glEnd()

        sx, sz = config.DRONE_INICIO
        glBegin(GL_LINE_LOOP)
        glColor4f(0.3, 0.8, 1.0, 0.5)
        for k in range(32):
            a = 2 * math.pi * k / 32
            glVertex3f(sx + 1.5 * math.cos(a), 0.08, sz + 1.5 * math.sin(a))
        glEnd()

        if luz_ligada:
            lx, ly, lz, _ = config.LUZ_POSICAO
            glBegin(GL_LINES)                    # "fio" mostrando onde a luz está
            glColor4f(1.0, 0.9, 0.5, 0.4)
            glVertex3f(lx, ly, lz)
            glColor4f(1.0, 0.9, 0.5, 0.0)
            glVertex3f(lx, 0.0, lz)
            glEnd()
