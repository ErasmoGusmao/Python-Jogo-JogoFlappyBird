# Jogo Flappy Brid conectada a IA
# Aula: https://www.youtube.com/watch?v=WSPstecsF90
# 06/02/2022

import pygame
import os
import random
# Biblioteca para rodar o algorítimo NEAT da rede neural
import neat

# Variáveis globais para uso da IA (NÃO É RECOMENDADO FAZER DESSA FORMA)
ai_jogando = True   # Módulo de jogo:  True - ( IA joga); False - ( Usuário joga)
geracao = 0         # Geração inicial da IA

# Constantes da janela do jogo
TELA_LARGURA = 500
TELA_ALTURA = 800

# pygame.transform.scale2x() para ampliar a imagem e 2 vezes
# os.path.join('imgs','pipe.png') para eu pegar a imagem que está dentro de uma pasta 'imgs' e não o mesmo diretório do execultável

IMAGEM_CANO = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'pipe.png')))
IMAGEM_CHAO = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'base.png')))
IMAGEM_BACKGROUND = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bg.png')))
IMAGES_PASSARO = [
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird1.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird2.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird3.png')))
]

# Configurando o texto da pontuação
pygame.font.init()
FONTE_PONTOS = pygame.font.SysFont('arial', 50)

class Passaro:
    IMGS = IMAGES_PASSARO
    # animação da rotação
    ROTACAO_MAXIMA = 25
    VELOCIDADE_ROTACAO = 20
    TEMPO_ANIMACAO = 5

    # atributos do pássaro
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angulo = 0
        self.velocidade = 0
        self.altura = self.y
        self.tempo = 0
        self.contagem_imagem = 0
        self.imagem = self.IMGS[0]

    def pular(self):
        self.velocidade = -10.5
        self.tempo = 0
        self.altura = self.y

    def mover(self):
        # Calcular o deslocamento
        self.tempo += 1

        # Sf = So + Vo*Tempo - (aceleração*Tempo^2)/2
        deslocamento = 1.5*(self.tempo**2) + self.velocidade*self.tempo

        # Restrigir o deslocamento
        if deslocamento > 16:
            deslocamento = 16
        elif deslocamento < 0:
            # Para dar um ganho inicial quando o pássaro pula
            deslocamento -= 2

        self.y += deslocamento

        # ângulo do pássaro
        if deslocamento < 0 or self.y < (self.altura + 50):
            if self.angulo < self.ROTACAO_MAXIMA:
                self.angulo = self.ROTACAO_MAXIMA
        else:
            if self.angulo > -90:
                self.angulo -= self.VELOCIDADE_ROTACAO

    def desenhar(self, tela):
        # Definir qual imagem do pássaro será usada
        self.contagem_imagem += 1
        if self.contagem_imagem < self.TEMPO_ANIMACAO:
            self.imagem = self.IMGS[0]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO * 2:
            self.imagem = self.IMGS[1]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO * 3:
            self.imagem = self.IMGS[2]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO * 4:
            self.imagem = self.IMGS[1]
        elif self.contagem_imagem < self.TEMPO_ANIMACAO * 4 + 1:
            self.imagem = self.IMGS[0]
            self.contagem_imagem = 0

        # Se o pássaro cai -> não bate a assa ( imagem fixa)
        if self.angulo < -80:
            self.imagem = self.IMGS[1]
            self.contagem_imagem = self.TEMPO_ANIMACAO * 2

        # Desehar a imagem
        imagem_rotacionada = pygame.transform.rotate(self.imagem, self.angulo)
        pos_centro_imagem = self.imagem.get_rect(topleft=(self.x, self.y)).center
        retangulo = imagem_rotacionada.get_rect(center=pos_centro_imagem)
        tela.blit(imagem_rotacionada, retangulo.topleft)

    def get_mask(self):
        # Função para pegar a mascara do desenho do pássaro dentro do retâgulo
        return pygame.mask.from_surface(self.imagem)

