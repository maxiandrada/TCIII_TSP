import copy
from Solucion import Solucion

class camino(object):
    def __init__(self, s, g, demandas, capacidad, matrizDistancias):
        self.__demandas = demandas
        self.__capacidad = capacidad
        self.__matrizDistancias = matrizDistancias
        if not (self.solucionFactible(s) and self.solucionFactible(g)):
            raise Exception("SolucionesInfactibles")
        else:
            self.__s = s
            self.__g = g
            self.__indS = [0,1] #(ruta, vertice)
            self.__indG = [0,1]
            self.__condMT = self.igualesTam()
            self.__condMR = self.igualesRec()
            self.generaCamino()

    def pathRelinking(self):
        rutas = []
        for sec in self.__s:
            S = Solucion(self.__matrizDistancias, self.__demandas, 0)
            # cap = S.cargarDesdeSecuenciaDeVertices(S.cargaVertices(sec, False))
            cap = S.cargaGrafoDesdeSec(sec)
            S.setCapacidad(cap)
            S.setCapacidadMax(self.__capacidad)
            rutas.append(S)
        self.generaCamino()
        self.chequeaConsistencia(self.__s)
        return rutas

    def pathRelinking2(self):
        self.generaCamino()
        self.chequeaConsistencia(self.__s)
        return self.__s

    def chequeaConsistencia(self, sol):
        v = 2
        inconsistente = False
        while v < len(self.__matrizDistancias) and not inconsistente:
            cont = 0
            for ruta in sol:
                if v in ruta:
                    cont += 1
            if not cont == 1:
                inconsistente = True
                print ("Algo anda mal con path relinking ")
                print (str(sol))
                raise Exception("SolucionesInfactibles")
            else:
                v += 1
        if not self.solucionFactible(self.__s):
            print ("ALGO ANDA MAL CON LA FACTIBILIDAD "+str(self.__s))

            raise Exception ("SolucionesInfactibles")

    def setSol(self, s, g):
        if not (self.solucionFactible(s) and self.solucionFactible(g)):
            raise Exception("SolucionesInfactibles")
        else:
            self.__s = s
            self.__g = g
            self.__indS = [0,1] #(ruta, vertice)
            self.__indG = [0,1]
            self.__condMT = self.igualesTam()
            self.__condMR = self.igualesRec()
            self.generaCamino()

    def solucionFactible(self, p):
        i = 0
        while i < len(p) and self.rutaFactible(p[i]):
            i+=1
        return False if i < len(p) else True

    def rutaFactible(self, ruta):
        acu = 0.0
        # print (str(ruta))
        # cad = "acu = "
        for i in range(len(ruta)):
            acu += self.__demandas[ruta[i]-1]
            # cad += str(self.__demandas[ruta[i]-1])
        # print (cad)
        return False if acu > self.__capacidad else True

    def igualesTam(self):
        i = 0
        while i < len(self.__s) and len(self.__s[i]) == len(self.__g[i]):
            i += 1
        if i<len(self.__s):
            return False
        else:
            return True

    def igualesRec(self):
        indS = [0,1]
        indG = [0,1]
        band = True
        while band and indS!= None and indG!=None:
            if self.__s[indS[0]][indS[1]] != self.__g[indG[0]][indG[1]]:
                band = False
            indS = self.incIndS(indS)
            indG = self.incIndG(indG)
        if band:
            return True
        else:
            return False

    def generaCamino (self):
        # # print ("----inicio pr----")
        aux1 = -1
        aux2 = -1
        if not self.iguales():  #caso en que ya sean iguales
            if not self.__condMR:
                aux1 = self.__s[self.__indS[0]][self.__indS[1]]
                aux2 = self.__g[self.__indG[0]][self.__indG[1]]
                if aux1 == aux2:
                    self.__indS=self.incIndS(self.__indS)
                    self.__indG=self.incIndG(self.__indG)
                    self.__condMR = self.igualesRec()
                    print ("entro 1")
                    return self.generaCamino() if self.__indS != None and self.__indG != None else []
                self.__s[self.__indS[0]][self.__indS[1]] = aux2

                indS=self.incIndS(self.__indS) 
                indG=self.incIndG(self.__indG)
                if indS!=None and indG!=None:
                    # # print ("Los indices no son None")
                    auxRuta = self.__indS[0]
                    self.__indS=self.incIndS(self.__indS) 
                    self.__indG=self.incIndG(self.__indG)            
                    # # print ("indices:"+str(self.__indS)+str(self.__indG))
                    band = True
                    while indS!=None and band:
                        if self.__s[indS[0]][indS[1]] == aux2:
                            self.__s[indS[0]][indS[1]] = aux1
                            band = False
                        else:
                            indS = self.incIndS(indS)
                    self.__condMR = self.igualesRec()
                    if indS!= None and self.rutaFactible(self.__s[auxRuta]) and self.rutaFactible(self.__s[indS[0]]):
                        print ("entro 2")
                        return self.__s
                    else:
                        print ("entro 3")
                        return self.generaCamino()
                else:
                    print ("entro 4")
                    self.__condMR = self.igualesRec()
                    return self.__s
            elif not self.__condMT:
                i = 0
                b = True
                while b and i < len(self.__s):
                    if len(self.__s[i]) < len(self.__g[i]):
                        aux3=self.__s[i+1].pop(1)
                        self.__s[i].append(aux3)
                        b = False
                        b2 = self.rutaFactible(self.__s[i]) and self.rutaFactible(self.__s[i+1])
                    elif len(self.__s[i]) > len(self.__g[i]):
                        aux3 = self.__s[i].pop(-1)
                        self.__s[i+1].insert(1, aux3)
                        b = False
                        b2 = self.rutaFactible(self.__s[i]) and self.rutaFactible(self.__s[i+1])
                    else:
                        i+=1
                self.__condMT = self.igualesTam()
                if b2:
                    print ("entro 5")
                    return [] if self.__condMT else self.__s
                else:
                    print ("entro 6")
                    return self.generaCamino()
            else:
                # # print ("Ya llegamos a la solución guía")
                return []
        else:
            # # print ("Ya llegamos a la solución guía")
            return []

    def incIndS(self, indS):
        ind = copy.deepcopy(indS)
        if ind != None:
            if ind[1]+1 < len(self.__s[ind[0]]):
                ind[1]+=1
                return ind
            else:
                if ind[0]+1 < len(self.__s):
                    ind[0]+=1
                    ind[1]=1
                    return ind
                else:
                    return None #es el último de la secuencia
        else:
            return None

    def incIndG(self, indG):
        ind = copy.deepcopy(indG)
        if ind != None:
            if ind[1]+1 < len(self.__g[ind[0]]):
                ind[1]+=1
                return ind
            else:
                if ind[0]+1 < len(self.__g):
                    ind[0]+=1
                    ind[1]=1
                    return ind
                else:
                    return None #es el último de la secuencia
        else:
            return None

    def iguales(self):
        if self.__condMT and self.__condMR:
            return True
        else:
            return False
    

