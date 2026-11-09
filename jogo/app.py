"""
Laço principal: janela, entrada, regras do jogo e ordem de desenho.
"""
import math
import os
import time

import pygame
from OpenGL.GL import (
    GL_BACK, GL_CCW, GL_COLOR_BUFFER_BIT, GL_CULL_FACE, GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST, GL_EXP2, GL_FOG, GL_FOG_COLOR, GL_FOG_DENSITY, GL_FOG_MODE,
    GL_LEQUAL, GL_LIGHTING, GL_LINE_SMOOTH, GL_MULTISAMPLE, GL_NORMALIZE, GL_RGB,
    GL_SMOOTH, GL_UNSIGNED_BYTE, glClear, glClearColor, glColor4f,
    glCullFace, glDepthFunc, glDisable, glEnable, glFogf, glFogfv, glFogi,
    glFrontFace, glLineWidth, glReadPixels, glShadeModel, glViewport,
)

from . import config, iluminacao, texturas
from .camera import Camera
from .cenario import Cenario
from .entidades import (Caixa, Celula, Drone, Pilar, Portal, finalizar_efeitos,
                        iniciar_efeitos)
from .hud import Hud
from .primitivas import Malha

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AJUDA = [
    "W/S  acelerar / ré     A/D  girar",
    "Setas ou mouse (arrastar)  orbitar câmera   Roda  zoom",
    "C  câmera   L  luz   N  normais   F  limite de FPS",
    "P  captura de tela   H  ocultar ajuda   R  reiniciar   Esc  sair",
]


class Entrada:
    def __init__(self, frente=0.0, giro=0.0, cam_yaw=0.0, cam_pitch=0.0):
        self.frente, self.giro = frente, giro
        self.cam_yaw, self.cam_pitch = cam_yaw, cam_pitch


def ler_teclado():
    t = pygame.key.get_pressed()
    return Entrada(
        frente=float(t[pygame.K_w]) - float(t[pygame.K_s]),
        giro=float(t[pygame.K_a]) - float(t[pygame.K_d]),
        cam_yaw=float(t[pygame.K_LEFT]) - float(t[pygame.K_RIGHT]),
        cam_pitch=float(t[pygame.K_UP]) - float(t[pygame.K_DOWN]),
    )