class Cano:
    DISTANCIA = 200
    VELOCIDADE = 5

    def __init__(self, x):
        self.x = x
        self.altura = 0
        # Posição
        self.pos_topo = 0
        self.pos_base = 0

        #Imagem do cano
        self.CANO_TOPO = pygame.transform.flip(IMAGEM_CANO, False, True)  # Flipei a imagem original do cano somente na vertical
        self.CANO_BASE = IMAGEM_CANO

        # Parâmtro para definir se o cano já passou do pássaro
        self.passou = False

        # Função que vai gerar a altura do cano
        self.definir_altura()

    def definir_altura(self):
        self.altura = random.randrange(50, 450)
        self.pos_topo = self.altura - self.CANO_TOPO.get_height()
        self.pos_base = self.altura + self.DISTANCIA

    def mover(self):
        self.x -= self.VELOCIDADE

    def desenhar(self, tela):
        tela.blit(self.CANO_TOPO, (self.x, self.pos_topo))
        tela.blit(self.CANO_BASE, (self.x, self.pos_base))

    def colidir(self, passaro):
        passaro_mask = passaro.get_mask()
        topo_mask = pygame.mask.from_surface(self.CANO_TOPO)
        base_mask = pygame.mask.from_surface(self.CANO_BASE)

        distancia_topo = (self.x - passaro.x, self.pos_topo - round(passaro.y))  # Deve ser um número inteiro, por isso arredonda a posição y do pássaro
        distancia_base = (self.x - passaro.x, self.pos_base - round(passaro.y))

        # Variáveis do tipo bool para verificar se houve colisão ( se True = colidiu, se False = não colidiu)
        topo_ponto = passaro_mask.overlap(topo_mask, distancia_topo)  # para ver se tem 2 pixels iguais
        base_ponto = passaro_mask.overlap(base_mask, distancia_base)  # para ver se tem 2 pixels iguais

        # Verifica a colisão
        if topo_ponto or base_ponto:
            return True
        else:
            return False

class Chao:
    VELOCIDADE = 5
    LARGURA = IMAGEM_CHAO.get_width()
    IMAGEM = IMAGEM_CHAO

    def __init__(self, y):
        self.y = y
        self.x1 = 0                         # posição da imagem do 1º chão
        self.x2 = self.LARGURA              # posição da imagem do 2º chão

    def mover(self):
        self.x1 -= self.VELOCIDADE
        self.x2 -= self.VELOCIDADE

        # Jogando a imagem do chão para o início da fila
        if self.x1 + self.LARGURA < 0:
            self.x1 = self.x2 + self.LARGURA
        if self.x2 + self.LARGURA < 0:
            self.x2 = self.x1 + self.LARGURA

    def desenhar(self, tela):
        tela.blit(self.IMAGEM, (self.x1, self.y))
        tela.blit(self.IMAGEM, (self.x2, self.y))

def desenhar_tela(tela, passaros, canos, chao, pontos):
    tela.blit(IMAGEM_BACKGROUND, (0, 0))

    # Para futuro treinamento da IA - treinar vários pássaros de uma só vez
    for passaro in passaros:
        passaro.desenhar(tela)

    for cano in canos:
        cano.desenhar(tela)

    texto = FONTE_PONTOS.render(f"Pontuação: {pontos}", 1, (255, 255, 255))
    tela.blit(texto, (TELA_LARGURA - 10 - texto.get_width(), 10))

    # Informa na pela a geração da IA
    if ai_jogando:
        texto = FONTE_PONTOS.render(f"Geração: {geracao}", 1, (255, 255, 255))
        tela.blit(texto, (10, 10))

    chao.desenhar(tela)
    pygame.display.update()

