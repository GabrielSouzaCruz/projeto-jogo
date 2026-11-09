# Operação Centelha

Minijogo 3D do **Trabalho Prático 1 de Computação Gráfica** (IFSULDEMINAS, Campus Machado, Prof. Renan).

Uma estação espacial perdeu sua fonte de energia. Pilote o drone de manutenção, recupere as
**5 células de energia** espalhadas pela plataforma, desvie das caixas e pilares e alcance o
**portal de saída**, que só se abre (vermelho → verde) quando todas as células forem coletadas.

**Integrantes:** Gabriel Cruz · Yasmin Dias · Alisson Henrique

---

## Instalação

Requisitos: Python 3.10 ou superior.

Recomendado: criar um ambiente virtual na pasta do projeto e instalar as dependências nele.

```bash
python -m venv .venv
```

Ative o ambiente conforme o terminal:

| Terminal | Comando |
|---|---|
| Windows (PowerShell) | `.\.venv\Scripts\Activate.ps1` |
| Windows (CMD) | `.venv\Scripts\activate.bat` |
| Linux / macOS | `source .venv/bin/activate` |

Se o PowerShell bloquear a execução de scripts, rode antes
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

Depois instale as dependências:

```bash
pip install -r requirements.txt
```

No Linux, se aparecer erro sobre `gluPerspective` ou `gluBuild2DMipmaps`, instale a biblioteca GLU:
`sudo apt install libglu1-mesa` (Windows e macOS já trazem).

## Execução

```bash
python main.py
```

Todos os caminhos são relativos à pasta do projeto, então o jogo pode ser executado a partir de
qualquer diretório. Se alguma textura de `assets/texturas/` for apagada, ela é recriada
automaticamente.

## Controles

| Tecla | Ação |
|---|---|
| W / S | Acelerar / ré |
| A / D | Girar o drone |
| Setas, ou arrastar com o mouse | Orbitar a câmera |
| Roda do mouse | Aproximar / afastar a câmera |
| C | Alternar câmera (seguir drone / aérea) |
| L | Ligar / desligar a fonte de luz |
| N | Mostrar as normais das superfícies |
| F | Alternar limite de FPS (144 / 30) — a velocidade não muda, pois tudo usa `dt` |
| P | Salvar captura de tela em `capturas/` |
| H | Mostrar / ocultar a ajuda |
| R | Reiniciar a missão |
| Esc | Encerrar |

## Estrutura

```
main.py                    ponto de entrada
jogo/config.py             TODOS os valores ajustáveis (velocidades, luz, escalas, posições)
jogo/primitivas.py         malhas construídas por código (cubo, grade, octaedro, esfera, toro, cilindro)
jogo/texturas.py           carregamento de texturas, GL_REPEAT, mipmaps
jogo/iluminacao.py         luz, contribuição ambiente e materiais
jogo/camera.py             gluPerspective + gluLookAt, modos de câmera
jogo/entidades.py          drone, células, portal, caixas e pilares
jogo/cenario.py            piso, paredes, céu, marcador da luz
jogo/hud.py                textos na tela
jogo/app.py                laço principal, regras e ordem de desenho
ferramentas/gerar_texturas.py  gera as texturas por código
assets/texturas/           piso_metal.png, caixa.png, parede_painel.png
```

## Onde está cada técnica

| Requisito | Onde | Como aparece no jogo |
|---|---|---|
| Primitivas (≥ 3 tipos) | `primitivas.py`, `entidades.py`, `cenario.py` | `GL_TRIANGLES` (cristal das células, tampas dos cilindros), `GL_QUADS` (caixas, piso, paredes, anéis), `GL_LINES` / `GL_LINE_LOOP` / `GL_LINE_STRIP` (feixe do sensor, limites, normais), `GL_TRIANGLE_FAN` (disco do portal), `GL_POINTS` (estrelas) |
| Objeto composto | `Drone.desenhar()` | corpo, faixa, cúpula, sensor, 4 braços, motores, LEDs e hélices, cada peça com sua transformação |
| Coordenadas locais → mundo | `primitivas.py` → `glTranslate/glRotate/glScale` | malhas centradas na origem e posicionadas na cena |
| Câmera e projeção | `camera.py` | `gluLookAt` (modelview) e `gluPerspective` (projeção) |
| Teste de profundidade | `App._iniciar_opengl()` | `GL_DEPTH_TEST`: caixas ocultam o drone quando ele passa atrás |
| Translação | `Drone.atualizar()`, `_aplicar_raiz()` | deslocamento do drone, posicionamento de todos os objetos |
| Rotação | idem + células e portal | orientação (yaw) e inclinação do drone, hélices, células, anel |
| Escala | `Drone._peca()`, `Celula.desenhar()` | peças do drone a partir de um cubo unitário, célula encolhendo ao ser coletada, `DRONE_ESCALA` |
| Transformação hierárquica | `Drone.desenhar()` | hélice gira no próprio eixo e acompanha braço → corpo → mundo |
| Rotação contínua | hélices, células | `angulo += velocidade * dt` |
| Movimento periódico | células flutuando, drone oscilando | `sin(2π · f · t)` |
| Animação por evento | coleta, abertura do portal, colisão, entrada no portal | célula encolhe e sobe; anel muda de cor e o disco abre; drone pisca e treme; drone é sugado |
| `dt` | `App.executar()` | `dt = clock.tick() / 1000`; tecla F comprova |
| Texturas (≥ 2) | `texturas.py`, `cenario.py`, `Caixa` | piso metálico, caixas, painéis de parede |
| Repetição de textura | piso (14×14), paredes, contêiner comprido | UV > 1 com `GL_REPEAT` |
| Sem deformação | `cubo(uv_por_unidade=...)` | UV proporcional ao tamanho real da face |
| Normais | `primitivas.py` | planas (caixas, cristal) e suaves (esfera, toro, cilindro); tecla N |
| Difusa / especular / ambiente | `iluminacao.py` | luz pontual lateral, brilho especular no drone, pilares e células; ambiente global |
| Liga/desliga luz | tecla L | só ambiente + emissão permanecem |
| Colisões | `Caixa.colisao_circulo` (AABB), `Pilar.colisao_circulo` (distância entre centros) | drone é empurrado para fora e quica |

## Origem das texturas

As três texturas foram **geradas por código** pelo script `ferramentas/gerar_texturas.py`
(desenho procedural com pygame). Não há imagens de terceiros no projeto.

## Limitações

- Iluminação calculada por vértice (Gouraud, pipeline fixo); por isso o piso é subdividido em
  48×48 para a luz pontual variar suavemente.
- Colisões apenas no plano XZ (o drone voa a altura constante).
- Sem sombras projetadas.
