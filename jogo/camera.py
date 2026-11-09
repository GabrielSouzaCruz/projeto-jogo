"""
Câmera e projeção.

  Projeção: gluPerspective  -> matriz de PROJEÇÃO (perspectiva: longe = menor)
  Visão:    gluLookAt       -> matriz MODELVIEW (leva o mundo para o referencial da câmera)

Dois modos (tecla C): seguir o drone em terceira pessoa ou vista aérea.
Setas / arrastar com o mouse orbitam; roda do mouse aproxima/afasta.
"""
import math

from OpenGL.GL import GL_MODELVIEW, GL_PROJECTION, glLoadIdentity, glMatrixMode
from OpenGL.GLU import gluLookAt, gluPerspective

from . import config

MODOS = ("seguir", "aerea")


def _limitar(v, a, b):
    return max(a, min(b, v))


class Camera:
    def __init__(self):
        self.modo = 0
        self.pos = [0.0, 5.0, 20.0]
        self.alvo = [0.0, 1.0, 0.0]
        self.reiniciar_parametros()

    def reiniciar_parametros(self):
        self.yaw_extra = 0.0
        self.pitch = config.CAM_PITCH
        self.distancia = config.CAM_DISTANCIA

    def reiniciar(self, drone):
        self.reiniciar_parametros()
        self.pos, self.alvo = map(list, self._desejado(drone))

    @property
    def nome_modo(self):
        return "seguir drone" if MODOS[self.modo] == "seguir" else "aérea"

    def alternar_modo(self):
        self.modo = (self.modo + 1) % len(MODOS)
        self.yaw_extra = 0.0

    def orbitar(self, d_yaw, d_pitch):
        self.yaw_extra += d_yaw
        self.pitch = _limitar(self.pitch + d_pitch, 5.0, 80.0)

    def zoom(self, delta):
        self.distancia = _limitar(self.distancia + delta, 3.5, 16.0)

    def _desejado(self, drone):
        if MODOS[self.modo] == "seguir":
            yaw = drone.yaw + math.radians(self.yaw_extra)
            p = math.radians(self.pitch)
            alvo = (drone.x, drone.y + 0.3, drone.z)
            # posição atrás do drone, em coordenadas esféricas ao redor do alvo
            pos = (alvo[0] + self.distancia * math.cos(p) * math.sin(yaw),
                   alvo[1] + self.distancia * math.sin(p),
                   alvo[2] + self.distancia * math.cos(p) * math.cos(yaw))
            lim = config.ARENA_MEIA - 0.3
            pos = (_limitar(pos[0], -lim, lim), pos[1], _limitar(pos[2], -lim, lim))
        else:
            ye = math.radians(self.yaw_extra)
            alvo = (0.0, 0.0, -1.0)
            pos = (config.CAM_AEREA_RAIO * math.sin(ye), config.CAM_AEREA_ALTURA,
                   config.CAM_AEREA_RAIO * math.cos(ye))
        return pos, alvo

    def atualizar(self, dt, drone, entrada_yaw, entrada_pitch, foco=None):
        self.orbitar(entrada_yaw * config.CAM_VEL_ORBITA * dt,
                     entrada_pitch * config.CAM_VEL_ORBITA * dt)
        pos_d, alvo_d = foco if foco else self._desejado(drone)
        # suavização exponencial dependente de dt (mesmo efeito a 30 ou 144 FPS)
        k = 1.0 - math.exp(-config.CAM_SUAVIDADE * dt)
        k_alvo = 1.0 - math.exp(-config.CAM_SUAVIDADE * 2.0 * dt)
        for i in range(3):
            self.pos[i] += (pos_d[i] - self.pos[i]) * k
            self.alvo[i] += (alvo_d[i] - self.alvo[i]) * k_alvo

    def aplicar_projecao(self, aspecto):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(config.CAM_FOV, aspecto, config.CAM_PERTO, config.CAM_LONGE)
        glMatrixMode(GL_MODELVIEW)

    def aplicar_visao(self):
        glLoadIdentity()
        gluLookAt(*self.pos, *self.alvo, 0.0, 1.0, 0.0)