def main(genomas, config_AI): # fitness function
    #Contador que indica quantas vezes a IA iniciaou o jogo
    global geracao  # geracao é uma variável global
    geracao += 1

    if ai_jogando:
        # Criar vários pássaros
        passaros = []
        redes = [] # lista de redes neurais que usará as configurações da lista_genoma
        lista_genomas = [] # Lista relativa as configurações do genoma da rede neura
        for _, genoma in genomas:   # genomas é uma lista de túplas (IDGenema, genoma), como não quero pegar o IDGenoma, eu uso o '_' o FOR
            rede = neat.nn.FeedForwardNetwork.create(genoma, config_AI)  # Criando a rede neural
            redes.append(rede)
            genoma.fitness = 0 # pontuação para treinar a rede neural (incentívos)
            lista_genomas.append(genoma)
            passaros.append(Passaro(230, 350))
    else:
        passaros = [Passaro(230, 350)]
    chao = Chao(730)
    canos = [Cano(700)]
    tela = pygame.display.set_mode((TELA_LARGURA, TELA_ALTURA))
    pontos = 0
    relogio = pygame.time.Clock()

    rodando = True  # Para dar um break na execulção do jogo
    while rodando:
        relogio.tick(30)

        # Interação com o usuário
        for evento in pygame.event.get():   # Se for detectado o evento de saida do jogo quando clica no "X" da janela
            if evento.type == pygame.QUIT:
                rodando = False
                pygame.quit()
                quit()
            if not ai_jogando:
                if evento.type == pygame.KEYDOWN: # Verifica se ocorreu algum evento no tecado
                    if evento.key == pygame.K_SPACE: # Se o evento foi a barra de espaço (pygame.K_ESCAPE = Esc)
                        for passaro in passaros:
                            passaro.pular()

        indice_cano = 0
        if len(passaros) > 0: # se ainda tiver passaro na lista
            # descobrir qual cano olhar
            if len(canos) > 1 and passaros[0].x > (canos[0].x + canos[0].CANO_TOPO.get_width()):
                indice_cano = 1
        else: # todos os pássaros morreram
            rodando = False
            break

        # Mover os objetos do jogo
        for i, passaro in enumerate(passaros):
            passaro.mover()
            if ai_jogando:
                # aumentar um pouco a fitness do pássaro
                lista_genomas[i].fitness += 0.1
                output = redes[i].activate((passaro.y,
                                            abs(passaro.y - canos[indice_cano].altura),
                                            abs(passaro.y - canos[indice_cano].pos_base))) #.activate((input1, input2, input3))
                # -1 e 1 -> se o output for > 0,5 o pássaro pula
                if output[0] > 0.5:
                    passaro.pular()
        chao.mover()

        adicioar_cano = False
        remover_canos = []
        for cano in canos:
            for i, passaro in enumerate(passaros):
                if cano.colidir(passaro):   # Se o passaro colidiu com o cano
                    passaros.pop(i) # Retiro meu pássaro que morreu da lista de pássaros
                    if ai_jogando:
                        lista_genomas[i].fitness -= 1
                        lista_genomas.pop(i)
                        redes.pop(i)
                if not cano.passou and passaro.x > cano.x:  # Por defiição cano.passou = False, mas se o pássarou passou do cano, então atualiza
                    cano.passou = True
                    adicioar_cano = True
            cano.mover()
            if cano.x + cano.CANO_TOPO.get_width() < 0: # Cano saiu da TELA
                remover_canos.append(cano)

        if adicioar_cano:
            pontos += 1
            canos.append(Cano(600))
            if ai_jogando:
                for genoma in lista_genomas:
                    genoma.fitness += 5
        for cano in remover_canos:
            canos.remove(cano)

        for i, passaro in enumerate(passaros):  # Verificar se ele colidiu com o topo da tela ou o chão
            if(passaro.y + passaro.imagem.get_height()) > chao.y or passaro.y < 0:
                passaros.pop(i) # Remove o pássaro da lista
                if ai_jogando:
                    lista_genomas.pop(i)
                    redes.pop(i)

        desenhar_tela(tela, passaros, canos, chao, pontos)

def rodar(caminho_config_IA): # Onde será configurada a IA ( pegar o gonfig ) e chamar a main()
    config = neat.config.Config(neat.DefaultGenome,
                                neat.DefaultReproduction,
                                neat.DefaultSpeciesSet,
                                neat.DefaultStagnation,
                                caminho_config_IA)

    populacao = neat.Population(config)

    ##### ESTATÍSTICAS DO RESULTADO DO APRENDIZADO####
    populacao.add_reporter(neat.StdOutReporter(True))
    populacao.add_reporter(neat.StatisticsReporter())

    if ai_jogando:
        populacao.run(main, 50) # Rodar a main por 50 geração. Se não usasse nada, ele iria para no que foi determina do o arquivo config_IA
    else:
        main(None, None)

if __name__ == '__main__':
    caminho = os.path.dirname(__file__)
    caminho_config_IA = 'config_IA.txt'
    rodar(caminho_config_IA)
