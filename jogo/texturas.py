"""
Carregamento de texturas.

Caminhos são sempre relativos à pasta do projeto (nada fixo do computador).
Se algum PNG estiver faltando, ele é regenerado pelo script de ferramentas/.
"""
import os
import sys

import pygame
from OpenGL.GL import (
    GL_LINEAR, GL_LINEAR_MIPMAP_LINEAR, GL_MODULATE, GL_REPEAT, GL_RGBA,
    GL_TEXTURE_2D, GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER, GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_UNSIGNED_BYTE,
    glBindTexture, glDisable, glEnable, glGenTextures, glTexEnvi, glTexParameteri,
)
from OpenGL.GLU import gluBuild2DMipmaps

from .primitivas import Malha

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_TEXTURAS = os.path.join(RAIZ, "assets", "texturas")
NOMES = ["piso_metal.png", "caixa.png", "parede_painel.png"]


def _garantir_arquivos():
    if all(os.path.exists(os.path.join(PASTA_TEXTURAS, n)) for n in NOMES):
        return
    sys.path.insert(0, os.path.join(RAIZ, "ferramentas"))
    from gerar_texturas import gerar_todas
    gerar_todas(PASTA_TEXTURAS)


def carregar_textura(caminho):
    imagem = pygame.image.load(caminho)
    largura, altura = imagem.get_size()
    # True = inverte verticalmente: no OpenGL a origem (0,0) da textura fica embaixo
    dados = pygame.image.tostring(imagem, "RGBA", True)
    tid = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tid)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)   # repetição
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, largura, altura, GL_RGBA, GL_UNSIGNED_BYTE, dados)
    return tid


def carregar_texturas():
    _garantir_arquivos()
    # GL_MODULATE: cor final = cor da textura x cor calculada pela iluminação
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    return {os.path.splitext(n)[0]: carregar_textura(os.path.join(PASTA_TEXTURAS, n))
            for n in NOMES}


def usar(tid):
    """Ativa uma textura (ignorado enquanto as normais estão sendo exibidas)."""
    if Malha.modo_normais:
        return
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tid)


def nenhuma():
    glDisable(GL_TEXTURE_2D)
