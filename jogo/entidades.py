"""
Objetos do jogo: drone, células de energia, portal e obstáculos.

Cada objeto guarda seu estado (posição, ângulos, timers) e sabe se desenhar.
Toda animação usa dt (segundos desde o quadro anterior): velocidade_por_segundo * dt.
"""
import math

from OpenGL.GL import (
    GL_BLEND, GL_CULL_FACE, GL_LINE_LOOP, GL_LINE_STRIP, GL_LINES,
    GL_ONE, GL_SRC_ALPHA, GL_TRIANGLE_FAN, glBegin, glBlendFunc, glColor4f,
    glDepthMask, glDisable, glEnable, glEnd, glLineWidth, glPopMatrix, glPushMatrix,
    glRotatef, glScalef, glTranslatef, glVertex3f,
)

from . import config, texturas
from .iluminacao import com_iluminacao, material, sem_iluminacao
from .primitivas import cilindro, cubo, esfera, octaedro, toro


def suavizar(t):
    """smoothstep: 0..1 com início e fim suaves."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def misturar(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def iniciar_efeitos():
    """Estado para efeitos translúcidos (linhas brilhantes, disco do portal)."""
    sem_iluminacao()
    texturas.nenhuma()
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)   # mistura aditiva = brilho
    glDepthMask(False)                   # testa profundidade, mas não grava


def finalizar_efeitos():
    glDepthMask(True)
    glDisable(GL_BLEND)
    com_iluminacao()


# ===========================================================================
# DRONE — objeto composto e hierárquico
# ===========================================================================
class Drone:
    def __init__(self):
        self.m_corpo = cubo(1, 1, 1, subdiv=6, nome="drone_corpo")
        self.m_cubo = cubo(1, 1, 1, subdiv=2, nome="drone_peca")
        self.m_cupula = esfera(1.0, 24, 10, hemisferio=True, nome="drone_cupula")
        self.m_motor = cilindro(1.0, 1.0, 16, nome="drone_motor")
        self.reiniciar()

    @property
    def raio(self):
        return config.DRONE_RAIO_BASE * config.DRONE_ESCALA

    def reiniciar(self):
        self.x, self.z = config.DRONE_INICIO
        self.y = config.ALTURA_VOO
        self.yaw = math.radians(config.DRONE_YAW_INICIAL)
        self.vx = self.vz = 0.0
        self.angulo_helice = 0.0
        self.tempo = 0.0
        self.inclinacao_frente = 0.0
        self.inclinacao_lado = 0.0
        self.impacto = 0.0
        self.escala_evento = 1.0
        self.entrada = None          # animação de entrada no portal
        self.entrada_concluida = False

    def frente(self):
        """Direção para onde o nariz aponta (yaw = 0 -> -Z)."""
        return -math.sin(self.yaw), -math.cos(self.yaw)

    @property
    def velocidade(self):
        return math.hypot(self.vx, self.vz)

    # -------------------------------------------------------------- lógica
    def atualizar(self, dt, frente, giro, controlavel):
        self.tempo += dt
        esforco = abs(frente) + 0.5 * abs(giro)
        # ROTAÇÃO CONTÍNUA das hélices (graus/s * s)
        self.angulo_helice = (self.angulo_helice
                              + config.HELICE_VEL * (1 + 0.5 * esforco) * dt) % 360.0
        self.impacto = max(0.0, self.impacto - dt)

        if self.entrada is not None:
            self._atualizar_entrada(dt)
            return
        if not controlavel:
            frente = giro = 0.0

        self.yaw += math.radians(config.DRONE_VEL_GIRO) * giro * dt
        fx, fz = self.frente()
        self.vx += fx * config.DRONE_ACELERACAO * frente * dt
        self.vz += fz * config.DRONE_ACELERACAO * frente * dt
        amortecimento = math.exp(-config.DRONE_AMORTECIMENTO * dt)
        self.vx *= amortecimento
        self.vz *= amortecimento
        v = self.velocidade
        if v > config.DRONE_VEL_MAX:
            self.vx *= config.DRONE_VEL_MAX / v
            self.vz *= config.DRONE_VEL_MAX / v
        # TRANSLAÇÃO: posição += velocidade * dt
        self.x += self.vx * dt
        self.z += self.vz * dt

        # inclinação visual (nariz abaixa ao acelerar, inclina na curva)
        k = 1.0 - math.exp(-8.0 * dt)
        alvo_frente = -config.DRONE_INCLINACAO_MAX * frente
        alvo_lado = config.DRONE_INCLINACAO_MAX * 0.8 * giro
        self.inclinacao_frente += (alvo_frente - self.inclinacao_frente) * k
        self.inclinacao_lado += (alvo_lado - self.inclinacao_lado) * k

    def resolver_colisoes(self, obstaculos):
        colidiu = False
        for obst in obstaculos:
            resultado = obst.colisao_circulo(self.x, self.z, self.raio)
            if resultado is None:
                continue
            nx, nz, penetracao = resultado
            self.x += nx * penetracao          # empurra para fora
            self.z += nz * penetracao
            vn = self.vx * nx + self.vz * nz   # velocidade em direção ao obstáculo
            if vn < 0:
                self.vx -= (1 + config.DRONE_RESTITUICAO) * vn * nx
                self.vz -= (1 + config.DRONE_RESTITUICAO) * vn * nz
                if -vn > 1.2 and self.impacto <= 0:
                    self.impacto = config.IMPACTO_DURACAO   # dispara animação de evento
            colidiu = True
        return colidiu

    def limitar(self, meia):
        lim = meia - self.raio
        if abs(self.x) > lim:
            self.x = math.copysign(lim, self.x)
            self.vx *= -0.3
        if abs(self.z) > lim:
            self.z = math.copysign(lim, self.z)
            self.vz *= -0.3

    def iniciar_entrada(self, destino_x, destino_z):
        self.entrada = {"t": 0.0, "x0": self.x, "z0": self.z,
                        "x1": destino_x, "z1": destino_z - 1.0}

    def _atualizar_entrada(self, dt):
        e = self.entrada
        e["t"] += dt
        p = suavizar(e["t"] / config.ENTRADA_PORTAL_DURACAO)
        self.x = e["x0"] + (e["x1"] - e["x0"]) * p
        self.z = e["z0"] + (e["z1"] - e["z0"]) * p
        self.yaw += math.radians(540) * dt * p
        self.escala_evento = 1.0 - p
        self.inclinacao_frente *= 0.9
        self.inclinacao_lado *= 0.9
        if e["t"] >= config.ENTRADA_PORTAL_DURACAO:
            self.entrada_concluida = True

    # ------------------------------------------------------------ desenho
    def _aplicar_raiz(self):
        """Transformação do drone no MUNDO (nó raiz da hierarquia)."""
        oscilacao = config.OSCILACAO_AMPLITUDE * math.sin(
            2 * math.pi * config.OSCILACAO_FREQUENCIA * self.tempo)      # MOVIMENTO PERIÓDICO
        tremor = 0.0
        if self.impacto > 0:
            tremor = 0.08 * (self.impacto / config.IMPACTO_DURACAO) * math.sin(self.tempo * 70)
        glTranslatef(self.x + tremor, self.y + oscilacao, self.z)       # TRANSLAÇÃO
        glRotatef(math.degrees(self.yaw), 0, 1, 0)                     # ROTAÇÃO (orientação)
        glRotatef(self.inclinacao_frente, 1, 0, 0)
        glRotatef(self.inclinacao_lado, 0, 0, 1)
        s = config.DRONE_ESCALA * self.escala_evento
        glScalef(s, s, s)                                              # ESCALA geral

    def _peca(self, malha, tx, ty, tz, sx, sy, sz):
        """Desenha uma peça: cubo unitário escalado e posicionado no referencial do drone."""
        glPushMatrix()
        glTranslatef(tx, ty, tz)
        glScalef(sx, sy, sz)
        malha.desenhar()
        glPopMatrix()

    def desenhar(self):
        if self.escala_evento <= 0.01:
            return
        texturas.nenhuma()
        f = self.impacto / config.IMPACTO_DURACAO
        emissao_impacto = (0.9 * f, 0.12 * f, 0.05 * f, 1.0)

        glPushMatrix()
        self._aplicar_raiz()

        # corpo central (metal claro com forte brilho especular)
        material((0.58, 0.62, 0.7), especular=(1, 1, 1), brilho=90, emissao=emissao_impacto)
        self._peca(self.m_corpo, 0, 0, 0, 0.9, 0.32, 1.15)
        # faixa laranja (identidade visual)
        material((0.95, 0.45, 0.1), especular=(0.6, 0.6, 0.6), brilho=40, emissao=emissao_impacto)
        self._peca(self.m_cubo, 0, 0.165, 0.32, 0.92, 0.02, 0.26)
        # cúpula de vidro
        material((0.08, 0.3, 0.5), especular=(1, 1, 1), brilho=120)
        self._peca(self.m_cupula, 0, 0.16, -0.08, 0.34, 0.24, 0.42)
        # sensor frontal + lente emissiva
        material((0.16, 0.16, 0.19), especular=(0.8, 0.8, 0.8), brilho=60)
        self._peca(self.m_cubo, 0, -0.03, -0.66, 0.34, 0.16, 0.2)
        pulso = 0.6 + 0.4 * math.sin(self.tempo * 6)
        material((0.2, 0.02, 0.02), emissao=(1.0 * pulso, 0.15 * pulso, 0.1 * pulso))
        self._peca(self.m_cubo, 0, -0.03, -0.77, 0.16, 0.08, 0.03)

        # quatro braços — cada um é um "filho" do corpo
        for i in range(4):
            glPushMatrix()
            glRotatef(45 + 90 * i, 0, 1, 0)        # orienta o braço em X
            material((0.2, 0.22, 0.26), especular=(0.5, 0.5, 0.5), brilho=30)
            self._peca(self.m_cubo, 0, 0, -0.9, 0.12, 0.08, 0.9)

            glTranslatef(0, 0, -1.38)              # vai até a ponta do braço
            self._peca(self.m_motor, 0, -0.1, 0, 0.13, 0.22, 0.13)
            # LEDs: verde na frente, vermelho atrás (ajudam a ver a orientação)
            frente = i in (0, 3)
            led = (0.1, 1.0, 0.5) if frente else (1.0, 0.15, 0.1)
            material((0.05, 0.05, 0.05), emissao=led)
            self._peca(self.m_cubo, 0, -0.14, 0, 0.08, 0.06, 0.08)

            # HIERARQUIA: a hélice herda a transformação do drone e do braço
            # e ainda aplica sua própria rotação local em torno do próprio eixo.
            glTranslatef(0, 0.14, 0)
            sentido = 1 if i % 2 == 0 else -1
            glRotatef(self.angulo_helice * sentido, 0, 1, 0)
            material((0.85, 0.87, 0.9), especular=(0.7, 0.7, 0.7), brilho=50)
            self._peca(self.m_cubo, 0, 0, 0, 0.95, 0.02, 0.09)
            glRotatef(90, 0, 1, 0)
            self._peca(self.m_cubo, 0, 0, 0, 0.95, 0.02, 0.09)
            glPopMatrix()

        glPopMatrix()

    def desenhar_efeitos(self):
        """Feixe do sensor (primitiva GL_LINES)."""
        if self.escala_evento <= 0.01 or self.entrada is not None:
            return
        glPushMatrix()
        self._aplicar_raiz()
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glColor4f(1.0, 0.2, 0.15, 0.9)
        glVertex3f(0, -0.03, -0.8)
        glColor4f(1.0, 0.2, 0.15, 0.0)
        glVertex3f(0, -0.03, -5.0)
        glEnd()
        glPopMatrix()


# ===========================================================================
# CÉLULA DE ENERGIA
# ===========================================================================
class Celula:
    _cristal = None
    _anel = None

    def __init__(self, x, z, fase):
        if Celula._cristal is None:
            Celula._cristal = octaedro(0.32, 0.55, nome="celula_cristal")
            Celula._anel = toro(0.6, 0.04, 32, 8, nome="celula_anel")
        self.x, self.z = x, z
        self.fase = fase
        self.reiniciar()

    def reiniciar(self):
        self.ativa = True
        self.coletando = False
        self.t_coleta = 0.0
        self.angulo = self.fase * 57.0
        self.tempo = 0.0

    @property
    def disponivel(self):
        return self.ativa and not self.coletando

    def coletar(self):
        self.coletando = True
        self.t_coleta = 0.0

    def atualizar(self, dt):
        self.tempo += dt
        self.angulo = (self.angulo + config.CELULA_VEL_GIRO * dt) % 360.0   # ROTAÇÃO CONTÍNUA
        if self.coletando:
            self.t_coleta += dt
            self.angulo += 720.0 * dt
            if self.t_coleta >= config.CELULA_DURACAO_COLETA:
                self.ativa = False

    @property
    def progresso_coleta(self):
        return self.t_coleta / config.CELULA_DURACAO_COLETA if self.coletando else 0.0

    @property
    def y(self):
        # MOVIMENTO PERIÓDICO: flutua com uma senoide
        base = config.CELULA_ALTURA + config.CELULA_FLUTUA_AMPLITUDE * math.sin(
            2 * math.pi * config.CELULA_FLUTUA_FREQUENCIA * self.tempo + self.fase)
        return base + 1.2 * suavizar(self.progresso_coleta)   # sobe ao ser coletada

    def desenhar(self):
        if not self.ativa:
            return
        texturas.nenhuma()
        p = self.progresso_coleta
        escala = config.CELULA_ESCALA * (1.0 - suavizar(p)) * (1.0 + 0.4 * math.sin(math.pi * p))
        pulso = 0.5 + 0.5 * math.sin(self.tempo * 4 + self.fase)

        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.angulo, 0, 1, 0)
        glScalef(escala, escala, escala)
        material((0.1, 0.65, 0.85), especular=(1, 1, 1), brilho=100,
                 emissao=(0.0, 0.22 + 0.2 * pulso + p, 0.32 + 0.25 * pulso + p))
        Celula._cristal.desenhar()
        glRotatef(-2 * self.angulo, 0, 1, 0)
        glRotatef(70, 1, 0, 0)
        material((0.9, 0.75, 0.3), especular=(1, 1, 1), brilho=80, emissao=(0.15, 0.1, 0.0))
        Celula._anel.desenhar()
        glPopMatrix()

    def desenhar_efeitos(self):
        """Feixe vertical e anel no chão para localizar a célula."""
        if not self.disponivel:
            return
        pulso = 0.5 + 0.5 * math.sin(self.tempo * 3 + self.fase)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glColor4f(0.2, 0.9, 1.0, 0.5)
        glVertex3f(self.x, 0.02, self.z)
        glColor4f(0.2, 0.9, 1.0, 0.0)
        glVertex3f(self.x, 5.0, self.z)
        glEnd()
        raio = 0.6 + 0.25 * pulso
        glBegin(GL_LINE_LOOP)
        glColor4f(0.2, 0.9, 1.0, 0.35 + 0.3 * pulso)
        for k in range(24):
            a = 2 * math.pi * k / 24
            glVertex3f(self.x + raio * math.cos(a), 0.03, self.z + raio * math.sin(a))
        glEnd()


# ===========================================================================
# PORTAL DE SAÍDA
# ===========================================================================
VERMELHO = (1.0, 0.18, 0.12)
VERDE = (0.2, 1.0, 0.55)


class Portal:
    def __init__(self):
        self.x, self.z = config.PORTAL_POSICAO
        self.m_anel = toro(config.PORTAL_RAIO, 0.16, 56, 12, nome="portal_anel")
        self.m_no = esfera(0.13, 12, 8, nome="portal_no")
        self.m_base = cubo(4.6, 0.3, 1.6, subdiv=4, nome="portal_base")
        self.m_coluna = cubo(0.45, 3.9, 0.45, subdiv=3, nome="portal_coluna")
        self.reiniciar()

    def reiniciar(self):
        self.ativo = False
        self.t_ativacao = 0.0
        self.rotacao = 0.0
        self.tempo = 0.0
        self.coletadas = 0
        self.total = len(config.CELULAS)

    def ativar(self):
        self.ativo = True
        self.t_ativacao = 0.0

    @property
    def abertura(self):
        return suavizar(self.t_ativacao / config.PORTAL_DURACAO_ABERTURA) if self.ativo else 0.0

    def atualizar(self, dt, coletadas):
        self.tempo += dt
        self.coletadas = coletadas
        self.rotacao = (self.rotacao + (30.0 + 150.0 * self.abertura) * dt) % 360.0
        if self.ativo:
            self.t_ativacao += dt

    def dentro(self, x, z):
        return (self.abertura > 0.95 and abs(x - self.x) < 1.3 and abs(z - self.z) < 0.9)

    def perto(self, x, z):
        return math.hypot(x - self.x, z - self.z) < 5.0

    def desenhar(self):
        texturas.nenhuma()
        a = self.abertura
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        material((0.22, 0.24, 0.3), especular=(0.6, 0.6, 0.6), brilho=40)
        glPushMatrix()
        glTranslatef(0, 0.15, 0)
        self.m_base.desenhar()
        glPopMatrix()
        for sx in (-2.05, 2.05):
            glPushMatrix()
            glTranslatef(sx, 0.3 + 1.95, 0)
            self.m_coluna.desenhar()
            glPopMatrix()

        # ANIMAÇÃO POR EVENTO: anel muda de vermelho para verde e pulsa ao abrir
        cor = misturar(VERMELHO, VERDE, a)
        brilho = 0.25 + 0.55 * a * (0.75 + 0.25 * math.sin(self.tempo * 6))
        glPushMatrix()
        glTranslatef(0, config.PORTAL_CENTRO_Y, 0)
        s = 1.0 + 0.05 * a * math.sin(self.tempo * 5)
        glScalef(s, s, s)
        glRotatef(self.rotacao * 0.2, 0, 0, 1)
        material((cor[0] * 0.5, cor[1] * 0.5, cor[2] * 0.5), especular=(1, 1, 1), brilho=80,
                 emissao=tuple(c * brilho for c in cor))
        self.m_anel.desenhar()
        glPopMatrix()

        # indicadores de progresso: um "nó" aceso por célula coletada
        for i in range(self.total):
            ang = math.radians(90 + (i - (self.total - 1) / 2) * 26)
            aceso = i < self.coletadas
            glPushMatrix()
            glTranslatef(config.PORTAL_RAIO * math.cos(ang),
                         config.PORTAL_CENTRO_Y + config.PORTAL_RAIO * math.sin(ang), 0.2)
            if aceso:
                material((0.1, 0.6, 0.8), emissao=(0.2, 0.9, 1.0))
            else:
                material((0.15, 0.15, 0.18), especular=(0.5, 0.5, 0.5), brilho=30)
            self.m_no.desenhar()
            glPopMatrix()
        glPopMatrix()

    def desenhar_efeitos(self):
        a = self.abertura
        cy = config.PORTAL_CENTRO_Y
        r_int = config.PORTAL_RAIO - 0.16
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        glDisable(GL_CULL_FACE)
        if a < 1.0:
            # barreira: linhas horizontais vermelhas enquanto bloqueado
            glLineWidth(1.5)
            glBegin(GL_LINES)
            for k in range(-6, 7):
                yy = k * r_int / 7
                meia = math.sqrt(max(r_int ** 2 - yy ** 2, 0))
                alfa = (0.25 + 0.15 * math.sin(self.tempo * 4 + k)) * (1 - a)
                glColor4f(1.0, 0.2, 0.15, alfa)
                glVertex3f(-meia, cy + yy, 0)
                glVertex3f(meia, cy + yy, 0)
            glEnd()
        if a > 0:
            # disco do portal: leque de triângulos (GL_TRIANGLE_FAN) girando
            raio = r_int * a
            glBegin(GL_TRIANGLE_FAN)
            glColor4f(0.8, 1.0, 0.9, 0.85 * a)
            glVertex3f(0, cy, 0)
            n = 48
            for k in range(n + 1):
                ang = 2 * math.pi * k / n
                onda = 0.5 + 0.5 * math.sin(6 * ang + math.radians(self.rotacao) * 3)
                glColor4f(0.1, 0.9 * onda + 0.1, 0.6, 0.25 * a)
                glVertex3f(raio * math.cos(ang), cy + raio * math.sin(ang), 0)
            glEnd()
            # espiral
            glLineWidth(2.0)
            for braco in range(3):
                glBegin(GL_LINE_STRIP)
                for k in range(40):
                    t = k / 39
                    ang = math.radians(self.rotacao * 2) + braco * 2.094 + t * 5
                    glColor4f(0.6, 1.0, 0.8, 0.6 * a * (1 - t))
                    glVertex3f(raio * t * math.cos(ang), cy + raio * t * math.sin(ang), 0.02)
                glEnd()
        glEnable(GL_CULL_FACE)
        glPopMatrix()


# ===========================================================================
# OBSTÁCULOS
# ===========================================================================
class Caixa:
    """Caixa de manutenção texturizada. Colisão por caixa delimitadora (AABB) em XZ."""

    def __init__(self, x, z, sx, sy, sz, y_base, textura):
        self.x, self.z = x, z
        self.sx, self.sy, self.sz = sx, sy, sz
        self.y_base = y_base
        self.textura = textura
        # UV proporcional ao tamanho: a textura não estica (1 repetição a cada min(sx,sy,sz))
        self.malha = cubo(sx, sy, sz, subdiv=4, uv_por_unidade=1.0 / min(sx, sy, sz),
                          nome="caixa")

    def colisao_circulo(self, x, z, raio):
        if self.y_base > 0:          # caixa empilhada: a de baixo já colide
            return None
        minx, maxx = self.x - self.sx / 2, self.x + self.sx / 2
        minz, maxz = self.z - self.sz / 2, self.z + self.sz / 2
        px, pz = max(minx, min(x, maxx)), max(minz, min(z, maxz))   # ponto mais próximo
        dx, dz = x - px, z - pz
        d2 = dx * dx + dz * dz
        if d2 >= raio * raio:
            return None
        if d2 > 1e-9:
            d = math.sqrt(d2)
            return dx / d, dz / d, raio - d
        opcoes = [(x - minx, -1, 0), (maxx - x, 1, 0), (z - minz, 0, -1), (maxz - z, 0, 1)]
        pen, nx, nz = min(opcoes)
        return nx, nz, pen + raio

    def desenhar(self):
        texturas.usar(self.textura)
        material((1.0, 1.0, 1.0), especular=(0.25, 0.25, 0.25), brilho=20)
        glPushMatrix()
        glTranslatef(self.x, self.y_base + self.sy / 2, self.z)
        self.malha.desenhar()
        glPopMatrix()
        texturas.nenhuma()


class Pilar:
    """Pilar cilíndrico. Colisão por distância entre centros."""

    def __init__(self, x, z, raio, altura):
        self.x, self.z, self.raio, self.altura = x, z, raio, altura
        # malhas já no tamanho real (sem escala não uniforme -> normais exibidas corretas)
        self.malha = cilindro(raio, altura, 28, nome="pilar")
        self.faixa = toro(raio + 0.02, 0.08, 32, 8, nome="pilar_faixa")

    def colisao_circulo(self, x, z, raio):
        dx, dz = x - self.x, z - self.z
        d = math.hypot(dx, dz)
        minimo = raio + self.raio
        if d >= minimo:
            return None
        if d < 1e-9:
            return 1.0, 0.0, minimo
        return dx / d, dz / d, minimo - d

    def desenhar(self):
        texturas.nenhuma()
        glPushMatrix()
        glTranslatef(self.x, 0, self.z)
        material((0.35, 0.37, 0.42), especular=(0.9, 0.9, 0.9), brilho=60)
        self.malha.desenhar()
        # faixas de alerta laranja (identidade: obstáculo)
        for h in (1.0, self.altura - 0.6):
            glPushMatrix()
            glTranslatef(0, h, 0)
            glRotatef(90, 1, 0, 0)
            material((0.9, 0.42, 0.08), especular=(0.6, 0.6, 0.6), brilho=40,
                     emissao=(0.35, 0.12, 0.0))
            self.faixa.desenhar()
            glPopMatrix()
        glPopMatrix()
