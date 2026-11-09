"""
HUD (textos na tela). O texto é renderizado pelo pygame em uma imagem, enviado
como textura e desenhado num quadrilátero em projeção ortográfica 2D.
"""
from OpenGL.GL import (
    GL_BLEND, GL_CULL_FACE, GL_DEPTH_TEST, GL_FOG, GL_LIGHTING, GL_LINEAR,
    GL_MODELVIEW, GL_ONE_MINUS_SRC_ALPHA, GL_PROJECTION, GL_QUADS, GL_RGBA,
    GL_SRC_ALPHA, GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER,
    GL_UNSIGNED_BYTE, glBegin, glBindTexture, glBlendFunc, glColor4f,
    glDeleteTextures, glDisable, glEnable, glEnd, glGenTextures, glLoadIdentity,
    glMatrixMode, glOrtho, glPopMatrix, glPushMatrix, glTexCoord2f, glTexImage2D,
    glTexParameteri, glVertex2f,
)
import pygame


class Hud:
    def __init__(self, largura, altura):
        self.largura, self.altura = largura, altura
        self.fontes = {}
        self.cache = {}

    def _fonte(self, tamanho):
        if tamanho not in self.fontes:
            self.fontes[tamanho] = pygame.font.Font(None, tamanho)
        return self.fontes[tamanho]

    def _textura(self, texto, tamanho):
        chave = (texto, tamanho)
        if chave not in self.cache:
            if len(self.cache) > 300:
                glDeleteTextures([t for t, _, _ in self.cache.values()])
                self.cache.clear()
            sup = self._fonte(tamanho).render(texto, True, (255, 255, 255))
            dados = pygame.image.tostring(sup, "RGBA", True)
            tid = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tid)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, sup.get_width(), sup.get_height(), 0,
                         GL_RGBA, GL_UNSIGNED_BYTE, dados)
            self.cache[chave] = (tid, sup.get_width(), sup.get_height())
        return self.cache[chave]

    def iniciar(self):
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_FOG)
        glDisable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.largura, self.altura, 0, -1, 1)   # origem no canto superior esquerdo
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

    def finalizar(self):
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)
        glEnable(GL_CULL_FACE)
        glEnable(GL_FOG)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

    def retangulo(self, x, y, w, h, cor):
        glDisable(GL_TEXTURE_2D)
        glColor4f(*cor)
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()

    def texto(self, texto, x, y, tamanho=28, cor=(1, 1, 1), alfa=1.0, ancora="esq"):
        if not texto or alfa <= 0:
            return 0
        tid, w, h = self._textura(texto, tamanho)
        if ancora == "centro":
            x -= w / 2
        elif ancora == "dir":
            x -= w
        # sombra para legibilidade
        for dx, dy, c, a in ((2, 2, (0, 0, 0), 0.6 * alfa), (0, 0, cor, alfa)):
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, tid)
            glColor4f(c[0], c[1], c[2], a)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 1); glVertex2f(x + dx, y + dy)
            glTexCoord2f(1, 1); glVertex2f(x + dx + w, y + dy)
            glTexCoord2f(1, 0); glVertex2f(x + dx + w, y + dy + h)
            glTexCoord2f(0, 0); glVertex2f(x + dx, y + dy + h)
            glEnd()
        return w