class App:
    def __init__(self, largura=config.LARGURA, altura=config.ALTURA):
        pygame.init()
        self.largura, self.altura = largura, altura
        flags = pygame.DOUBLEBUF | pygame.OPENGL
        try:   # antisserrilhado, se a placa de vídeo suportar
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
            pygame.display.set_mode((largura, altura), flags)
        except pygame.error:
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 0)
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 0)
            pygame.display.set_mode((largura, altura), flags)
        pygame.display.set_caption(config.NOME_MISSAO)

        self._iniciar_opengl()
        self.tex = texturas.carregar_texturas()
        self.cenario = Cenario(self.tex)
        self.drone = Drone()
        self.portal = Portal()
        self.celulas = [Celula(x, z, fase=i * 1.3) for i, (x, z) in enumerate(config.CELULAS)]
        self.obstaculos = ([Caixa(*c, textura=self.tex["caixa"]) for c in config.CAIXAS]
                           + [Pilar(*p) for p in config.PILARES])
        self.camera = Camera()
        self.hud = Hud(largura, altura)
        self.relogio = pygame.time.Clock()

        self.luz_ligada = True
        self.mostrar_normais = False
        self.mostrar_ajuda = True
        self.fps_baixo = False
        self.rodando = True
        self._t_titulo = 0.0
        self.reiniciar()

    # ------------------------------------------------------------ setup
    def _iniciar_opengl(self):
        glViewport(0, 0, self.largura, self.altura)
        glClearColor(*config.COR_FUNDO)
        glEnable(GL_DEPTH_TEST)          # teste de profundidade (oclusão correta)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)           # descarta faces de costas para a câmera
        glCullFace(GL_BACK)
        glFrontFace(GL_CCW)
        glEnable(GL_NORMALIZE)           # renormaliza normais após glScale
        glShadeModel(GL_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        try:
            glEnable(GL_MULTISAMPLE)
        except Exception:
            pass
        glEnable(GL_FOG)                 # neblina leve reforça a profundidade
        glFogi(GL_FOG_MODE, GL_EXP2)
        glFogfv(GL_FOG_COLOR, config.COR_FUNDO)
        glFogf(GL_FOG_DENSITY, config.NEBLINA_DENSIDADE)
        iluminacao.configurar()

    def reiniciar(self):
        self.drone.reiniciar()
        self.portal.reiniciar()
        for c in self.celulas:
            c.reiniciar()
        self.camera.reiniciar(self.drone)
        self.estado = "jogando"          # jogando -> entrando -> concluida
        self.tempo_missao = 0.0
        self.tempo_estado = 0.0
        self.mensagem = None
        self.avisar("Recupere as 5 células de energia e alcance o portal", 4.0, (0.6, 0.9, 1.0))

    def avisar(self, texto, duracao=2.5, cor=(1, 1, 1)):
        if self.mensagem and self.mensagem[0] == texto:   # mesma mensagem: só prolonga
            self.mensagem[1] = max(self.mensagem[1], duracao)
            return
        self.mensagem = [texto, duracao, duracao, cor]

    @property
    def coletadas(self):
        return sum(1 for c in self.celulas if not c.disponivel)

    # ------------------------------------------------------------ eventos
    def processar_eventos(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.rodando = False
            elif ev.type == pygame.KEYDOWN:
                self.tecla(ev.key)
            elif ev.type == pygame.MOUSEMOTION and (ev.buttons[0] or ev.buttons[2]):
                self.camera.orbitar(-ev.rel[0] * 0.3, ev.rel[1] * 0.3)
            elif ev.type == pygame.MOUSEWHEEL:
                self.camera.zoom(-ev.y * 0.8)

    def tecla(self, k):
        if k == pygame.K_ESCAPE:
            self.rodando = False
        elif k == pygame.K_r:
            self.reiniciar()
        elif k == pygame.K_l:
            self.luz_ligada = not self.luz_ligada
            self.avisar("Luz " + ("ligada" if self.luz_ligada else "desligada"), 1.5)
        elif k == pygame.K_c:
            self.camera.alternar_modo()
            self.avisar("Câmera: " + self.camera.nome_modo, 1.5)
        elif k == pygame.K_n:
            self.mostrar_normais = not self.mostrar_normais
        elif k == pygame.K_f:
            self.fps_baixo = not self.fps_baixo
            lim = config.FPS_LIMITE_BAIXO if self.fps_baixo else config.FPS_LIMITE_NORMAL
            self.avisar(f"Limite de FPS: {lim} (a velocidade não muda: dt)", 2.0)
        elif k == pygame.K_h:
            self.mostrar_ajuda = not self.mostrar_ajuda
        elif k == pygame.K_p:
            self.salvar_captura()

    # ------------------------------------------------------------ lógica
    def atualizar(self, dt, entrada):
        self.tempo_estado += dt
        if self.estado == "jogando":
            self.tempo_missao += dt
        controlavel = self.estado == "jogando"

        self.drone.atualizar(dt, entrada.frente, entrada.giro, controlavel)
        if controlavel:
            self.drone.resolver_colisoes(self.obstaculos)
            self.drone.limitar(config.ARENA_MEIA)

        # coleta: distância entre centros (no plano XZ)
        for c in self.celulas:
            c.atualizar(dt)
            if controlavel and c.disponivel:
                d = math.hypot(c.x - self.drone.x, c.z - self.drone.z)
                if d < self.drone.raio + config.CELULA_RAIO_COLETA:
                    c.coletar()
                    n = self.coletadas
                    if n < len(self.celulas):
                        self.avisar(f"Célula coletada: {n}/{len(self.celulas)}", 1.8,
                                    (0.4, 0.95, 1.0))

        self.portal.atualizar(dt, self.coletadas)
        if self.coletadas == len(self.celulas) and not self.portal.ativo:
            self.portal.ativar()
            self.avisar("Portal de saída ativado! Siga até ele", 3.0, (0.4, 1.0, 0.6))

        if controlavel and self.portal.dentro(self.drone.x, self.drone.z):
            self.estado = "entrando"
            self.tempo_estado = 0.0
            self.drone.iniciar_entrada(self.portal.x, self.portal.z)
        elif (controlavel and not self.portal.ativo
              and self.portal.perto(self.drone.x, self.drone.z)):
            faltam = len(self.celulas) - self.coletadas
            self.avisar(f"Portal bloqueado: faltam {faltam} célula(s)", 0.3, (1.0, 0.45, 0.35))

        if self.estado == "entrando" and self.drone.entrada_concluida:
            self.estado = "concluida"
            self.tempo_estado = 0.0

        foco = None
        if self.estado != "jogando":      # final: câmera recua e enquadra o portal
            foco = ((self.portal.x, 3.2, self.portal.z + 9.0),
                    (self.portal.x, config.PORTAL_CENTRO_Y, self.portal.z))
        self.camera.atualizar(dt, self.drone, entrada.cam_yaw, entrada.cam_pitch, foco)

        if self.mensagem:
            self.mensagem[1] -= dt
            if self.mensagem[1] <= 0:
                self.mensagem = None

    # ------------------------------------------------------------ desenho
    def desenhar(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.camera.aplicar_projecao(self.largura / self.altura)
        self.camera.aplicar_visao()
        iluminacao.posicionar()           # depois da câmera -> luz fixa no mundo
        iluminacao.definir(self.luz_ligada)

        # 1) objetos opacos (gravam profundidade)
        self.cenario.desenhar_ceu()
        self.cenario.desenhar(self.luz_ligada)
        for o in self.obstaculos:
            o.desenhar()
        self.portal.desenhar()
        for c in self.celulas:
            c.desenhar()
        self.drone.desenhar()

        # 2) efeitos translúcidos (por último, sem gravar profundidade)
        iniciar_efeitos()
        self.cenario.desenhar_efeitos(self.luz_ligada)
        for c in self.celulas:
            c.desenhar_efeitos()
        self.portal.desenhar_efeitos()
        self.drone.desenhar_efeitos()
        finalizar_efeitos()

        # 3) normais (tecla N)
        if self.mostrar_normais:
            self._desenhar_normais()

        self._desenhar_hud()

    def _desenhar_normais(self):
        glDisable(GL_LIGHTING)
        texturas.nenhuma()
        glLineWidth(1.0)
        glColor4f(1.0, 1.0, 0.2, 1.0)
        Malha.modo_normais = True
        try:
            for o in self.obstaculos:
                o.desenhar()
            self.portal.desenhar()
            for c in self.celulas:
                c.desenhar()
            self.drone.desenhar()
        finally:
            Malha.modo_normais = False
        glEnable(GL_LIGHTING)

    def _desenhar_hud(self):
        h = self.hud
        h.iniciar()
        total = len(self.celulas)
        n = self.coletadas

        h.retangulo(16, 16, 300, 112, (0.02, 0.04, 0.08, 0.55))
        h.texto(config.NOME_MISSAO.upper(), 30, 26, 30, (1.0, 0.65, 0.2))
        h.texto(f"Células: {n}/{total}", 30, 58, 28, (0.5, 0.95, 1.0))
        for i in range(total):   # barra de progresso
            cor = (0.3, 0.9, 1.0, 0.95) if i < n else (0.3, 0.35, 0.45, 0.6)
            h.retangulo(170 + i * 26, 60, 20, 16, cor)
        h.texto(f"Tempo: {self.tempo_missao:5.1f} s", 30, 88, 24, (0.85, 0.88, 0.95))
        luz = "LIGADA" if self.luz_ligada else "DESLIGADA"
        h.texto(f"Luz: {luz}", 300, 88, 24,
                (1.0, 0.9, 0.5) if self.luz_ligada else (0.6, 0.6, 0.65), ancora="dir")

        fps = self.relogio.get_fps()
        h.texto(f"{fps:4.0f} FPS   câmera: {self.camera.nome_modo}", self.largura - 20, 20,
                22, (0.7, 0.75, 0.8), ancora="dir")

        if self.mostrar_ajuda:
            y0 = self.altura - 20 - 22 * len(AJUDA)
            h.retangulo(16, y0 - 10, 520, 22 * len(AJUDA) + 16, (0.02, 0.04, 0.08, 0.5))
            for i, linha in enumerate(AJUDA):
                h.texto(linha, 28, y0 + i * 22, 22, (0.8, 0.85, 0.9))

        if self.mensagem and self.estado == "jogando":
            texto, resto, dur, cor = self.mensagem
            alfa = min(1.0, resto / 0.3)          # some suavemente no final
            h.texto(texto, self.largura / 2, 150, 36, cor, alfa, ancora="centro")

        if self.estado == "jogando" and self.tempo_estado < 3.5:
            alfa = min(1.0, (3.5 - self.tempo_estado) / 0.8)
            h.texto(config.NOME_MISSAO.upper(), self.largura / 2, self.altura / 2 - 80, 72,
                    (1.0, 0.65, 0.2), alfa, ancora="centro")

        if self.estado == "concluida":
            alfa = min(1.0, self.tempo_estado / 0.6)
            h.retangulo(0, self.altura / 2 - 110, self.largura, 220, (0.0, 0.05, 0.04, 0.65 * alfa))
            h.texto("MISSÃO CONCLUÍDA", self.largura / 2, self.altura / 2 - 80, 80,
                    (0.4, 1.0, 0.6), alfa, ancora="centro")
            h.texto(f"Células recuperadas: {total}/{total}   Tempo: {self.tempo_missao:.1f} s",
                    self.largura / 2, self.altura / 2 + 5, 34, (0.9, 0.95, 1.0), alfa,
                    ancora="centro")
            h.texto("Pressione R para jogar de novo ou Esc para sair", self.largura / 2,
                    self.altura / 2 + 50, 28, (0.7, 0.8, 0.85), alfa, ancora="centro")
        h.finalizar()

    def _atualizar_titulo(self, dt):
        self._t_titulo -= dt
        if self._t_titulo > 0:
            return
        self._t_titulo = 0.25
        status = {"jogando": "em andamento", "entrando": "entrando no portal",
                  "concluida": "CONCLUÍDA"}[self.estado]
        pygame.display.set_caption(
            f"{config.NOME_MISSAO} | Células {self.coletadas}/{len(self.celulas)} | "
            f"Missão {status} | Luz {'on' if self.luz_ligada else 'off'}")

    def salvar_captura(self, caminho=None):
        if caminho is None:
            pasta = os.path.join(RAIZ, "capturas")
            os.makedirs(pasta, exist_ok=True)
            caminho = os.path.join(pasta, time.strftime("captura_%Y%m%d_%H%M%S.png"))
        dados = glReadPixels(0, 0, self.largura, self.altura, GL_RGB, GL_UNSIGNED_BYTE)
        imagem = pygame.image.fromstring(bytes(dados), (self.largura, self.altura), "RGB", True)
        pygame.image.save(imagem, caminho)
        self.avisar("Captura salva em capturas/", 1.5)
        return caminho

    # ------------------------------------------------------------ laço
    def executar(self):
        while self.rodando:
            limite = config.FPS_LIMITE_BAIXO if self.fps_baixo else config.FPS_LIMITE_NORMAL
            # dt = tempo real desde o quadro anterior, em segundos
            dt = min(self.relogio.tick(limite) / 1000.0, config.DT_MAXIMO)
            self.processar_eventos()
            self.atualizar(dt, ler_teclado())
            self.desenhar()
            self._atualizar_titulo(dt)
            pygame.display.flip()
        pygame.quit()
