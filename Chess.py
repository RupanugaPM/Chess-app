import pygame, sys, random , time

width=800
height=800

clock = pygame.time.Clock()
pygame.init() # initiates pygame
pygame.display.set_caption('Chess')
WINDOW_SIZE = (width,height)
screen = pygame.display.set_mode(WINDOW_SIZE,0,32) # initiate the window

"""k king
p pawn
n knight
q queen
b bishop
r rook
♜	♞	♝	♛	♚ black
♖	♘	♗	♕	♔ white
♔
U+2654
♕
U+2655
♖
U+2656
♗
U+2657
♘
U+2658
♙
U+2659
♚
U+265A
♛
U+265B
♜
U+265C
 ♝
U+265D
♞
U+265E
♟
Black Chess Pawn

"""


class Chess():
    def __init__(self):        
        self.boarddimension=100
        self.board=[["rb","nb","bb","qb","kb","bb","nb","rb"],["pb","pb","pb","pb","pb","pb","pb","pb"],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],["pw","pw","pw","pw","pw","pw","pw","pw"],["rw","nw","bw","qw","kw","bw","nw","rw"]]
        self.boardcolor=[(124,252,0),(0,0,0)] #!st is black squares and next one is white squarescolors
        #self.boardhasbeenclicked=Falsecthis can be checked by seeing if legal moves list is empty or not so i removed it
        self.turn=True #True for white false for black
        self.touchedpiece=[]
        self.legalmoves=[]
        self.movingpieces=["rw","nw","bw","qw","kw","pw","rb","nb","bb","qb","kb","pb"]
        self.movingpiecesd=["♖","♘","♗","♕","\u2654","♙","♜","♞","♝","♛","♚","♟"]
        self.legalmoveradius=10
        self.mouse=pygame.mouse.get_pos()
        self.radius=15
        self.krrb=[False,False,False]
        self.krrw=[False,False,False]
        self.promotionchosen=False
        self.knight=[[2,1],[-2,1],[2,-1],[-2,-1],[1,2],[-1,2],[1,-2],[-1,-2]]
        self.bishop=[[1,1],[-1,1],[1,-1],[-1,-1]]
        self.rook=[[1,0],[0,1],[-1,0],[0,-1]]
        self.royal=[[1,0],[0,1],[-1,0],[0,-1],[1,1],[-1,1],[1,-1],[-1,-1]]
        """
    def promotion(self):
        pass
    def pawn(self):
        if self.touchedpiece[0][-1]=="b":
            if self.touchedpiece[1][1]<7 and self.touchedpiece[1][0]<7 and self.board[self.touchedpiece[1][1]+1][self.touchedpiece[1][0]+1]!=0:
                self.legalmoves.append([self.touchedpiece[1][1]+1,self.touchedpiece[1][0]+1])
            if self.touchedpiece[1][1]<7 and self.touchedpiece[1][0]>0 and self.board[self.touchedpiece[1][1]+1][self.touchedpiece[1][0]-1]!=0:
                self.legalmoves.append([self.touchedpiece[1][1]+1,self.touchedpiece[1][0]-1])
            if self.touchedpiece[1][1]<7 and self.board[self.touchedpiece[1][1]+1][self.touchedpiece[1][0]]==0:
                    self.legalmoves.append([self.touchedpiece[1][1]+1,self.touchedpiece[1][0]])
            if self.touchedpiece[1][1]==1:
                #j then i for self.board
                if self.board[self.touchedpiece[1][1]+1][self.touchedpiece[1][0]]==0:
                    if self.board[self.touchedpiece[1][1]+2][self.touchedpiece[1][0]]==0:
                        self.legalmoves.append([self.touchedpiece[1][1]+2,self.touchedpiece[1][0]])          
        if self.touchedpiece[0][-1]=="w":
            
            if self.touchedpiece[1][1]>0 and self.touchedpiece[1][0]<7 and self.board[self.touchedpiece[1][1]-1][self.touchedpiece[1][0]+1]!=0:
                self.legalmoves.append([self.touchedpiece[1][1]-1,self.touchedpiece[1][0]+1])
            if self.touchedpiece[1][1]>0 and self.touchedpiece[1][0]>0 and self.board[self.touchedpiece[1][1]-1][self.touchedpiece[1][0]-1]!=0:
                self.legalmoves.append([self.touchedpiece[1][1]-1,self.touchedpiece[1][0]-1])
            if self.touchedpiece[1][1]>0 and self.board[self.touchedpiece[1][1]-1][self.touchedpiece[1][0]]==0:
                    self.legalmoves.append([self.touchedpiece[1][1]-1,self.touchedpiece[1][0]])
            if self.touchedpiece[1][1]==6:
                #j then i for self.board
                if self.board[self.touchedpiece[1][1]-1][self.touchedpiece[1][0]]==0:
                    if self.board[self.touchedpiece[1][1]-2][self.touchedpiece[1][0]]==0:
                        self.legalmoves.append([self.touchedpiece[1][1]-2,self.touchedpiece[1][0]])      
    def knight(self):
        pass
    def bishop(self):
        pass
    def rook(self):
        pass
    def queen(self):
        pass
    def king(self):
        pass
    def check(self):
        pass
    """
    def update(self):
        self.mouse=pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if len(self.legalmoves)!=0:
                    if [self.mouse[1]//100,self.mouse[0]//100] in self.legalmoves:
                        if self.touchedpiece[0][0]=="p":
                            if self.touchedpiece[0][-1]=="w" and self.board[self.mouse[1]//100][self.mouse[0]//100]=="sb":
                                self.board[self.mouse[1]//100+1][self.mouse[0]//100]=0
                            if self.touchedpiece[0][-1]=="b" and self.board[self.mouse[1]//100][self.mouse[0]//100]=="sw":
                                self.board[self.mouse[1]//100-1][self.mouse[0]//100]=0      
                        self.board[self.mouse[1]//100][self.mouse[0]//100]=self.touchedpiece[0]
                        self.board[self.touchedpiece[1][1]][self.touchedpiece[1][0]]=0
                        for i in range(len(self.board)):
                            for j in range(len(self.board[i])):
                                if self.board[i][j]==0:
                                    pass
                                elif self.board[i][j][0]=="s":
                                    self.board[i][j]=0
                                else:
                                    pass
                        if self.touchedpiece[0][0]=="p":
                            if self.touchedpiece[0][-1]=="w":
                                if self.touchedpiece[1][1]==6 and self.mouse[1]//100==4:
                                    self.board[5][self.mouse[0]//100]="sw"
                            if self.touchedpiece[0][-1]=="b":
                                if self.touchedpiece[1][1]==1 and self.mouse[1]//100==3:
                                    self.board[2][self.mouse[0]//100]="sb"         

                        self.touchedpiece=[]
                        self.legalmoves=[]
                        self.turn=not self.turn
                if self.board[self.mouse[1]//100][self.mouse[0]//100]!=0:
                    self.touchedpiece=[self.board[self.mouse[1]//100][self.mouse[0]//100],[self.mouse[0]//100,self.mouse[1]//100]]
                    self.legalmoves=[]
                    print(self.touchedpiece)#rows in 1 and columns at 0 
                    
                    if self.turn==True and self.touchedpiece[0][-1]=="b":
                        self.touchedpiece=[]
                    elif self.turn==False and self.touchedpiece[0][-1]=="w":
                        self.touchedpiece=[]                        
                else:
                    self.touchedpiece=[]
        #comment
        try:
            if len(self.legalmoves)==0: 
                if self.touchedpiece[0][0]=="p":
                    if self.touchedpiece[0][-1]=="b":
                        if self.touchedpiece[1][1]<7 and self.touchedpiece[1][0]<7 and self.board[self.touchedpiece[1][1]+1][self.touchedpiece[1][0]+1]!=0 and self.board[self.touchedpiece[1][1]+1][self.touchedpiece[1][0]+1][-1]!="b":
                            self.legalmoves.append([self.touchedpiece[1][1]+1,self.touchedpiece[1][0]+1])
                        if self.touchedpiece[1][1]<7 and self.touchedpiece[1][0]>0 and self.board[self.touchedpiece[1][1]+1][self.touchedpiece[1][0]-1]!=0 and self.board[self.touchedpiece[1][1]+1][self.touchedpiece[1][0]-1][-1]!="b":
                            self.legalmoves.append([self.touchedpiece[1][1]+1,self.touchedpiece[1][0]-1])
                        if self.touchedpiece[1][1]<7 and self.board[self.touchedpiece[1][1]+1][self.touchedpiece[1][0]]==0:
                                self.legalmoves.append([self.touchedpiece[1][1]+1,self.touchedpiece[1][0]])
                        if self.touchedpiece[1][1]==1:
                            #j then i for self.board
                            if self.board[self.touchedpiece[1][1]+1][self.touchedpiece[1][0]]==0:
                                if self.board[self.touchedpiece[1][1]+2][self.touchedpiece[1][0]]==0:
                                    self.legalmoves.append([self.touchedpiece[1][1]+2,self.touchedpiece[1][0]])          
                    if self.touchedpiece[0][-1]=="w":
                        
                        if self.touchedpiece[1][1]>0 and self.touchedpiece[1][0]<7 and self.board[self.touchedpiece[1][1]-1][self.touchedpiece[1][0]+1]!=0 and self.board[self.touchedpiece[1][1]-1][self.touchedpiece[1][0]+1][-1]!="w":
                            self.legalmoves.append([self.touchedpiece[1][1]-1,self.touchedpiece[1][0]+1])
                        if self.touchedpiece[1][1]>0 and self.touchedpiece[1][0]>0 and self.board[self.touchedpiece[1][1]-1][self.touchedpiece[1][0]-1]!=0 and self.board[self.touchedpiece[1][1]-1][self.touchedpiece[1][0]-1][-1]!="w":
                            self.legalmoves.append([self.touchedpiece[1][1]-1,self.touchedpiece[1][0]-1])
                        if self.touchedpiece[1][1]>0 and self.board[self.touchedpiece[1][1]-1][self.touchedpiece[1][0]]==0:
                                self.legalmoves.append([self.touchedpiece[1][1]-1,self.touchedpiece[1][0]])

                        if self.touchedpiece[1][1]==6:
                            #j then i for self.board
                            if self.board[self.touchedpiece[1][1]-1][self.touchedpiece[1][0]]==0:
                                if self.board[self.touchedpiece[1][1]-2][self.touchedpiece[1][0]]==0:
                                    self.legalmoves.append([self.touchedpiece[1][1]-2,self.touchedpiece[1][0]])              
                elif self.touchedpiece[0][0]=="n":
                    if self.touchedpiece[0][-1]=="b":
                        for i in self.knight:
                            if i[0]+self.touchedpiece[1][1]<=7 and i[0]+self.touchedpiece[1][1]>=0 and i[1]+self.touchedpiece[1][0]>=0 and i[1]+self.touchedpiece[1][0]<=7 and (self.board[i[0]+self.touchedpiece[1][1]][i[1]+self.touchedpiece[1][0]]==0 or self.board[i[0]+self.touchedpiece[1][1]][i[1]+self.touchedpiece[1][0]][-1]!="b"):
                                self.legalmoves.append([i[0]+self.touchedpiece[1][1],i[1]+self.touchedpiece[1][0]])
 
                    if self.touchedpiece[0][-1]=="w":
                        for i in self.knight:
                            if i[0]+self.touchedpiece[1][1]<=7 and i[0]+self.touchedpiece[1][1]>=0 and i[1]+self.touchedpiece[1][0]>=0 and i[1]+self.touchedpiece[1][0]<=7 and (self.board[i[0]+self.touchedpiece[1][1]][i[1]+self.touchedpiece[1][0]]==0 or self.board[i[0]+self.touchedpiece[1][1]][i[1]+self.touchedpiece[1][0]][-1]!="w"):
                                self.legalmoves.append([i[0]+self.touchedpiece[1][1],i[1]+self.touchedpiece[1][0]])

                elif self.touchedpiece[0][0]=="b":
                    if self.touchedpiece[0][-1]=="b":
                        for i in self.bishop:
                            for j in range(1,8):
                                if i[0]*j+self.touchedpiece[1][1]<=7 and i[0]*j+self.touchedpiece[1][1]>=0 and i[1]*j+self.touchedpiece[1][0]>=0 and i[1]*j+self.touchedpiece[1][0]<=7 and (self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="b"):
                                    if self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][0]=="s":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                    elif self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="b":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                        break
                                else:
                                    break
                    if self.touchedpiece[0][-1]=="w":
                        for i in self.bishop:
                            for j in range(1,8):
                                if i[0]*j+self.touchedpiece[1][1]<=7 and i[0]*j+self.touchedpiece[1][1]>=0 and i[1]*j+self.touchedpiece[1][0]>=0 and i[1]*j+self.touchedpiece[1][0]<=7 and (self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="w"):
                                    if self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][0]=="s":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                    elif self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="w":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                        break
                                else:
                                    break
                elif self.touchedpiece[0][0]=="r":
                    if self.touchedpiece[0][-1]=="b":
                        for i in self.rook:
                            for j in range(1,8):
                                if i[0]*j+self.touchedpiece[1][1]<=7 and i[0]*j+self.touchedpiece[1][1]>=0 and i[1]*j+self.touchedpiece[1][0]>=0 and i[1]*j+self.touchedpiece[1][0]<=7 and (self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="b"):
                                    if self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][0]=="s":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                    elif self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="b":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                        break
                                else:
                                    break
                    if self.touchedpiece[0][-1]=="w":
                        for i in self.rook:
                            for j in range(1,8):
                                if i[0]*j+self.touchedpiece[1][1]<=7 and i[0]*j+self.touchedpiece[1][1]>=0 and i[1]*j+self.touchedpiece[1][0]>=0 and i[1]*j+self.touchedpiece[1][0]<=7 and (self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="w"):
                                    if self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][0]=="s":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                    elif self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="w":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                        break
                                else:
                                    break
                elif self.touchedpiece[0][0]=="q":
                    if self.touchedpiece[0][-1]=="b":
                        for i in self.royal:
                            for j in range(1,8):
                                if i[0]*j+self.touchedpiece[1][1]<=7 and i[0]*j+self.touchedpiece[1][1]>=0 and i[1]*j+self.touchedpiece[1][0]>=0 and i[1]*j+self.touchedpiece[1][0]<=7 and (self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="b"):
                                    if self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][0]=="s":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                    elif self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="b":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                        break
                                else:
                                    break
                    if self.touchedpiece[0][-1]=="w":
                        for i in self.royal:
                            for j in range(1,8):
                                if i[0]*j+self.touchedpiece[1][1]<=7 and i[0]*j+self.touchedpiece[1][1]>=0 and i[1]*j+self.touchedpiece[1][0]>=0 and i[1]*j+self.touchedpiece[1][0]<=7 and (self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="w"):
                                    if self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][0]=="s":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                    elif self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="w":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                        break
                                else:
                                    break                                 
                elif self.touchedpiece[0][0]=="k":
                    if self.touchedpiece[0][-1]=="b":
                        for i in self.royal:
                            for j in range(1,2):
                                if i[0]*j+self.touchedpiece[1][1]<=7 and i[0]*j+self.touchedpiece[1][1]>=0 and i[1]*j+self.touchedpiece[1][0]>=0 and i[1]*j+self.touchedpiece[1][0]<=7 and (self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="b"):
                                    if self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][0]=="s":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                    elif self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="b":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                        break
                                else:
                                    break
                    if self.touchedpiece[0][-1]=="w":
                        for i in self.royal:
                            for j in range(1,2):
                                if i[0]*j+self.touchedpiece[1][1]<=7 and i[0]*j+self.touchedpiece[1][1]>=0 and i[1]*j+self.touchedpiece[1][0]>=0 and i[1]*j+self.touchedpiece[1][0]<=7 and (self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="w"):
                                    if self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]]==0 or self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][0]=="s":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                    elif self.board[i[0]*j+self.touchedpiece[1][1]][i[1]*j+self.touchedpiece[1][0]][-1]!="w":
                                        self.legalmoves.append([i[0]*j+self.touchedpiece[1][1],i[1]*j+self.touchedpiece[1][0]])
                                        break
                                else:
                                    break   
        except:
            pass

    def show(self):
        for i in range(8):
            for j in range(8):
                try:
                    if [i,j]==self.touchedpiece[1]:
                        pygame.draw.rect(screen, (155,0,0), (i*self.boarddimension, j*self.boarddimension, self.boarddimension, self.boarddimension))
                    else:
                        pygame.draw.rect(screen, self.boardcolor[1] if (i+j)%2==0 else self.boardcolor[0], (i*self.boarddimension, j*self.boarddimension, self.boarddimension, self.boarddimension))
                        
                except:
                    pygame.draw.rect(screen, self.boardcolor[1] if (i+j)%2==0 else self.boardcolor[0], (i*self.boarddimension, j*self.boarddimension, self.boarddimension, self.boarddimension))
        for i in range(len(self.board)):
            for j in range(len(self.board[i])):
                if self.board[i][j]==0 or self.board[i][j][0]=="s":
                    pass
                else:
                    self.font=pygame.font.Font('Quivira.ttf', int(self.boarddimension))
                    self.text = self.font.render(self.movingpiecesd[self.movingpieces.index(self.board[i][j])], True, (165,142,142))
                    self.textRect = self.text.get_rect()
                    self.textRect.center= (j*100+self.boarddimension/2, i*100+self.boarddimension/2)
                    screen.blit(self.text, self.textRect)
        try:
            for i in self.legalmoves:
                pygame.draw.circle(screen, (255,255,255), [i[1]*100+self.boarddimension//2,i[0]*100+ self.boarddimension//2], 10)
        except:
            pass

l=Chess()
t1=time.time()
t2=time.time()
while True: # game loop
    screen.fill((0,0,0))
    #spd=pygame.mouse.get_pos()[0]/16

    l.update()
    l.show()

    keys = pygame.key.get_pressed()
    #moving charecter
    """if keys[pygame.K_a]:
        time.sleep(1)"""
    pygame.display.update()
    clock.tick(60)

