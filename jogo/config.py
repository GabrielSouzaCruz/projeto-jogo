"""
Configurações do jogo.

Todos os valores "ajustáveis" ficam aqui, com nomes claros, para facilitar
alterações rápidas durante a apresentação (velocidade de animação, posição da
luz, escala de objetos etc.).
"""

# ---------------------------------------------------------------------------
# Janela
# ---------------------------------------------------------------------------
LARGURA = 1280
ALTURA = 720
NOME_MISSAO = "Operação Centelha"
FPS_LIMITE_NORMAL = 144
FPS_LIMITE_BAIXO = 30          # tecla F alterna (demonstra que dt funciona)
DT_MAXIMO = 0.05               # evita "saltos" se a janela travar

COR_FUNDO = (0.02, 0.03, 0.06, 1.0)

# ---------------------------------------------------------------------------
# Arena (mundo). Eixo Y para cima, piso em y = 0.
# ---------------------------------------------------------------------------
ARENA_MEIA = 14.0              # a arena vai de -14 a +14 em X e em Z
ALTURA_PAREDE = 3.0
TAMANHO_PAINEL_PAREDE = 3.0    # 1 repetição da textura a cada 3 unidades
REPETICOES_PISO = 14           # textura do piso se repete 14x em cada eixo
SUBDIVISOES_PISO = 48          # piso subdividido -> luz pontual mais suave

# ---------------------------------------------------------------------------
# Drone
# ---------------------------------------------------------------------------
DRONE_INICIO = (0.0, 11.5)     # (x, z)
DRONE_YAW_INICIAL = 0.0        # graus; 0 = olhando para -Z (em direção ao portal)
ALTURA_VOO = 1.3               # altura aproximadamente constante
DRONE_ESCALA = 0.7             # escala geral do drone
DRONE_RAIO_BASE = 1.6          # raio de colisão antes da escala

DRONE_ACELERACAO = 20.0        # unidades/s²
DRONE_VEL_MAX = 7.0            # unidades/s
DRONE_AMORTECIMENTO = 3.0      # quanto maior, mais rápido o drone para
DRONE_VEL_GIRO = 140.0         # graus/s (teclas A/D)
DRONE_INCLINACAO_MAX = 14.0    # graus de inclinação visual ao acelerar/girar
DRONE_RESTITUICAO = 0.35       # "quique" ao bater em obstáculos

HELICE_VEL = 900.0             # graus/s (rotação contínua)
OSCILACAO_AMPLITUDE = 0.07     # movimento periódico do drone
OSCILACAO_FREQUENCIA = 1.4     # Hz

IMPACTO_DURACAO = 0.35         # s de animação ao colidir

# ---------------------------------------------------------------------------
# Células de energia
# ---------------------------------------------------------------------------
CELULAS = [                    # (x, z)
    (-9.5, 8.0),
    (9.5, 6.5),
    (-1.0, -0.5),
    (-10.0, -4.0),
    (8.5, -8.0),
]
CELULA_ALTURA = 1.4
CELULA_VEL_GIRO = 90.0         # graus/s
CELULA_FLUTUA_AMPLITUDE = 0.25
CELULA_FLUTUA_FREQUENCIA = 0.6 # Hz
CELULA_ESCALA = 1.0
CELULA_RAIO_COLETA = 0.6       # somado ao raio do drone
CELULA_DURACAO_COLETA = 0.5    # s encolhendo antes de sumir

# ---------------------------------------------------------------------------
# Obstáculos
# ---------------------------------------------------------------------------
# Caixas: (x, z, largura_x, altura, profundidade_z, y_base)
CAIXAS = [
    (-4.5, 6.0, 2.0, 2.0, 2.0, 0.0),
    (4.5, 2.0, 2.4, 2.4, 2.4, 0.0),
    (-6.0, -7.0, 4.0, 2.0, 2.0, 0.0),   # contêiner comprido (textura repete 2x)
    (3.5, -5.5, 1.6, 1.6, 1.6, 0.0),
    (3.5, -5.5, 1.1, 1.1, 1.1, 1.6),    # caixa empilhada (só visual)
]
# Pilares: (x, z, raio, altura)
PILARES = [
    (-2.5, 3.0, 0.65, 4.0),
    (9.0, -1.0, 0.65, 4.0),
]

# ---------------------------------------------------------------------------
# Portal de saída
# ---------------------------------------------------------------------------
PORTAL_POSICAO = (0.0, -12.0)  # (x, z)
PORTAL_RAIO = 1.7
PORTAL_CENTRO_Y = 2.0
PORTAL_DURACAO_ABERTURA = 1.2  # s
ENTRADA_PORTAL_DURACAO = 1.2   # s do drone "sugado" pelo portal

# ---------------------------------------------------------------------------
# Iluminação (pipeline fixo do OpenGL)
# ---------------------------------------------------------------------------
LUZ_POSICAO = (-9.0, 7.0, 3.0, 1.0)   # w = 1 -> luz pontual (posição no mundo)
LUZ_DIFUSA = (1.0, 0.94, 0.82, 1.0)
LUZ_ESPECULAR = (1.0, 1.0, 1.0, 1.0)
LUZ_ATENUACAO_LINEAR = 0.02
LUZ_ATENUACAO_QUADRATICA = 0.001
AMBIENTE_GLOBAL = (0.2, 0.21, 0.27, 1.0)  # contribuição ambiente (sempre ativa)

NEBLINA_DENSIDADE = 0.016

# ---------------------------------------------------------------------------
# Câmera
# ---------------------------------------------------------------------------
CAM_FOV = 60.0
CAM_PERTO = 0.1
CAM_LONGE = 250.0
CAM_DISTANCIA = 7.0
CAM_PITCH = 24.0               # graus acima do drone
CAM_VEL_ORBITA = 90.0          # graus/s com as setas
CAM_SUAVIDADE = 6.0            # quanto maior, mais "colada" no drone
CAM_AEREA_ALTURA = 22.0
CAM_AEREA_RAIO = 18.0