#### SECCION DE PRUEBAS ####

# s = [[1,4,5,2],[1,9,8,3],[1,6,7,10]]
# g = [[1,2,3,4,9],[1,5,7,8],[1,6,10]]
# demandas = [0.0,2.0,4.0,2.0,5.0,6.0,7.0,6.0,3.0,4.0]
# capacidad = 100


# s= [[1, 4, 3, 18, 20, 32, 22], [1, 7, 24, 29, 5, 12, 9, 19, 10, 23], [1, 17, 8, 14, 2, 13], [1, 21, 6, 26, 11, 16, 30, 28], [1, 25, 15, 27, 31]]
# g= [[1, 23, 10, 19, 9, 12, 5, 29, 24, 7], [1, 4, 3, 18, 20, 32, 22], [1, 17, 8, 14, 2, 13], [1, 30, 16, 11, 26, 6, 21], [1, 28, 25, 15, 27, 31]]
# demandas = [0.0, 19.0, 21.0, 6.0, 19.0, 7.0, 12.0, 16.0, 6.0, 16.0, 8.0, 14.0, 21.0, 16.0, 3.0, 22.0, 18.0, 19.0, 1.0, 24.0, 8.0, 12.0, 4.0, 8.0, 24.0, 24.0, 2.0, 20.0, 15.0, 2.0, 14.0, 9.0]
# capacidad = 100

