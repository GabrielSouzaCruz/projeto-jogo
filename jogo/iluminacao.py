"""
Iluminação com o pipeline fixo do OpenGL (modelo de Phong por vértice / Gouraud).

Cor de um vértice = emissão
                  + ambiente_global * material_ambiente
                  + [luz ligada] atenuação * (difusa * max(N·L, 0)
                                              + especular * max(N·H, 0)^brilho)
"""
from OpenGL.GL import (
    GL_AMBIENT, GL_DIFFUSE, GL_EMISSION, GL_FRONT_AND_BACK, GL_LIGHT0,
    GL_LIGHT_MODEL_AMBIENT, GL_LIGHT_MODEL_COLOR_CONTROL, GL_LIGHT_MODEL_LOCAL_VIEWER,
    GL_LIGHTING, GL_LINEAR_ATTENUATION, GL_POSITION, GL_QUADRATIC_ATTENUATION,
    GL_SEPARATE_SPECULAR_COLOR, GL_SHININESS, GL_SPECULAR, GL_TRUE, glDisable,
    glEnable, glLightf, glLightfv, glLightModelfv, glLightModeli, glMaterialf,
    glMaterialfv,
)

from . import config

PRETO = (0.0, 0.0, 0.0, 1.0)


def configurar():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    # Contribuição ambiente: permite enxergar regiões não iluminadas (e a cena com a luz desligada)
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, config.AMBIENTE_GLOBAL)
    # Especular calculado com a posição real do observador (brilho muda com a câmera)
    glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, GL_TRUE)
    # Especular somado DEPOIS da textura: o brilho não fica "tingido" pela textura
    glLightModeli(GL_LIGHT_MODEL_COLOR_CONTROL, GL_SEPARATE_SPECULAR_COLOR)

    glLightfv(GL_LIGHT0, GL_AMBIENT, PRETO)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, config.LUZ_DIFUSA)
    glLightfv(GL_LIGHT0, GL_SPECULAR, config.LUZ_ESPECULAR)
    glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, config.LUZ_ATENUACAO_LINEAR)
    glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, config.LUZ_ATENUACAO_QUADRATICA)


def posicionar():
    """Deve ser chamada DEPOIS de configurar a câmera (gluLookAt): o OpenGL
    multiplica a posição pela matriz modelview atual, então a luz fica fixa no mundo."""
    glLightfv(GL_LIGHT0, GL_POSITION, config.LUZ_POSICAO)


def definir(ligada):
    if ligada:
        glEnable(GL_LIGHT0)
    else:
        glDisable(GL_LIGHT0)


def material(difusa, especular=PRETO, brilho=0.0, emissao=PRETO, ambiente=None):
    """Define como a superfície responde à luz."""
    def rgba(c):
        return tuple(c) if len(c) == 4 else (c[0], c[1], c[2], 1.0)

    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, rgba(ambiente or difusa))
    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, rgba(difusa))
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, rgba(especular))
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, float(brilho))
    glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, rgba(emissao))


def sem_iluminacao():
    glDisable(GL_LIGHTING)


def com_iluminacao():
    glEnable(GL_LIGHTING)