# try:
#     print (str(s)+" Solucion")
#     caminito = camino(s, g, demandas, capacidad, [])
#     c = caminito.pathRelinking2()
#     print(str(c))
#     while not caminito.iguales():
#         c = caminito.pathRelinking2()
#         print (str(c)+str(caminito.iguales()))
#     print (str(caminito.iguales()))
#     print (str(g)+" Guia")
# except Exception as e:
#     print (e)
# print (str(s))

# [[1, 4, 3, 18, 20, 32, 22], [1, 7, 24, 29, 5, 12, 9, 19, 10, 23], [1, 17, 8, 14, 2, 13], [1, 21, 6, 26, 11, 16, 30, 28], [1, 25, 15, 27, 31]]
# # [[1, 23, 10, 19, 9, 12, 5, 29, 24, 7], [1, 4, 3, 18, 20, 32, 22], [1, 17, 8, 14, 2, 13], [1, 30, 16, 11, 26, 6, 21], [1, 28, 25, 15, 27, 31]]

# [[1, 4, 3, 18, 20, 32, 22], [1, 7, 24, 29, 5, 12, 9, 19, 10, 23], [1, 17, 8, 14, 2, 13], [1, 28, 30, 16, 11, 26, 6, 21], [1, 25, 15, 27, 31]]
# Se estancó durante 0 min 10 seg. Admitimos una solucion peor para diversificar en nodo 1-->    Costo: 833.532
# [[1, 23, 10, 19, 9, 12, 5, 29, 24, 7], [1, 4, 3, 18, 20, 32, 22], [1, 17, 8, 14, 2, 13], [1, 30, 16, 11, 26, 6, 21], [1, 28, 25, 15, 27, 31]]
# Se estancó durante 0 min 9 seg en path relinking. Admitimos una solución de path relinking -->    Costo: 938.076
# Parto de otra sol inicial para path relinking
# [[1, 23, 3, 18, 20, 32, 22], [1, 7, 24, 29, 5, 12, 9, 19, 10, 4], [1, 17, 8, 14, 2, 13], [1, 21, 6, 26, 11, 16, 30, 28], [1, 25, 15, 27, 31]]
# [[1, 23, 10, 19, 9, 12, 5, 29, 24, 7], [1, 4, 3, 18, 20, 32, 22], [1, 17, 8, 14, 2, 13], [1, 30, 16, 11, 26, 6, 21], [1, 28, 25, 15, 27, 31]]
# Se estancó durante 0 min 10 seg en path relinking. Admitimos una solución de path relinking -->    Costo: 947.338
# Se estancó durante 0 min 10 seg. Admitimos una solucion peor para diversificar en nodo 1-->    Costo: 869.328
# Parto de otra sol inicial para path relinking
# [[1, 23, 3, 18, 20, 32, 22], [1, 7, 24, 29, 5, 12, 9, 19, 10, 4], [1, 17, 8, 14, 2, 13], [1, 28, 30, 16, 11, 26, 6, 21], [1, 25, 15, 27, 31]]
# [[1, 23, 10, 19, 9, 12, 5, 29, 24, 7], [1, 4, 3, 18, 20, 32, 22], [1, 17, 8, 14, 2, 13], [1, 30, 16, 11, 26, 6, 21], [1, 28, 25, 15, 27, 31]]