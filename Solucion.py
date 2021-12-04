from Grafo import Grafo 
from Vertice import Vertice 
from Arista import Arista
import copy
import sys
import random
import math
import numpy as np
from time import time

class Solucion(Grafo):
    def __init__(self, M, Demanda, capacidad,G=None,vacio=False):
        super(Solucion, self).__init__(M, Demanda,G,vacio=vacio)
        self.__capacidad = capacidad
        self.__capacidadMax = 0

    def __str__(self):
        cad = "\nRecorrido de la solución: " + str(self.getV()) + "\n" + "Aristas de la solución: "+ str(self.getA())
        cad += "\nCosto Asociado: " + str(round(self.getCostoAsociado(),3)) + "        Capacidad: "+ str(self.__capacidad)
        return cad
    def __repr__(self):
        return str(self.getV())
    def __eq__(self, otro):
        return (self._costoAsociado == otro._costoAsociado and self.__class__ == otro.__class__)
    def __ne__(self, otro):
        return (self._costoAsociado != otro._costoAsociado and self.__class__ == otro.__class__)
    def __gt__(self, otro):
        return self._costoAsociado > otro._costoAsociado
    def __lt__(self, otro):
        return self._costoAsociado < otro._costoAsociado
    def __ge__(self, otro):
        return self._costoAsociado >= otro._costoAsociado
    def __le__(self, otro):
        return self._costoAsociado <= otro._costoAsociado
    def __len__(self):
        return len(self._V)
    def setCapacidadMax(self, capMax):
        self.__capacidadMax = capMax
    def setCapacidad(self, capacidad):
        self.__capacidad = capacidad
    def getCapacidad(self):
        return self.__capacidad
    def getCapacidadMax(self):
        return self.__capacidadMax
    #Longitud que debería tener cada solucion por cada vehiculo
    def longitudSoluciones(self, length, nroVehiculos):
        if(nroVehiculos == 0):
            return length
        length = (length/nroVehiculos)
        decimales = math.modf(length)[0]
        if decimales < 5.0:
            length = int(length)
        else:
            length = int(length)+1
        return length

    #Rutas iniciales o la primera solucion
    def rutasIniciales(self, strSolInicial, nroVehiculos, demandas, capacidad,G):
        rutas = []
        sol_factible = False
        _lambda = 1
        mu = ni = iteracion = 0
        Rant = None

        while(not sol_factible):
            rutas = []

            if(strSolInicial==0):
                print("Solucion inicial con Clark & Wright...")
                R, _lambda, mu, ni, iteracion, fact = self.clarkWright(nroVehiculos, _lambda, mu, ni, iteracion)

                if iteracion <= 1:
                    Rant = copy.deepcopy(R)
                        
                if not fact:
                    if(iteracion == 1):
                        print("No se encontro solucion factible con Clark & Wright probamos con otra")
                        sol_factible = False
                    print("aún nada u.u Seguimos probando con otras variaciones")                
                else:
                    rutas = self.cargarRutas(Rant, capacidad,G)
                    if len(rutas) > nroVehiculos:
                        print("Eliminando rutas sobrantes")
                        rutas = self.eliminarRutasSobrantes(rutas, nroVehiculos, capacidad)
                    
                    if rutas != []:
                        print("se encontro solución inicial factible :)")
                        sol_factible = True
                    else:
                        print("No se encontró sol factible. Probamos con una al azar")
                        strSolInicial = 3

            elif(strSolInicial==1):
                print("Sol Inicial por Vecino Cercano...")
                sol_factible = self.solInicial_VecinoCercano(nroVehiculos, capacidad, demandas, rutas, G)

                if sol_factible:
                    rutas = self.cargarRutas(rutas, capacidad,G)
                
                strSolInicial = 0
            
            elif(strSolInicial == 2):
                print("Sol Inicial secuencial...")
                secuenciaInd = list(range(1,len(self._matrizDistancias)))
                print("secuencia de indices de los vectores: "+str(secuenciaInd))
                sol_factible = self.cargar_secuencia(secuenciaInd, nroVehiculos, demandas, capacidad, rutas)
                strSolInicial = 3
            
            else:
                print("Sol Inicial al azar...")
                secuenciaInd = list(range(1,len(self._matrizDistancias)))
                random.shuffle(secuenciaInd)
                sol_factible = self.cargar_secuencia(secuenciaInd, nroVehiculos, demandas, capacidad, rutas)

        print("Cantidad de Vehículos "+ str(nroVehiculos)+" cantidad de rutas: "+str(len(rutas)))
        return rutas, strSolInicial
    
    #Cargar las rutas a partir de una lista de enteros
    def cargar_secuencia(self, secuencia, nroVehiculos, demandas, capacidad, rutas):
        secuenciaInd = secuencia
        sub_secuenciaInd = []
        
        for i in range(0,nroVehiculos):
            #Sin contar la vuelta (x,1)
            #nroVehiculos = 3
            #[1,2,3,4,5,6,7,8,9,10] Lo ideal seria: [1,2,3,4] - [1,5,6,7] - [1,8,9,10]
            sub_secuenciaInd = self.solucion_secuencia(secuenciaInd, capacidad, demandas, nroVehiculos)
            S = Solucion(self._matrizDistancias, self._demanda, 0)
            S.setCapacidadMax(capacidad)
            cap = S.cargarDesdeSecuenciaDeVertices(S.cargaVertices([0]+sub_secuenciaInd, True))
            S.setCapacidad(cap)
            rutas.append(S)
            secuenciaInd = [x for x in secuenciaInd if x not in set(sub_secuenciaInd)]
            i
        if len(secuenciaInd) > 0:
            print("La solucion inicial no es factible. Implementar luego....")
            return False
        else:
            return True

    #secuenciaInd: secuencia de Indices
    #capacidad: capacidad maxima de los vehiculos
    #demanda: demanda de cada cliente
    def solucion_secuencia(self, secuenciaInd, capacidad, demandas, nroVehiculos):
        acum_demanda = 0
        sub_secuenciaInd = []
        for x in secuenciaInd:
            value = self.getV()[x].getValue()-1
            if(acum_demanda + demandas[value] <= self.__capacidadMax):
                acum_demanda += demandas[value]
                sub_secuenciaInd.append(x)
                #if (acum_demanda > self.__capacidad/nroVehiculos):
                #    break
        
        return sub_secuenciaInd

    def solInicial_VecinoCercano(self, nroVehiculos, capacidad, demanda, rutas, G):
        visitados = []
        recorrido = []
        visitados.append(0)    #Agrego el vertice inicial
        V = [i for i in range(0, len(self.getV()))]

        for j in range(0, nroVehiculos):
            recorrido = [1]
            masCercano=0
            acum_demanda = 0
            for i in range(0,len(self._matrizDistancias)):
                masCercano = self.vecinoMasCercano(masCercano, visitados, acum_demanda, demanda, capacidad) #obtiene la posicion dela matriz del vecino mas cercano
                if(masCercano != 0):
                    acum_demanda += demanda[masCercano]
                    recorrido.append(masCercano+1)
                    visitados.append(masCercano)
                    V.remove(masCercano)
                if(acum_demanda > self.__capacidad/nroVehiculos):
                    break
                i
            j
            rutas.append(recorrido)

        if(len(visitados) < len(self.getV())):
            #V = np.arange(0, len(self.getV()))
            #noVisitados = [x for x in V if x not in V]
            recorrido = [(i+1) for i in V]
            print("recorrido: "+str(recorrido))
            rutas.append(recorrido)
            print("Solucion no factible. Repetimos proceso con otra solucion inicial")
            return False
        else:
            return True

    def vecinoMasCercano(self, pos, visitados, acum_demanda, demanda, capacidad):
        masCercano = self._matrizDistancias[pos][pos]
        indMasCercano = 0
    
        for i in range(0, len(self._matrizDistancias)):
            costo = self._matrizDistancias[pos][i]
            if(costo<masCercano and i not in visitados and demanda[i]+acum_demanda <= capacidad):
                masCercano = costo
                indMasCercano = i
        
        return indMasCercano

    def cargarRutas(self, rutas, capacidad,gr):
        R = []
        t = time()
        print("Se inició cargarRutas")
        for r in rutas:
            S = Solucion(self._matrizDistancias, self._demanda,capacidad,G=gr,vacio=True)
            #cap = S.cargarDesdeSecuenciaDeVertices(S.cargaVertices(r, False))
            cap = S.cargaGrafoDesdeSec(r)
            S.setCapacidad(cap)
            S.setCapacidadMax(capacidad)
            R.append(S)
        print("tiempo cargar rutas: ", time()-t)
        return R

    def mezclarRuta(self,r1,r2,rutas):
        #r1 y r2 son índices de las rutas.
        rutas[r1] = rutas[r1] + rutas[r2][1:]
    
    def obtenerAhorrosOncan(self,_lambda, mu,ni):
        t1 = time()
        print("empezó obtener ahorros")
        M = self._matrizDistancias
        D = self._demanda
        avgD = sum(D)/len(D)
        ahorros = []
        
        for i in range(1,len(M)-1):
            for j in range(i+1,len(M)):
                s = M[i][0]+ M[0][j]- _lambda*M[i][j] + mu * abs(M[i][0]-M[0][j]) + ni * ((D[i]-D[j])/avgD)
                t = (i+1,j+1,s)
                ahorros.append(t)
        print("tiempo obtener ahorros ", time()-t1)
        ahorros = sorted(ahorros, key=lambda x: x[2], reverse=True)
        return ahorros

    def obtenerAhorros(self):
        M = self._matrizDistancias
        ahorros = []
        for i in range(1,len(M)-1):
            for j in range(i+1,len(M)):
                s = M[i][0]+ M[0][j]-M[i][j] 
                s = round(s,3)
                t = (i+1,j+1,s)
                ahorros.append(t)
        ahorros = sorted(ahorros, key=lambda x: x[2], reverse=True)
        return ahorros
    
    def removerAhorros(self,lista,i,c):
        ret = [x for x in lista if x[i]!=c]
        return ret

    def buscar(self,v1,rutas):
        c = 0 #Indice cliente en ruta r
        r = 0 #Indice ruta
        cond = True
        while(r<len(rutas) and cond):
            if v1 in rutas[r]:
                cond = False
                c = rutas[r].index(v1)
            else:
                r+=1
        return (r, c)  

    def esInterno(self, c,ruta):
        if c in ruta:  
            posicion = ruta.index(c)
            if(1 < posicion and posicion < len(ruta)-1):
                return True
            else:
                return False
        else:
            return False

    def estaEnUnRutaNoVacia(self,v1,rutas):
        return len(rutas[v1])>2 

    def cargaTotal(self, dem,ruta):
        suma = 0
        for r in ruta:
            suma += dem[r-1]
        self.capacidad = suma
        return suma

    def removeRuta(self,index,rutas):
        rutas.pop(index) 

    def clarkWright(self, nroVehiculos, lambdaIni, muIni, niIni, nroIteracAntes):
        _lambda = lambdaIni
        mu = muIni
        ni = niIni
        # _lambda = 1
        # mu = 0
        # ni = 0
        t = time()
        #sol_factible = False
        iteracion = nroIteracAntes
        #while(not sol_factible):
        ahorros = self.obtenerAhorrosOncan(_lambda,mu,ni)
        # ahorros = self.obtenerAhorros()
        dem = self._demanda
        recargaAhorro = True
        rutas = [[1,i] for i in range(2,self.getGrado()+1)]
        print("inició clarke wright")
        fact = True

        while(len(ahorros)>0 and len(rutas)!=nroVehiculos):
            t2 = time()
            mejorAhorro = ahorros.pop(0)
            capacidadMax = self.__capacidadMax
            i = self.buscar(mejorAhorro[0],rutas) # i = (r1,c1) índice de la ruta en la que se encuentra 
            j = self.buscar(mejorAhorro[1],rutas) # igual que i
            IesInterno = self.esInterno(mejorAhorro[0],rutas[i[0]])
            JesInterno = self.esInterno(mejorAhorro[1],rutas[j[0]])
            demCliente = dem[mejorAhorro[1]-1]
            if (len(rutas[i[0]]) == 2 and len(rutas[j[0]]) == 2) or (self.estaEnUnRutaNoVacia(i[0],rutas) and not IesInterno and self.estaEnUnRutaNoVacia(j[0],rutas) and not JesInterno and i[0]!=j[0]):
                carga1 = self.cargaTotal(dem,rutas[i[0]])
                carga2 = self.cargaTotal(dem,rutas[j[0]])
                if(carga1 + carga2 <= capacidadMax):
                    self.mezclarRuta(i[0],j[0],rutas)
                    self.removeRuta(j[0],rutas)
            else: 
                if(self.estaEnUnRutaNoVacia(i[0],rutas) and not self.estaEnUnRutaNoVacia(j[0],rutas) and not IesInterno):
                    demCliente = dem[mejorAhorro[1]-1]
                    cargaRuta = self.cargaTotal(dem,rutas[i[0]])
                    if(cargaRuta+demCliente <= capacidadMax):
                        ind = rutas[i[0]].index(mejorAhorro[0])
                        rutas[i[0]].insert(ind+1,mejorAhorro[1])
                        self.removeRuta(j[0],rutas)
                elif(self.estaEnUnRutaNoVacia(j[0],rutas) and  not self.estaEnUnRutaNoVacia(i[0],rutas) and not JesInterno):
                    demCliente = dem[mejorAhorro[0]-1]
                    cargaRuta = self.cargaTotal(dem,rutas[j[0]])
                    if(cargaRuta+demCliente <= capacidadMax):
                        if(j[1]==1):
                            rutas[j[0]].insert(1,mejorAhorro[0])
                        else:
                            ind = rutas[j[0]].index(mejorAhorro[1])
                            rutas[j[0]].insert(ind+1,mejorAhorro[0])
                        self.removeRuta(i[0],rutas)

        if(len(rutas)!=nroVehiculos):
            if(iteracion == 0):
                _lambda = 0.1 
                mu = 2
                ni = 2 
                # rutas = []
                fact = False
            elif(iteracion < 5):
                _lambda += 0.5
                mu -= 0.1
                ni -= 0.1
                # rutas = []
                fact = False
            else:
                _lambda += 0.1
                mu -= 0.1
                ni -= 0.1
                fact = True
            iteracion +=1
        print("tiempo clarke wright ", time()-t)

        return rutas, _lambda, mu, ni, iteracion, fact

    def swap(self, k_Opt, aristaIni, rutas_orig, indRutas, indAristas):
        rutas = copy.deepcopy(rutas_orig)
        if(k_Opt[0] == 2):
            opcion = k_Opt[1]
            rutas = self.swap_2opt(aristaIni, indRutas, indAristas, rutas, opcion)
        elif(k_Opt[0] == 3):
            opcion = k_Opt[1]
            rutas = self.swap_3opt(aristaIni, indRutas, indAristas, rutas, opcion)
        elif(k_Opt[0] == 4):
            opcion = k_Opt[1]
            rutas = self.swap_4opt(aristaIni, indRutas, indAristas, rutas, opcion)
        elif(k_Opt[0] == 5):
            opcion = k_Opt[1]
            rutas = self.swap_Exchange(aristaIni, indRutas, indAristas, rutas, opcion)

        return rutas

    def getPosiciones(self, V_origen, V_destino, rutas):
        ind_verticeOrigen = -1
        ind_verticeDestino = -1
        ind_rutaOrigen = -1
        ind_rutaDestino = -1
        
        #arista_azar = (3,7)    => V_origen = 3 y V_destino = 7
        #r: 1-2-3-4-5                r2: 1-6-7-8-9-10   
        #  (1,2)(2,3)(3,4)(4,5)(5,1)   (1,6)(6,7)(7,8)(8,9)(9,10)(10,1)
        #ind_VertOrigen = 2     ind_VertDest = 1
        for i in range(0,len(rutas)):
            for j in range(0, len(rutas[i].getV())):
                v = rutas[i].getV()[j]
                if (V_origen == v):
                    ind_verticeOrigen = j
                    ind_rutaOrigen = i
                elif (V_destino == v):
                    ind_verticeDestino = j-1
                    ind_rutaDestino = i
                if (ind_verticeOrigen != -1 and ind_verticeDestino != -1):
                    break
            if (ind_rutaOrigen != -1 and ind_rutaDestino != -1):
                if (ind_rutaOrigen == ind_rutaDestino and ind_verticeOrigen > ind_verticeDestino):
                    ind = ind_verticeOrigen
                    ind_verticeOrigen = ind_verticeDestino + 1
                    ind_verticeDestino = ind - 1
                break
        if(len(rutas)==0):
            print("Error en getPosiciones\n"+str(rutas))

        return [ind_rutaOrigen, ind_rutaDestino],[ind_verticeOrigen, ind_verticeDestino]

    def __deepcopy__(self,memo):
        aux = copy.copy(self)
        aux._A = copy.copy(self._A)
        aux._V = copy.copy(self._V)
        return aux

    def evaluarOpt(self, lista_permitidos, ind_permitidos, ind_random, rutas, condEstancamiento):
        kOpt = 0            #2, 3 o 4-opt
        tipo_kOpt = 0       #Las variantes de cada opt's anteriores
        costoSolucion = float("inf")
        nuevoCosto = float("inf")
        indRutas = indAristas = []
        DROP_2opt = DROP_3opt = DROP_4opt = []
        indDROP_2opt = indDROP_3opt = indDROP_4opt = []
        ADD = DROP = []
        indDROP = indADD = []
        
        while(costoSolucion == float("inf") and ind_random!=[]):
            ind = ind_random[-1]
            ind_random = ind_random[:-1]
            aristaIni = lista_permitidos[ind_permitidos[ind]]
            aristaIniOrig = copy.deepcopy(aristaIni)
            V_origen = aristaIni.getOrigen()
            V_destino = aristaIni.getDestino()
            ADD = []
            ADD.append(aristaIniOrig)
            indADD = []
            indADD.append(aristaIni.getId())
            
            indRutas, indAristas = self.getPosiciones(V_origen, V_destino, rutas)
            
            indR = [indRutas[0], indRutas[1]]
            indA = [indAristas[0], indAristas[1]]
            nuevoCosto, tipo_2opt, DROP_2opt, indDROP_2opt = self.evaluar_2opt(aristaIni, indR, indA, rutas)
            if(nuevoCosto < costoSolucion):
                costoSolucion = nuevoCosto
                kOpt = 2
                tipo_kOpt = tipo_2opt
                DROP = DROP_2opt
                indDROP = indDROP_2opt
            
            indR = [indRutas[0], indRutas[1]]
            indA = [indAristas[0], indAristas[1]]
            nuevoCosto, tipo_3opt, DROP_3opt, indDROP_3opt = self.evaluar_3opt(aristaIni, indR, indA, rutas)
            if(nuevoCosto < costoSolucion or (condEstancamiento and nuevoCosto!=float("inf")) ):
                costoSolucion = nuevoCosto
                kOpt = 3
                tipo_kOpt = tipo_3opt
                DROP = DROP_3opt
                indDROP = indDROP_3opt 
                
            indR = [indRutas[0], indRutas[1]]
            indA = [indAristas[0], indAristas[1]]
            nuevoCosto, tipo_4opt, DROP_4opt, indDROP_4opt = self.evaluar_4opt(aristaIni, indR, indA, rutas)
            if(nuevoCosto < costoSolucion or (condEstancamiento and nuevoCosto!=float("inf")) ):
                costoSolucion = nuevoCosto
                kOpt = 4
                tipo_kOpt = tipo_4opt
                DROP = DROP_4opt
                indDROP = indDROP_4opt
            
            indR = [indRutas[0], indRutas[1]]
            indA = [indAristas[0], indAristas[1]]
            nuevoCosto, tipo_exch, DROP_exch, indDROP_exch  = self.evaluar_Exchange(aristaIni, indR, indA, rutas)
            if(nuevoCosto < costoSolucion or (condEstancamiento and nuevoCosto!=float("inf")) ):
                costoSolucion = nuevoCosto
                kOpt = 5
                tipo_kOpt = tipo_exch
                DROP = DROP_exch
                indDROP = indDROP_exch
                #ADD = ADD_exch
                #indADD = indADD_exch

        if(costoSolucion != float("inf")):
            index = [i for i in range(0,len(ind_permitidos)) if ind_permitidos[i] in indDROP or ind_permitidos[i] in indADD]
            ind_permitidos = np.delete(ind_permitidos, index)
        else:
            costoSolucion = self.getCostoAsociado()
            ADD = DROP = []
        
        return costoSolucion, [kOpt, tipo_kOpt], indRutas, indAristas, ADD, DROP, ind_permitidos
    
    def evaluar_2opt(self, aristaIni, ind_rutas, ind_A, rutas):
        opcion = 0
        costo_solucion = float("inf")
        costo_r_add1 = aristaIni.getPeso()
        
        DROP = []
        index_DROP = []

        if(ind_rutas[0]!=ind_rutas[1]):
            r1 = rutas[ind_rutas[0]]
            r2 = rutas[ind_rutas[1]]
            A_r1 = r1.getA()
            A_r2 = r2.getA()
            
            for i in range(1,3):
                if(len(r1.getV())-1 == ind_A[0] or len(r2.getV())-1 == ind_A[1]+1):
                    continue

                if(i==2):
                    #print("2da opcion")            
                    r1 = rutas[ind_rutas[1]]
                    r2 = rutas[ind_rutas[0]]
                    a = copy.copy(A_r1)
                    A_r1 = A_r2
                    A_r2 = a
                    j = ind_A[0]
                    ind_A[0] = ind_A[1] +1          #=> La posicion de 'a' es en donde la arista tiene como origen 'a' (+1)
                    ind_A[1] = j -1             	#=> La posicion de 'b' es en donde la arista tiene como destino 'b'(-1)
                
                    A_r1_right = A_r1[ind_A[0]+1:]
                    A_r2_left = A_r2[:ind_A[1]]
                    
                    #Caso no factible por ej:
                    #r1: 1-2-3-4-5-a    r2: 1-b-6-7-8-9-10  -> Sol: r1: 1-2-3-4-5-a-b-6-7-8-9-10    r2: 1
                    if(A_r1_right==[] and A_r2_left==[] and opcion == 1):
                        continue
                    
                    r1DemandaAcumulada = r1.getDemandaAcumulada()
                    r2DemandaAcumulada = r2.getDemandaAcumulada()
                    
                    cap_r1_left = r1DemandaAcumulada[ind_A[0]]
                    cap_r1_right = r1DemandaAcumulada[-1] - cap_r1_left
                    
                    cap_r2_left = r2DemandaAcumulada[ind_A[1]]
                    cap_r2_right = r2DemandaAcumulada[-1] - cap_r2_left
                    
                    cap_r1 = cap_r1_left + cap_r2_right
                    cap_r2 = cap_r2_left + cap_r1_right
                    
                    if(cap_r1 > self.__capacidadMax or cap_r2 > self.__capacidadMax):
                        continue
                    
                    A_r1_drop = A_r1[ind_A[0]]
                    A_r2_drop = A_r2[ind_A[1]]
                    
                    if(A_r2_left!=[]):
                        V_origen = A_r2_left[-1].getDestino()
                    #vertice 'a' de la arista (a,b) se encuentra al principio
                    else:
                        V_origen = Vertice(1,0)
                    
                    #vertice 'b' de la arista (a,b) no se encuentra al final
                    if(A_r1_right!=[]):
                        V_destino = A_r1_right[0].getOrigen()
                    #vertice 'b' de la arista (a,b) no se encuentra al final
                    else:
                        V_destino = Vertice(1,0)
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r2_add = Arista(V_origen,V_destino, peso)   # => (6,4, peso)
                    #print("A_r2_add"+str(A_r2_add))
                    costo_r2_add = peso
                    A_r2_add.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                else:
                    A_r1_right = A_r1[ind_A[0]+1:]
                    A_r2_left = A_r2[:ind_A[1]]

                    A_r1_drop = A_r1[ind_A[0]]
                    A_r2_drop = A_r2[ind_A[1]]

                    #Caso no factible por ej:
                    #r1: 1-2-3-4-5-a    r2: 1-b-6-7-8-9-10  -> Sol: r1: 1-2-3-4-5-a-b-6-7-8-9-10    r2: 1
                    if(A_r1_right==[] and A_r2_left==[] and opcion == 1):
                        continue
                    
                    r1DemandaAcumulada = r1.getDemandaAcumulada()
                    r2DemandaAcumulada = r2.getDemandaAcumulada()
                    
                    cap_r1_left = r1DemandaAcumulada[ind_A[0]]
                    cap_r1_right = r1DemandaAcumulada[-1] - cap_r1_left
                    
                    cap_r2_left = r2DemandaAcumulada[ind_A[1]]
                    cap_r2_right = r2DemandaAcumulada[-1] - cap_r2_left
                    
                    cap_r1 = cap_r1_left + cap_r2_right
                    cap_r2 = cap_r2_left + cap_r1_right
                    
                    if(cap_r1 > self.__capacidadMax or cap_r2 > self.__capacidadMax):
                        continue
                                        
                    if(A_r2_left!=[]):
                        V_origen = A_r2_left[-1].getDestino()
                    #vertice 'a' de la arista (a,b) se encuentra al principio
                    else:
                        V_origen = Vertice(1,0)
                    
                    #vertice 'b' de la arista (a,b) no se encuentra al final
                    if(A_r1_right!=[]):
                        V_destino = A_r1_right[0].getOrigen()
                    #vertice 'b' de la arista (a,b) no se encuentra al final
                    else:
                        V_destino = Vertice(1,0)
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r2_add = Arista(V_origen,V_destino, peso)   # => (6,4, peso)
                    #print("A_r2_add"+str(A_r2_add))
                    costo_r2_add = peso
                    A_r2_add.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                                        
                costo_r1_drop = A_r1_drop.getPeso()
                costo_r2_drop = A_r2_drop.getPeso()

                nuevo_costo = self.getCostoAsociado() + costo_r_add1 + costo_r2_add - costo_r1_drop - costo_r2_drop
                
                if(nuevo_costo < costo_solucion):
                    costo_solucion = nuevo_costo
                    opcion = i
                    DROP = []
                    DROP.append(A_r1_drop)
                    DROP.append(A_r2_drop)
                    index_DROP = []
                    index_DROP.append(A_r1_drop.getId())
                    index_DROP.append(A_r2_drop.getId())
                    # ADD = []
                    # ADD.append(A_r2_add)
                    # index_ADD = []
                    # index_ADD.append(A_r2_add.getId())
        else:
            #En la misma ruta hay factibilidad, por lo tanto se calcula unicamente el costo
            r = rutas[ind_rutas[0]]
            V_r = r.getV()
            V_r.append(Vertice(1,0))
            A_r = r.getA()
            #r: 1,2,a,3,4,b,5,6,1     -> Ruta original
            #Sol:
            #r: 1,2,a,b,4,3,5,6,1     -> 1ra opcion
            #r: 1,2,4,3,a,b,5,6,1     -> 2da opcion
            #r: 1,6,5,b,a,3,4,2,1     -> 2da opcion
            for i in range(1,3):
                if(i==2):
                    if(0 in ind_A):
                        # a = 1
                        #r: a,2,3,4,5,b,6,1     -> Ruta original
                        #r: a,b,5,4,3,2,6,1     -> 1ra opcion        
                        #r: 1,6,b,5,4,3,2,a     -> Ruta original invertida
                        #r: 1,6,b,a,2,3,4,5     -> 2da opcion. No se puede xq a = 1        
                        # a o b no pueden ser igual a 1 para la segunda opcion
                        continue
                    
                    A_r_drop1 = A_r[ind_A[0]-1]
                    costo_r_drop1 = A_r_drop1.getPeso()
                    A_r_drop2 = A_r[ind_A[1]]
                    costo_r_drop2 = A_r_drop2.getPeso()
                    
                    V_origen = A_r_drop1.getOrigen()
                    V_destino = A_r_drop2.getOrigen()
                    costo_r_add2 = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]

                else:
                    A_r_drop1 = A_r[ind_A[0]]
                    costo_r_drop1 = A_r_drop1.getPeso()
                    A_r_drop2 = A_r[ind_A[1]+1]
                    costo_r_drop2 = A_r_drop2.getPeso()
                    try:
                        V_origen = V_r[ind_A[0]+1]
                    except:
                        print("Arista ini: "+str(aristaIni))
                        for i in range(0, len(rutas)):
                            x = rutas[i]
                            print("ruta #%d: %s" %(i, str(x.getV())))
                        print("ind_A: "+str(ind_A))
                        a = 1/0
                    V_destino = V_r[ind_A[1]+2]
                    costo_r_add2 = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    
                nuevo_costo = self.getCostoAsociado() + costo_r_add1 + costo_r_add2 - costo_r_drop1 - costo_r_drop2
                
                if(nuevo_costo < costo_solucion):
                    costo_solucion = nuevo_costo
                    opcion = i*(-1)
                    DROP = []
                    DROP.append(A_r_drop1)
                    DROP.append(A_r_drop2)
                    index_DROP = []
                    index_DROP.append(A_r_drop1.getId())
                    index_DROP.append(A_r_drop2.getId())
            
            V_r = V_r[:-1]
            r.setV(V_r)
            
        return costo_solucion, opcion, DROP, index_DROP

    def swap_2opt(self, arista_ini, ind_rutas, ind_A, rutas, opcion):    
        """
        2-opt:
        new_cost = costoSolucion + costo(a,b) + costo(8,4) - costo(a,4) - costo(8,b)
        r1: 1-2-3-a-4-5         r2: 1-6-7-b-8-9-10   -> ruta original
        resultado:
        r1: 1-2-3-a-b-8-9-10    r2: 1-6-7-4-5        -> 1ra opcion
        r1: 1-2-3-8-9-10        r2: 1-6-7-b-a-4-5    -> 2da opcion
        
        r: 1,2,a,3,4,b,5,6     -> ruta original 
        resultado:
        r: 1,2,a,b,4,3,5,6     -> 1ra opcion
        r: 1,2,4,3,a,b,5,6     -> 2da opcion
        """
        costoSolucion = self.getCostoAsociado()
        ADD = []
        DROP = []
        ADD.append(arista_ini)

        #En distintas rutas(opcion = 0 -> 1ra opcion sino 2da opcion)
        if(opcion==1 or opcion==2):
            r1 = rutas[ind_rutas[0]]
            r2 = rutas[ind_rutas[1]]
            A_r1 = r1.getA()
            A_r2 = r2.getA()
            if(opcion==1):
                A_r1_left = A_r1[:ind_A[0]]
                A_r1_right = A_r1[ind_A[0]+1:]
                A_r1_drop = A_r1[ind_A[0]]
                        
                A_r2_left = A_r2[:ind_A[1]]
                A_r2_right = A_r2[ind_A[1]+1:]                
                A_r2_drop = A_r2[ind_A[1]]

                if(A_r2_left!=[]):
                    V_origen = A_r2_left[-1].getDestino()
                #vertice 'a' de la arista (a,b) se encuentra al principio
                else:
                    V_origen = Vertice(1,0)    

                #vertice 'b' de la arista (a,b) no se encuentra al final
                if(A_r1_right!=[]):
                    V_destino = A_r1_right[0].getOrigen()
                #vertice 'b' de la arista (a,b) no se encuentra al final
                else:
                    V_destino = Vertice(1,0)
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r_add = Arista(V_origen,V_destino, peso)   # => (6,4, peso)
                #print("A_r2_add"+str(A_r2_add))
                A_r_add.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))

                ADD = []
                ADD.append(arista_ini)                

                if(A_r1_left!=[] and A_r1_left[-1].getDestino()!=arista_ini.getOrigen()):
                    arista_ini.invertir()
                
                A_r1_left.append(arista_ini)
                A_r1_left.extend(A_r2_right)
                A_r2_left.append(A_r_add)
                A_r2_left.extend(A_r1_right)
            else:
                A_r1_left = A_r1[:ind_A[0]-1]
                A_r1_right = A_r1[ind_A[0]:]
                A_r1_drop = A_r1[ind_A[0]-1]
                  
                A_r2_left = A_r2[:ind_A[1]+1]
                A_r2_right = A_r2[ind_A[1]+2:]                
                A_r2_drop = A_r2[ind_A[1]+1]

                if(arista_ini.getDestino() == A_r1_drop.getDestino()):
                    arista_ini.invertir()
                
                if(A_r1_left!=[]):
                    V_origen = A_r1_left[-1].getDestino()
                #En caso de que la arista al azar se encuentra al principio
                else:
                    V_origen = Vertice(1,0)
                
                if(A_r2_right!=[]):
                    V_destino = A_r2_right[0].getOrigen()
                #En caso de que la arista al azar se encuentra al final
                else:
                    V_destino = Vertice(1,0)
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r_add = Arista(V_origen,V_destino, peso)   # => (6,4, peso)
                A_r_add.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))

                if(A_r_add.getDestino() != arista_ini.getOrigen()):
                    arista_ini.invertir()
                
                A_r1_left.append(A_r_add)
                #print("A_r1_left: "+str(A_r1_left))
                A_r1_left.extend(A_r2_right)
                #print("A_r1_left: "+str(A_r1_left))
                A_r2_left.append(arista_ini)
                #print("A_r2_left: "+str(A_r2_left))
                A_r2_left.extend(A_r1_right)
                #print("A_r2_left: "+str(A_r2_left))
        
            costoSolucion -= r1.getCostoAsociado() + r2.getCostoAsociado()

            # ADD = []
            # ADD.append(arista_ini)
            # ADD.append(A_r_add)
            # DROP.append(A_r1_drop)
            # DROP.append(A_r2_drop)

            cap_r1 = r1.cargarDesdeAristas(A_r1_left)
            cap_r2 = r2.cargarDesdeAristas(A_r2_left)
            r1.setCapacidad(cap_r1)
            r2.setCapacidad(cap_r2)

            costoSolucion += r1.getCostoAsociado() + r2.getCostoAsociado()
        #En la misma ruta
        else:
            r = rutas[ind_rutas[0]]
            costoSolucion -= r.getCostoAsociado()
            V_r = r.getV()
            V_r.append(Vertice(1,0))
            
            if(opcion == -2):
                V_r = V_r[::-1]
                lenV = len(V_r) - 2
                ind_b = lenV - ind_A[1]
                ind_a = lenV - ind_A[0]
                ind_A = [ind_b, ind_a]
                ADD = []
                arista_ini.invertir()
                ADD.append(arista_ini)
            
            V_r_left = V_r[:ind_A[0]+1]
            V_r_middle = V_r[ind_A[0]+1:ind_A[1]+1]
            V_r_middle = V_r_middle[::-1]
            V_r_right = V_r[ind_A[1]+2:]
        
            try:
                A_r_drop1 = r.getA()[ind_A[0]]
                A_r_drop2 = r.getA()[ind_A[1]+1]
            except IndexError:
                print("r: "+str(r.getA()))
                print("aristaIni: "+str(arista_ini))
                print("ind_A: "+str(ind_A))
                a = 1/0
            V_origen = V_r_middle[-1]
            V_destino = V_r_right[0]
            peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
            A_r_add = Arista(V_origen,V_destino, peso)
            A_r_add.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))

            ADD.append(A_r_add)              
            DROP.append(A_r_drop1)
            DROP.append(A_r_drop2)
            
            V_r_left.append(V_r[ind_A[1]+1])
            V_r_left.extend(V_r_middle)
            V_r_left.extend(V_r_right)
            V_r = V_r_left[:-1]
            
            cap = r.cargarDesdeSecuenciaDeVertices(V_r)
            r.setCapacidad(cap)
            costoSolucion += r.getCostoAsociado()
        
        return rutas
    
    def evaluar_3opt(self, aristaIni, ind_rutas, ind_A, rutas):
        """
        3-opt: (a,b)
        r1: 1,2,3,a,4,5,6          r2: 1,7,8,b,9,10,11,12 -> ruta original
        r1: 1,2,3,a,b,4,5,6        r2: 1,7,8,9,10,11,12       -> 1ra opcion
        r1: 1,2,3,b,a,4,5,6        r2: 1,7,8,9,10,11,12       -> 2da opcion
        r1: 1,2,3,4,5,6            r2: 1,7,8,a,b,9,10,11,12   -> 3ra opcion
        r1: 1,2,3,4,5,6            r2: 1,7,8,b,a,9,10,11,12   -> 4ta opcion
        
        r: 1,2,a,3,4,5,b,6,7,8      -> ruta original 
        r: 1,2,a,b,3,4,5,6,7,8      -> 1ra opcion
        r: 1,2,b,a,3,4,5,6,7,8      -> 2da opcion
        r: 1,2,3,4,5,b,a,6,7,8      -> 3ra opcion
        r: 1,2,3,4,5,a,b,6,7,8      -> 4ta opcion
        """

        sol_factible_12 = sol_factible_34 = False
        #Opcion: 0 (1ra opcion) | 1 (2da opcion) | 3 (3ra opcion) | 4 (4ta opcion)
        #Misma ruta: -1(1ra opcion) | -2 (2da opcion) | -3 (3ra opcion) | -4 (4ta opcion)
        opcion = 0  
        costo_solucion = float("inf")
        costo_r_add1 = aristaIni.getPeso()

        DROP = []
        index_DROP = []

        #3-opt Distintas rutas
        if(ind_rutas[0]!=ind_rutas[1]):
            r1 = rutas[ind_rutas[0]]
            r2 = rutas[ind_rutas[1]]

            #Evaluar la factibilidad en las distintas opciones
            cap_r1 = r1.getCapacidad() + aristaIni.getDestino().getDemanda()
            if(cap_r1 <= self.__capacidadMax):
                sol_factible_12 = True
            #else:
            #    print("Sol no factible. 3-opt 1ra y 2da opcion")
            
            cap_r2 = r2.getCapacidad() + aristaIni.getOrigen().getDemanda()
            if(cap_r2 <= self.__capacidadMax):
                sol_factible_34 = True
            # else:
            #     print("Sol no factible. 3-opt 3ra y 4ta opcion")
            
            # r1: 1,2,3,a,4,5,6            r2: 1,7,8,b,9,10,11,12
            # r1: 1,2,3,4,5,6              r2: 1,7,8,a,b,9,10,11,12   -> 3ra opcion
            # r1: 1,2,3,4,5,6              r2: 1,7,8,b,a,9,10,11,12   -> 4ta opcion    
            if(sol_factible_34):
                #print("\nsol factible por 3-opt 3ra y 4ta opcion")
                #A_r1_left = r1.getA()[:ind_A[0]-1]
                A_r1_right = r1.getA()[ind_A[0]+1:]
                #print("A_r1_left: "+str(A_r1_left))
                #print("A_r1_r: "+str(A_r1_right))
                
                #A_r2_left = r2.getA()[:ind_A[1]]
                A_r2_right = r2.getA()[ind_A[1]+1:]
                #print("A_r2_left: "+str(A_r2_left))
                #print("A_r2_right: "+str(A_r2_right)+"\n")
                for i in range(3,5):
                    if(i==4 and A_r2_right == []):
                        #print("4ta opcion no es posible")
                        continue
                    #Obtengo las aristas que se eliminan y las que se añaden
                    #DROP
                    A_r1_drop1 = r1.getA()[ind_A[0]-1]
                    costo_r1_drop1 = A_r1_drop1.getPeso()
                    
                    A_r1_drop2 = r1.getA()[ind_A[0]]
                    costo_r1_drop2 = A_r1_drop2.getPeso()
                    
                    #ADD
                    V_origen = r1.getA()[ind_A[0]-1].getOrigen()
                    V_destino = r1.getA()[ind_A[0]].getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    #A_r1_add = Arista(V_origen, V_destino, peso)
                    #print("A_r1_add: "+str(A_r1_add))
                    costo_r1_add = peso

                    if(i==3):
                        A_r2_drop = r2.getA()[ind_A[1]]
                        costo_r2_drop = A_r2_drop.getPeso()
                    
                        V_origen = r2.getA()[ind_A[1]].getOrigen()
                        V_destino = r1.getA()[ind_A[0]-1].getDestino()
                        peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                        #A_r2_add = Arista(V_origen, V_destino, peso)
                        #A_r2_add.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                        #print("A_r2_add: "+str(A_r2_add))
                        costo_r2_add = peso
                    else:
                        A_r2_drop = r2.getA()[ind_A[1]+1]
                        costo_r2_drop = A_r2_drop.getPeso()
                    
                        V_origen = r1.getA()[ind_A[0]-1].getDestino()
                        V_destino = r2.getA()[ind_A[1]+1].getDestino()
                        peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                        #A_r2_add = Arista(V_origen, V_destino, peso)
                        #print("A_r2_add: "+str(A_r2_add))
                        costo_r2_add = peso

                    nuevo_costo = self.getCostoAsociado() + costo_r_add1 + costo_r1_add + costo_r2_add - costo_r1_drop1 - costo_r1_drop2 - costo_r2_drop
                    #print("Nuevo costo: ", nuevo_costo)
                
                    if(nuevo_costo < costo_solucion):
                        costo_solucion = nuevo_costo
                        opcion = i
                        DROP = []
                        index_DROP = []
                        DROP.append(A_r1_drop1)
                        DROP.append(A_r1_drop2)
                        DROP.append(A_r2_drop)
                        index_DROP.append(A_r1_drop1.getId())
                        index_DROP.append(A_r1_drop2.getId())
                        index_DROP.append(A_r2_drop.getId())
                        #print("DROP: "+str(DROP))

            #r1: 1,2,3,a,4,5,6            r2: 1,7,8,b,9,10,11,12
            #r1: 1,2,3,b,a,4,5,6          r2: 1,7,8,9,10,11,12   -> 1ra opcion    
            #r1: 1,2,3,a,b,4,5,6          r2: 1,7,8,9,10,11,12   -> 2da opcion
            if(sol_factible_12):
                r1 = rutas[ind_rutas[1]]
                r2 = rutas[ind_rutas[0]]
                A_r1 = r1.getA()
                if(len(A_r1)<3):
                    #print("Sol no factible. No se cuenta con suficiente aristas para realizar el swap")
                    return costo_solucion, opcion, DROP, index_DROP        
                #print("Sol factible. 3-opt 1ra y 2da opcion")
                A_r2 = r2.getA()

                i = ind_A[0]
                ind_A[0] = ind_A[1] + 1
                ind_A[1] = i - 1
                #A_r1_left = A_r1[:ind_A[0]-1]
                A_r1_right = A_r1[ind_A[0]+1:]
                #print("A_r1_left: "+str(A_r1_left))
                #print("A_r1_r: "+str(A_r1_right))
                
                #A_r2_left = A_r2[:ind_A[1]]
                A_r2_right = A_r2[ind_A[1]+1:]
                #print("A_r2_left: "+str(A_r2_left))
                #print("A_r2_right: "+str(A_r2_right)+"\n")
                
                for i in range(1,3):
                    if(i==2 and A_r1_right == []):
                        #print("2da opcion no es posible")
                        continue
                    
                    #Obtengo las aristas que se eliminan y las que se añaden
                    #DROP
                    A_r1_drop1 = r1.getA()[ind_A[0]-1]
                    costo_r1_drop1 = A_r1_drop1.getPeso()
                    
                    A_r1_drop2 = r1.getA()[ind_A[0]]
                    costo_r1_drop2 = A_r1_drop2.getPeso()
                    
                    #ADD
                    V_origen = r1.getA()[ind_A[0]-1].getOrigen()
                    V_destino = r1.getA()[ind_A[0]].getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    #A_r1_add = Arista(V_origen, V_destino, peso)
                    #print("A_r1_add: "+str(A_r1_add))
                    costo_r1_add = peso

                    if(i==1):
                        A_r2_drop = A_r2[ind_A[1]]
                        costo_r2_drop = A_r2_drop.getPeso()
                    
                        V_origen = A_r2[ind_A[1]].getOrigen()
                        V_destino = r1.getA()[ind_A[0]-1].getDestino()
                        peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                        #A_r2_add = Arista(V_origen, V_destino, peso)
                        #print("A_r2_add: "+str(A_r2_add))
                        #A_r2_add.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                        costo_r2_add = peso
                    else:
                        A_r2_drop = A_r2[ind_A[1]+1]
                        costo_r2_drop = A_r2_drop.getPeso()
                    
                        V_origen = r1.getA()[ind_A[0]-1].getDestino()
                        V_destino = A_r2[ind_A[1]+1].getDestino()
                        peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                        #A_r2_add = Arista(V_origen, V_destino, peso)
                        #print("A_r2_add: "+str(A_r2_add))
                        costo_r2_add = peso

                    nuevo_costo = self.getCostoAsociado() + costo_r_add1 + costo_r1_add + costo_r2_add - costo_r1_drop1 - costo_r1_drop2 - costo_r2_drop
                    #print("Nuevo costo: ", nuevo_costo)
                    if(nuevo_costo < costo_solucion):
                        costo_solucion = nuevo_costo
                        opcion = i
                        DROP = []
                        index_DROP = []
                        DROP.append(A_r1_drop1)
                        DROP.append(A_r1_drop2)
                        DROP.append(A_r2_drop)
                        index_DROP.append(A_r1_drop1.getId())
                        index_DROP.append(A_r1_drop2.getId())
                        index_DROP.append(A_r2_drop.getId())
                        #print("DROP: "+str(DROP))

        #3-opt en la misma ruta
        else:
            # r: 1,2,a,3,4,5,b,6,7,8      -> ruta original 
            # resultado:
            # r: 1,2,a,b,3,4,5,6,7,8      -> 1ra opcion
            # r: 1,2,b,a,3,4,5,6,7,8      -> 2da opcion
            # r: 1,2,3,4,5,a,b,6,7,8      -> 3ra opcion
            # r: 1,2,3,4,5,b,a,6,7,8      -> 4ta opcion
            #print("\nPor la misma ruta")
            r = rutas[ind_rutas[0]]
            V_r = r.getV()
            V_r_middle = V_r[ind_A[0]+1:ind_A[1]+1]
            if(len(V_r_middle)<=1):                    #r: 1,2,a,3,b,4   Solo se aplica 2-opt y ya la aplicamos anteriormente
                return float("inf"), opcion, DROP, index_DROP        
            else:
                V_r.append(Vertice(1,0))
            
            V_r_left = V_r[:ind_A[0]+1]
            V_r_right = V_r[ind_A[1]+2:]
            # print("ind_A: "+str(ind_A))
            # print("V_r_r: "+str(V_r_right))
            # print("V_r_m: "+str(V_r_middle))
            # print("V_r_l: "+str(V_r_left))
            
            for ind in range(2):
                if(ind==1):
                    #print("\n3ra y 4ta opcion")
                    if(0 in ind_A):
                        continue
                    ind_A[0] = ind_A[0]-1
                    ind_A[1] = ind_A[1]+1
                    V_r_left = V_r[:ind_A[0]+1]
                #else:
                    #print("\n1ra y 2da opcion")
                
                if(ind == 0):
                    A_r_drop2 = r.getA()[ind_A[1]+1]
                    A_r_drop3 = r.getA()[ind_A[1]]
                    V_origen = V_r_middle[-1]
                    V_destino = V_r_right[0]
                else:
                    A_r_drop2 = r.getA()[ind_A[0]+1]
                    A_r_drop3 = r.getA()[ind_A[0]]
                    V_destino = V_r_middle[0]
                    V_origen = V_r_left[-1]
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r_add2 = Arista(V_origen,V_destino, peso)
                A_r_add2.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                
                costo_r_add2 = peso
                costo_r_drop2 = A_r_drop2.getPeso()
                costo_r_drop3 = A_r_drop3.getPeso()
                
                if(ind == 0):
                    for i in range(1,3):
                        if(i==1):
                            A_r_drop1 = r.getA()[ind_A[0]]
                            costo_r_drop1 = A_r_drop1.getPeso()
                            
                            V_origen = V_r[ind_A[1]+1]
                            V_destino = V_r_middle[0]
                            peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                            A_r_add3 = Arista(V_origen,V_destino, peso)
                            A_r_add3.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                            costo_r_add3 = peso
                            #print("A_r_add2: "+str(A_r_add2))
                            #print("A_r_add3: "+str(A_r_add3))
                        elif(i==2 and 0 not in ind_A):
                            A_r_drop1 = r.getA()[ind_A[0]-1]
                            costo_r_drop1 = A_r_drop1.getPeso()
                            
                            V_origen = V_r[ind_A[0]-1]
                            V_destino = V_r[ind_A[1]+1]
                            peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                            A_r_add3 = Arista(V_origen,V_destino, peso)
                            A_r_add3.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                            costo_r_add3 = peso                    
                            #print("A_r_add2: "+str(A_r_add2))
                            #print("A_r_add3: "+str(A_r_add3))
                        nuevo_costo = self.getCostoAsociado() + costo_r_add1 + costo_r_add2 + costo_r_add3 - costo_r_drop1 - costo_r_drop2 - costo_r_drop3
                        #print("Costo anterior: ", self.getCostoAsociado())
                        #print("Nuevo costo: ", nuevo_costo)
                        if(nuevo_costo < costo_solucion):
                            costo_solucion = nuevo_costo
                            opcion = (-1)*i - 2*ind
                            DROP = []
                            index_DROP = []
                            DROP.append(A_r_drop1)
                            DROP.append(A_r_drop2)
                            DROP.append(A_r_drop3)
                            index_DROP.append(A_r_drop1.getId())
                            index_DROP.append(A_r_drop2.getId())
                            index_DROP.append(A_r_drop3.getId())
                            #print("DROP: "+str(DROP))
                elif(ind == 1):
                    for i in range(1,3):
                        if(i==1):
                            A_r_drop1 = r.getA()[ind_A[1]]
                            costo_r_drop1 = A_r_drop1.getPeso()
                            
                            V_origen = V_r[ind_A[0]+1]
                            V_destino = V_r[ind_A[1]+1]
                            peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                            A_r_add3 = Arista(V_origen,V_destino, peso)
                            A_r_add3.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                            costo_r_add3 = peso
                            #print("A_r_add2: "+str(A_r_add2))
                            #print("A_r_add3: "+str(A_r_add3))
                        else:
                            A_r_drop1 = r.getA()[ind_A[1]-1]
                            costo_r_drop1 = A_r_drop1.getPeso()
                            
                            V_destino = V_r[ind_A[0]+1]
                            V_origen = V_r[ind_A[1]-1]
                            peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                            A_r_add3 = Arista(V_origen,V_destino, peso)
                            A_r_add3.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                            costo_r_add3 = peso                    
                            #print("A_r_add2: "+str(A_r_add2))
                            #print("A_r_add3: "+str(A_r_add3))
                        nuevo_costo = self.getCostoAsociado() + costo_r_add1 + costo_r_add2 + costo_r_add3 - costo_r_drop1 - costo_r_drop2 - costo_r_drop3
                        #print("Costo anterior: ", self.getCostoAsociado())
                        #print("Nuevo costo: ", nuevo_costo)
                        if(nuevo_costo < costo_solucion):
                            costo_solucion = nuevo_costo
                            opcion = (-1)*i - 2*ind
                            DROP = []
                            index_DROP = []
                            DROP.append(A_r_drop1)
                            DROP.append(A_r_drop2)
                            DROP.append(A_r_drop3)
                            index_DROP.append(A_r_drop1.getId())
                            index_DROP.append(A_r_drop2.getId())
                            index_DROP.append(A_r_drop3.getId())
                            #print("DROP: "+str(DROP))        
            V_r = r.getV()
            V_r = V_r[:-1]
            r.setV(V_r)
        
        return costo_solucion, opcion, DROP, index_DROP
        
    def swap_3opt(self, arista_ini, ind_rutas, ind_A, rutas, opcion):
        costoSolucion = self.getCostoAsociado()
        
        if(opcion > 0):
            # r1: 1,2,3,a,4,5,6            r2: 1,7,8,b,9,10,11,12
            if(opcion == 3 or opcion == 4):
                # r1: 1,2,3,4,5,6              r2: 1,7,8,b,a,9,10,11,12   -> 3ra opcion
                # r1: 1,2,3,4,5,6              r2: 1,7,8,a,b,9,10,11,12   -> 4ta opcion
                r1 = rutas[ind_rutas[0]]
                r2 = rutas[ind_rutas[1]]
                #print("\nsol factible por 3-opt 3ra y 4ta opcion")
                A_r1_left = r1.getA()[:ind_A[0]-1]
                A_r1_right = r1.getA()[ind_A[0]+1:]
            else:
                #r1: 1,2,3,b,a,4,5,6          r2: 1,7,8,9,10,11,12       -> 1ra opcion
                #r1: 1,2,3,a,b,4,5,6          r2: 1,7,8,9,10,11,12       -> 2da opcion
                #print("\nsol factible por 3-opt 1ra y 2da opcion")
                r1 = rutas[ind_rutas[1]]
                r2 = rutas[ind_rutas[0]]
                i = ind_A[0]
                ind_A[0] = ind_A[1] + 1
                ind_A[1] = i - 1
                A_r1_left = r1.getA()[:ind_A[0]-1]
                A_r1_right = r1.getA()[ind_A[0]+1:]
            costoSolucion -= r1.getCostoAsociado() + r2.getCostoAsociado()

            #print("A_r1_left: "+str(A_r1_left))
            #print("A_r1_right: "+str(A_r1_right))
            
            #ADD
            V_origen = r1.getA()[ind_A[0]-1].getOrigen()
            V_destino = r1.getA()[ind_A[0]].getDestino()
            peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
            A_r1_add = Arista(V_origen, V_destino, peso, len(self._matrizDistancias))
            
            #print("A_r1_add: "+str(A_r1_add))
            #costo_r1_add = peso

            if(opcion == 3 or opcion == 1):
                #print("Opcion 1 o 3")
                A_r2_left = r2.getA()[:ind_A[1]]
                A_r2_right = r2.getA()[ind_A[1]+1:]
                #print("A_r2_left: "+str(A_r2_left))
                #print("A_r2_right: "+str(A_r2_right))
                V_origen = r2.getA()[ind_A[1]].getOrigen()
                V_destino = r1.getA()[ind_A[0]-1].getDestino()
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r2_add = Arista(V_origen, V_destino, peso)
                A_r2_add.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                #print("A_r2_add: "+str(A_r2_add))
                #costo_r2_add = peso
                A_r2_left.append(A_r2_add)
                if(opcion==1):
                    arista_ini.invertir()
                A_r2_left.append(arista_ini)
            else:
                #print("Opcion 2 o 4")
                A_r2_left = r2.getA()[:ind_A[1]+1]
                A_r2_right = r2.getA()[ind_A[1]+2:]
                #print("A_r2_left: "+str(A_r2_left))
                #print("A_r2_right: "+str(A_r2_right))
                V_origen = r1.getA()[ind_A[0]-1].getDestino()
                V_destino = r2.getA()[ind_A[1]+1].getDestino()
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r2_add = Arista(V_origen, V_destino, peso)
                A_r2_add.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                #print("A_r2_add: "+str(A_r2_add))
                #costo_r2_add = peso
                if(opcion==4):
                    arista_ini.invertir()
                A_r2_left.append(arista_ini)
                A_r2_left.append(A_r2_add)
            A_r2_left.extend(A_r2_right)
            #print("A_r2: "+str(A_r2_left))            
            
            A_r1_left.append(A_r1_add)
            A_r1_left.extend(A_r1_right)
            #print("A_r1: "+str(A_r1_left))            
            #print("A_r2: "+str(A_r2_left))
            cap_r1 = r1.cargarDesdeAristas(A_r1_left)
            cap_r2 = r2.cargarDesdeAristas(A_r2_left)
            r1.setCapacidad(cap_r1)
            r2.setCapacidad(cap_r2)
            costoSolucion += r1.getCostoAsociado() + r2.getCostoAsociado()
            # print("Swap 3-opt")
            # print("cap r1: ",cap_r1)
            # print("r1: "+ str(r1.getV()) + "      -> costo: "+str(r1.getCostoAsociado()))
            # print("cap r2: ",cap_r2)
            # print("r2: "+ str(r2.getV()) + "      -> costo: "+str(r2.getCostoAsociado()))
        #3-opt en la misma ruta
        # r: 1,2,a,3,4,5,b,6,7,8      -> ruta original 
        # resultado:
        # r: 1,2,a,b,3,4,5,6,7,8      -> 1ra opcion
        # r: 1,2,b,a,3,4,5,6,7,8      -> 2da opcion
        # r: 1,2,3,4,5,b,a,6,7,8      -> 3ra opcion
        # r: 1,2,3,4,5,a,b,6,7,8      -> 4ta opcion
        else:
            #print("Misma ruta")
            r = rutas[ind_rutas[0]]
            costoSolucion -= r.getCostoAsociado()
            V_r = r.getV()
            V_r.append(Vertice(1,0))
            V_r_left = V_r[:ind_A[0]]
            V_r_middle = V_r[ind_A[0]+1:ind_A[1]+1]
            V_r_right = V_r[ind_A[1]+2:]
            #print("V_r_r: "+str(V_r_right))
            #print("V_r_m: "+str(V_r_middle))
            #print("V_r_l: "+str(V_r_left))
            
            # if(opcion == -1 or opcion == -2):
            #     #print("1ra opcion")
            #     #print("2da opcion")
            #     V_origen = V_r[ind_A[1]]
            #     V_destino = V_r[ind_A[1]+2]
            # elif(opcion == -3 or opcion == -4):
            #     #print("3ra y 4ta opcion")
            #     V_origen = V_r_left[-1]
            #     V_destino = V_r_middle[0]
            # peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
            # A_r_add2 = Arista(V_origen,V_destino, peso)
            #A_r_add2.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
            
            if(opcion == -1 or opcion == -4):
                V_origen = V_r[ind_A[0]]
                V_destino = V_r[ind_A[1]+1]
            elif(opcion == -2 or opcion == -3):
                V_origen = V_r[ind_A[1]+1]
                V_destino = V_r[ind_A[0]]
            peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
            A_r_add1 = Arista(V_origen,V_destino, peso)
            A_r_add1.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))               
            #print("A_r_add1: "+str(A_r_add1))
            #print("A_r_add2: "+str(A_r_add2))
            
            if(opcion == -1 or opcion == -2):
                V_r_left.append(A_r_add1.getOrigen())
                V_r_left.append(A_r_add1.getDestino())
                V_r_left.extend(V_r_middle)
                V_r_left.extend(V_r_right)
            else:
                V_r_left.extend(V_r_middle)
                V_r_left.append(A_r_add1.getOrigen())
                V_r_left.append(A_r_add1.getDestino())
                V_r_left.extend(V_r_right)
            
            V_r_left = V_r_left[:-1]
            #V_r = r.getV()
            #V_r = V_r[:-1]
            #r.setV(V_r)
            r.cargarDesdeSecuenciaDeVertices(V_r_left)
            costoSolucion += r.getCostoAsociado()
        
        return rutas
    
    def evaluar_4opt(self, arista_ini, ind_rutas, ind_A, rutas):
        """
        4-opt: (a,b)
        r1: 1,2,3,a,4,5,6        r2: 1,7,8,b,9,10,11,12
        resultado:
        r1: 1,2,3,a,b,5,6        r2: 1,7,8,4,9,10,11,12       -> 1ra opcion        
        r1: 1,2,b,a,4,5,6        r2: 1,7,8,3,9,10,11,12       -> 2da opcion
        r1: 1,2,3,9,4,5,6        r2: 1,7,8,b,a,10,11,12       -> 3ra opcion
        r1: 1,2,3,8,4,5,6        r2: 1,7,a,b,9,10,11,12       -> 4ta opcion 
        r: 1,2,3,a,4,5,6,b,7,8  -> Original
        resultado:
        r: 1,2,3,a,b,5,6,4,7,8  -> 1ra opcion
        r: 1,2,b,a,4,5,3,6,7,8  -> 2da opcion        
        r: 1,2,3,7,4,5,6,b,a,8  -> 3ra opcion
        r: 1,2,3,6,4,5,a,b,7,8  -> 4ta opcion
        """
        
        opcion = 0
        costo_solucion = float("inf")
        aristaInicial = copy.deepcopy(arista_ini)

        DROP = []
        index_DROP = []

        if(ind_A[1]-ind_A[0] == 1):
            return costo_solucion, opcion, DROP, index_DROP

        if(ind_rutas[0] != ind_rutas[1]):
            r1 = rutas[ind_rutas[0]]
            r2 = rutas[ind_rutas[1]]
            
            A_r1 = r1.getA()
            A_r2 = r2.getA()

            """
            r1: 1,2,a,3      r2: 1,5,b,6
            resultado:
            r1: 1,2,a,b      r2: 1,5,3,6       -> 1ra opcion        
            r1: 1,b,a,3      r2: 1,5,2,6       -> 2da opcion
            r1: 1,2,6,3      r2: 1,5,b,a       -> 3ra opcion
            r1: 1,2,5,3      r2: 1,a,b,6       -> 4ta opcion 
            """
            if(len(A_r1) <= 2 or len(A_r2) <= 2):
                return costo_solucion, opcion, [], []
            
            for i in range(1,5):
                arista_ini = copy.deepcopy(aristaInicial)
                if((i==2 or i==4) and (0 in ind_A or 1 in ind_A)):
                    continue
                if((i == 1 or i==3) and (len(r1.getV())-1 == ind_A[0] or len(r2.getV())-1 == ind_A[1]+1)):
                    #r1: 1,2,a        r2: 1,b,3
                    #r1: 1,2,a,b      r2: 1,1,4       -> No se puede 1ra opcion    
                    #r1: 1,2,3        r2: 1,b,a       -> 3ra opcion (No se puede aplicar 4-opt, se aplica 2-opt)
                    continue
                
                if(i == 1):
                    #r1: 1,2,3,a,4,5,6        r2: 1,7,8,b,9,10,11,12
                    #r1: 1,2,3,a,b,5,6        r2: 1,7,8,4,9,10,11,12       -> 1ra opcion
                    #print("Opcion ", i)
                    try:
                        A_r1_drop1 = A_r1[ind_A[0]]
                        A_r1_drop2 = A_r1[ind_A[0]+1]
                        A_r2_drop1 = A_r2[ind_A[1]]
                        A_r2_drop2 = A_r2[ind_A[1]+1]
                    except IndexError:
                        print("Arista ini: "+str(arista_ini))
                        print("A_r1: "+str(A_r1))
                        print("A_r2: "+str(A_r2))
                        print("ind_A: "+str(ind_A))
                        a = 1/0
                    A_r1_add1 = arista_ini

                    V_origen = A_r2_drop1.getDestino()
                    V_destino = A_r1_drop2.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r1_add2 = Arista(V_origen, V_destino, peso)
                    
                    V_origen = A_r2_drop1.getOrigen()
                    V_destino = A_r1_drop1.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r2_add1 = Arista(V_origen, V_destino, peso)
                    
                    V_origen = V_destino
                    V_destino = A_r2_drop2.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r2_add2 = Arista(V_origen, V_destino, peso)
                
                    if(A_r1_add1.getDestino() != A_r1_add2.getOrigen()):
                        arista_ini.invertir()
                elif(i == 2):
                    #print("Opcion ", i)
                    #r1: 1,2,3,a,4,5,6        r2: 1,7,8,b,9,10,11,12
                    #r1: 1,2,b,a,4,5,6        r2: 1,7,8,3,9,10,11,12       -> 2da opcion
                    A_r1_drop1 = A_r1[ind_A[0]-2]
                    A_r1_drop2 = A_r1[ind_A[0]-1]
                    A_r2_drop1 = A_r2[ind_A[1]]
                    A_r2_drop2 = A_r2[ind_A[1]+1]

                    A_r1_add2 = arista_ini

                    V_origen = A_r1_drop1.getOrigen()
                    V_destino = A_r2_drop1.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r1_add1 = Arista(V_origen, V_destino, peso)
                    
                    V_origen = A_r2_drop1.getOrigen()
                    V_destino = A_r1_drop1.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r2_add1 = Arista(V_origen, V_destino, peso)
                    
                    V_origen = V_destino
                    V_destino = A_r2_drop2.getDestino()
                    costo_r2_add2 = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r2_add2 = Arista(V_origen, V_destino, costo_r2_add2)
                elif(i == 3):
                    #r1: 1,2,3,a,4,5,6        r2: 1,7,8,b,9,10,11,12
                    #r1: 1,2,3,9,4,5,6        r2: 1,7,8,b,a,10,11,12       -> 3ra opcion
                    #print("Opcion ", i)
                    
                    A_r1_drop1 = A_r1[ind_A[0]-1]
                    A_r1_drop2 = A_r1[ind_A[0]]
                    A_r2_drop1 = A_r2[ind_A[1]+1]
                    A_r2_drop2 = A_r2[ind_A[1]+2]

                    A_r2_add1 = arista_ini

                    V_origen = A_r1_drop1.getOrigen()
                    V_destino = A_r2_drop1.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r1_add1 = Arista(V_origen, V_destino, peso)

                    V_origen = V_destino
                    V_destino = A_r1_drop2.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r1_add2 = Arista(V_origen, V_destino, peso)

                    V_origen = A_r1_drop1.getDestino()
                    V_destino = A_r2_drop2.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r2_add2 = Arista(V_origen, V_destino, peso)

                else:
                    #r1: 1,2,3,a,4,5,6        r2: 1,7,8,b,9,10,11,12
                    #r1: 1,2,3,8,4,5,6        r2: 1,7,a,b,9,10,11,12       -> 4ta opcion 
                    #print("Opcion ", i)
                    A_r1_drop1 = A_r1[ind_A[0]-1]
                    A_r1_drop2 = A_r1[ind_A[0]]
                    A_r2_drop1 = A_r2[ind_A[1]-1]
                    A_r2_drop2 = A_r2[ind_A[1]]

                    A_r2_add2 = arista_ini

                    V_origen = A_r1_drop1.getOrigen()
                    V_destino = A_r2_drop1.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r1_add1 = Arista(V_origen, V_destino, peso)

                    V_origen = V_destino
                    V_destino = A_r1_drop2.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r1_add2 = Arista(V_origen, V_destino, peso)

                    V_origen = A_r2_drop1.getOrigen()
                    V_destino = A_r1_drop1.getDestino()
                    costo_r2_add1 = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r2_add1 = Arista(V_origen, V_destino, costo_r2_add1)

                if(i == 3 or i == 4):
                    cap_r1 = r1.getCapacidad() - A_r1_drop1.getDestino().getDemanda() + A_r2_drop1.getDestino().getDemanda()
                    cap_r2 = r2.getCapacidad() - A_r2_drop1.getDestino().getDemanda() + A_r1_drop1.getDestino().getDemanda()
                else:
                    cap_r1 = r1.getCapacidad() - A_r1_drop1.getDestino().getDemanda() + A_r1_add1.getDestino().getDemanda()
                    cap_r2 = r2.getCapacidad() - A_r2_drop1.getDestino().getDemanda() + A_r2_add1.getDestino().getDemanda()
                
                if(cap_r1 > self.__capacidadMax or cap_r2 > self.__capacidadMax):
                    continue

                nuevo_costo = self.getCostoAsociado() + A_r1_add1.getPeso() + A_r1_add2.getPeso() + A_r2_add1.getPeso() + A_r2_add2.getPeso()
                nuevo_costo = nuevo_costo - A_r1_drop1.getPeso() - A_r1_drop2.getPeso() - A_r2_drop1.getPeso() - A_r2_drop2.getPeso()

                if(nuevo_costo < costo_solucion):
                    costo_solucion = nuevo_costo
                    opcion = i
                    DROP = []
                    index_DROP = []
                    DROP.append(A_r1_drop1)
                    DROP.append(A_r1_drop2)
                    DROP.append(A_r2_drop1)
                    DROP.append(A_r2_drop2)
                    index_DROP.append(A_r1_drop1.getId())
                    index_DROP.append(A_r1_drop2.getId())
                    index_DROP.append(A_r2_drop1.getId())
                    index_DROP.append(A_r2_drop2.getId())
        else:
            # r: 1,2,3,a,4,5,6,b,7,8  -> Original
            # r: 1,2,3,a,b,5,6,4,7,8  -> 1ra opcion
            # r: 1,2,b,a,4,5,3,6,7,8  -> 2da opcion        
            # r: 1,2,3,7,4,5,6,b,a,8  -> 3ra opcion
            # r: 1,2,3,6,4,5,a,b,7,8  -> 4ta opcion
                
            r = rutas[ind_rutas[0]]
            A_r = r.getA()
            if(len(A_r) <= 2):
                return costo_solucion, opcion, [], []
            
            for i in range(1,5):
                if(i==2 and (0 in ind_A or 1 in ind_A)):
                    continue
                if((i==3 or i==4) and 0 == ind_A[0]):
                    continue
                if(i==3 and len(r.getV())-1 == ind_A[1]+1):
                    continue
                if((i==1 or i==4) and (ind_A[1]-ind_A[0] <= 2)):
                    continue
                
                if(i == 1):
                    # r: 1,2,3,a,4,5,6,b,7,8  -> Original
                    # r: 1,2,3,a,b,5,6,4,7,8  -> 1ra opcion
                    #print("Opcion ",i)      
                    A_r_drop1 = A_r[ind_A[0]]
                    A_r_drop2 = A_r[ind_A[0]+1]
                    A_r_drop3 = A_r[ind_A[1]]
                    A_r_drop4 = A_r[ind_A[1]+1]

                    A_r_add1 = arista_ini
                    V_origen = A_r_drop4.getOrigen()
                    V_destino = A_r_drop2.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r_add2 = Arista(V_origen, V_destino, peso)

                    V_origen = A_r_drop3.getOrigen()
                    V_destino = A_r_drop1.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r_add3 = Arista(V_origen, V_destino, peso)

                    V_origen = V_destino
                    V_destino = A_r_drop4.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r_add4 = Arista(V_origen, V_destino, peso)

                    if(A_r_add1.getDestino() != A_r_add2.getOrigen()):
                        arista_ini.invertir()
                elif(i == 2):
                    # r: 1,2,3,a,4,5,6,b,7,8  -> Original
                    # r: 1,2,b,a,4,5,3,6,7,8  -> 2da opcion
                    A_r_drop1 = A_r[ind_A[0]-2]
                    A_r_drop2 = A_r[ind_A[0]-1]
                    A_r_drop3 = A_r[ind_A[1]]
                    A_r_drop4 = A_r[ind_A[1]+1]
                    
                    A_r_add2 = arista_ini

                    V_origen = A_r_drop1.getOrigen()
                    V_destino = A_r_drop4.getOrigen()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r_add1 = Arista(V_origen, V_destino, peso)

                        
                    V_origen = A_r_drop3.getOrigen()
                    V_destino = A_r_drop1.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r_add3 = Arista(V_origen, V_destino, peso)
                    
                    V_origen = V_destino
                    V_destino = A_r_drop4.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r_add4 = Arista(V_origen, V_destino, peso)

                    if(A_r_add1.getDestino() != A_r_add2.getOrigen()):
                        arista_ini.invertir()
                elif(i == 3):
                    # r: 1,2,3,a,4,5,6,b,7,8  -> Original
                    # r: 1,2,3,7,4,5,6,b,a,8  -> 3ra opcion
                    #print("Opcion ", i)
                    A_r_drop1 = A_r[ind_A[0]-1]
                    A_r_drop2 = A_r[ind_A[0]]
                    A_r_drop3 = A_r[ind_A[1]+1]
                    A_r_drop4 = A_r[ind_A[1]+2]

                    A_r_add3 = arista_ini

                    V_origen = A_r_drop1.getOrigen()
                    V_destino = A_r_drop3.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r_add1 = Arista(V_origen, V_destino, peso)

                    V_origen = V_destino
                    V_destino = A_r_drop2.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r_add2 = Arista(V_origen, V_destino, peso)

                    V_origen = A_r_drop2.getOrigen()
                    V_destino = A_r_drop4.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r_add4 = Arista(V_origen, V_destino, peso)
                    
                    if(A_r_add3.getDestino() != A_r_add4.getOrigen()):
                        arista_ini.invertir()
                else:
                    # r: 1,2,3,a,4,5,6,b,7,8  -> Original
                    # r: 1,2,3,6,4,5,a,b,7,8  -> 4ta opcion
                    #print("Opcion ", i)
                    A_r_drop1 = A_r[ind_A[0]-1]
                    A_r_drop2 = A_r[ind_A[0]]
                    A_r_drop3 = A_r[ind_A[1]-1]
                    A_r_drop4 = A_r[ind_A[1]]

                    A_r_add4 = arista_ini

                    V_origen = A_r_drop1.getOrigen()
                    V_destino = A_r_drop3.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r_add1 = Arista(V_origen, V_destino, peso)

                    V_origen = V_destino
                    V_destino = A_r_drop2.getDestino()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r_add2 = Arista(V_origen, V_destino, peso)

                    V_origen = A_r_drop3.getOrigen()
                    V_destino = A_r_drop2.getOrigen()
                    peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                    A_r_add3 = Arista(V_origen, V_destino, peso)

                    if(A_r_add3.getDestino() != A_r_add4.getOrigen()):
                        arista_ini.invertir()

                nuevo_costo = self.getCostoAsociado() + A_r_add1.getPeso() + A_r_add2.getPeso() + A_r_add3.getPeso() + A_r_add4.getPeso()
                nuevo_costo = nuevo_costo - A_r_drop1.getPeso() - A_r_drop2.getPeso() - A_r_drop3.getPeso() - A_r_drop4.getPeso()

                if(nuevo_costo < costo_solucion):
                    costo_solucion = nuevo_costo
                    opcion = i*(-1)
                    DROP = []
                    index_DROP = []
                    DROP.append(A_r_drop1)
                    DROP.append(A_r_drop2)
                    DROP.append(A_r_drop3)
                    DROP.append(A_r_drop4)
                    index_DROP.append(A_r_drop1.getId())
                    index_DROP.append(A_r_drop2.getId())
                    index_DROP.append(A_r_drop3.getId())
                    index_DROP.append(A_r_drop4.getId())
                
                #print("-> Nuevo costo: "+str(nuevo_costo)+"\n\n")

        return costo_solucion, opcion, DROP, index_DROP

    def swap_4opt(self, arista_ini, ind_rutas, ind_A, rutas, opcion):
        costo_solucion = self.getCostoAsociado()
        ADD = []
        DROP = []
        
        ADD.append(arista_ini)
        
        V_origen = arista_ini.getOrigen()
        V_destino = arista_ini.getDestino()
               
        #Cada ruta de al menos 4 aristas o 3 clientes. Si a o b estan al final: los intercambio
        ind_A_inicial = copy.copy(ind_A)
        
        
        if(opcion > 0):
            if(opcion==1 or opcion == 2):
                r1 = rutas[ind_rutas[0]]
                r2 = rutas[ind_rutas[1]]       
                if(opcion==2):     
                    ind_A[0] = ind_A_inicial[0]-2           
                    ind_A[1] = ind_A_inicial[1]      
                    V_origen = r1.getA()[ind_A[0]].getOrigen()
                    V_destino = arista_ini.getDestino()
                    peso = self._matrizDistancias[r1.getA()[ind_A[0]].getOrigen().getValue()-1][arista_ini.getDestino().getValue()-1]    
                    arista_nueva = Arista(V_origen, V_destino,peso)       
                    arista_nueva.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                    ADD = [arista_nueva]
                else:
                    ADD = [arista_ini]
                DROP = []
            elif(opcion==3 or opcion == 4):
                ind_A = copy.copy(ind_A_inicial)
                r1 = rutas[ind_rutas[1]]
                r2 = rutas[ind_rutas[0]]
                ind_A.reverse()

                if(opcion ==4):
                    ind_A[0] = ind_A[0]-1
                    ind_A[1] = ind_A[1]-1         
                    V_origen = r1.getA()[ind_A[0]].getOrigen()
                    V_destino = arista_ini.getOrigen()
                    peso = self._matrizDistancias[r1.getA()[ind_A[0]].getOrigen().getValue()-1][arista_ini.getOrigen().getValue()-1]    
                    arista_nueva = Arista(V_origen, V_destino,peso)       
                    arista_nueva.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                    ADD = [arista_nueva]                    
                else:
                    ADD = [arista_ini.getAristaInvertida()]
                    ind_A[0] += 1          
                    ind_A[1] -= 1
                DROP = []

            costo_solucion -= r1.getCostoAsociado()+r2.getCostoAsociado()
            
            V_r1 = r1.getV()
            if(V_r1[-1] != 1):
                V_r1.append(Vertice(1,0))
            
            if(V_origen == V_r1[-2] and opcion!=2):
                V_r1 = V_r1[::-1]
                ind_A[0] = 1
            
            V_r2 = r2.getV()
            if(V_r2[-1] != 1 ):
                V_r2.append(Vertice(1,0))

            if(V_destino == V_r2[-2] and opcion!=2):
                V_r2 = V_r2[::-1]
                ind_A[1] = 0
            
            V_r1_left = V_r1[:ind_A[0]+1]
            V_r1_right = V_r1[ind_A[0]+2:]
            V_r2_left = V_r2[:ind_A[1]+1]
            V_r2_right = V_r2[ind_A[1]+2:]    
            
            #Obtengo las aristas que se eliminan y las que se añaden
            #3 ADD's y 4 DROP's
            #1er DROP
            V_origen = V_r1[ind_A[0]]
            V_destino = V_r1[ind_A[0]+1]
            peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
            A_r1_drop1 = Arista(V_origen, V_destino, peso)
            A_r1_drop1.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))

            #2do DROP
            V_origen = V_destino
            V_destino = V_r1[ind_A[0]+2]
            
            peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
            A_r1_drop2 = Arista(V_origen, V_destino, peso)
            A_r1_drop2.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
            
            #2do ADD
            V_origen = ADD[0].getDestino()
            peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
            A_r1_add2 = Arista(V_origen, V_destino, peso)
            A_r1_add2.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
            
            #3er DROP
            V_origen = V_r2[ind_A[1]]
            V_destino = V_r2[ind_A[1]+1]
            peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
            A_r2_drop1 = Arista(V_origen, V_destino, peso)
            A_r2_drop1.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
            
            #3er ADD
            V_destino = V_r1[ind_A[0]+1]
            peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
            A_r2_add1 = Arista(V_origen, V_destino, peso)
            A_r2_add1.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
            
            #4to DROP
            V_origen = V_r2[ind_A[1]+1]
            V_destino = V_r2[ind_A[1]+2]
            peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
            A_r2_drop2 = Arista(V_origen, V_destino, peso)
            A_r2_drop2.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
            
            #4to ADD
            V_origen = A_r2_add1.getDestino()
            peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
            A_r2_add2 = Arista(V_origen, V_destino, peso)
            A_r2_add2.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
            
            DROP.append(A_r1_drop1)
            DROP.append(A_r1_drop2)
            DROP.append(A_r2_drop1)
            DROP.append(A_r2_drop2)
            
            ADD.append(A_r1_add2)
            ADD.append(A_r2_add1)
            ADD.append(A_r2_add2)

            V_r1_left.append(ADD[0].getDestino())
            V_r1_left.extend(V_r1_right)
            V_r2_left.append(ADD[2].getDestino())
            V_r2_left.extend(V_r2_right)
            
            if V_r1[-1] == 1:
                r1.setV(r1.getV()[:-1])
            if V_r2[-1] == 1:                
                r2.setV(r2.getV()[:-1])

            cap_r1 = r1.cargarDesdeSecuenciaDeVertices(V_r1_left[:-1])
            cap_r2 = r2.cargarDesdeSecuenciaDeVertices(V_r2_left[:-1])
            
            r1.setCapacidad(cap_r1)
            r2.setCapacidad(cap_r2)

            # if(cap_r1 > self.__capacidadMax or cap_r2 > self.__capacidadMax):
            #     print("r1: "+str(r1))
            #     print("r2: "+str(r2))
            #     print("ADD: "+str(ADD))
            #     print("DROP: "+str(DROP))
            #     print("Opcion: "+str(opcion))
            #     a = 1/0

        #4-opt en la misma ruta. Condicion: Deben haber 4 aristas de separacion entre a y b, si no se realiza 2-opt
        else:
            # r: 1,2,3,a,4,5,6,b,7,8  -> Original
            # r: 1,2,3,a,b,5,6,4,7,8  -> 1ra opcion
            # r: 1,2,b,a,4,5,3,6,7,8  -> 2da opcion        
            # r: 1,2,3,7,4,5,6,b,a,8  -> 3ra opcion
            # r: 1,2,3,6,4,5,a,b,7,8  -> 4ta opcion
            r = rutas[ind_rutas[0]]
            costo_solucion -= r.getCostoAsociado()
            A_r = r.getA()
            A_r_left = []
            A_r_middle = []
            A_r_right = []
            if(opcion == -1):
                # r: 1,2,3,a,4,5,6,b,7,8  -> Original
                # r: 1,2,3,a,b,5,6,4,7,8  -> 1ra opcion
                A_r_left = A_r[:ind_A[0]]
                A_r_middle = A_r[ind_A[0]+2:ind_A[1]]
                A_r_right = A_r[ind_A[1]+2:]

                A_r_drop1 = A_r[ind_A[0]]
                A_r_drop2 = A_r[ind_A[0]+1]
                A_r_drop3 = A_r[ind_A[1]]
                A_r_drop4 = A_r[ind_A[1]+1]

                A_r_add1 = arista_ini
                V_origen = A_r_drop4.getOrigen()
                V_destino = A_r_drop2.getDestino()
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r_add2 = Arista(V_origen, V_destino, peso)
                A_r_add2.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))


                V_origen = A_r_drop3.getOrigen()
                V_destino = A_r_drop1.getDestino()
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r_add3 = Arista(V_origen, V_destino, peso)
                A_r_add3.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))

                V_origen = V_destino
                V_destino = A_r_drop4.getDestino()
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r_add4 = Arista(V_origen, V_destino, peso)
                A_r_add4.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))

                if(A_r_add1.getDestino() != A_r_add2.getOrigen()):
                    arista_ini.invertir()

                # print("A_r_add1: "+str(A_r_add1))
                # print("A_r_add2: "+str(A_r_add2))
                # print("A_r_add3: "+str(A_r_add3))
                # print("A_r_add4: "+str(A_r_add4))
                # print("A_r_drop1: "+str(A_r_drop1))
                # print("A_r_drop3: "+str(A_r_drop2))
                # print("A_r_drop2: "+str(A_r_drop3))
                # print("A_r_drop4: "+str(A_r_drop4))

            elif(opcion == -2):
                # r: 1,2,3,a,4,5,6,b,7,8  -> Original
                # r: 1,2,b,a,4,5,3,6,7,8  -> 2da opcion
                #print("Opcion ",opcion)
                A_r_left = A_r[:ind_A[0]-2]
                A_r_middle = A_r[ind_A[0]:ind_A[1]]
                A_r_right = A_r[ind_A[1]+2:]
      
                A_r_drop1 = A_r[ind_A[0]-2]
                A_r_drop2 = A_r[ind_A[0]-1]
                A_r_drop3 = A_r[ind_A[1]]
                A_r_drop4 = A_r[ind_A[1]+1]

                A_r_add2 = arista_ini

                V_origen = A_r_drop1.getOrigen()
                V_destino = A_r_drop4.getOrigen()
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r_add1 = Arista(V_origen, V_destino, peso)
                A_r_add1.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                    
                V_origen = A_r_drop3.getOrigen()
                V_destino = A_r_drop1.getDestino()
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r_add3 = Arista(V_origen, V_destino, peso)
                A_r_add3.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                
                V_origen = V_destino
                V_destino = A_r_drop4.getDestino()
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r_add4 = Arista(V_origen, V_destino, peso)
                A_r_add4.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))

                if(A_r_add1.getDestino() != A_r_add2.getOrigen()):
                    arista_ini.invertir()
            elif(opcion == -3):
                # r: 1,2,3,a,4,5,6,b,7,8  -> Original
                # r: 1,2,3,7,4,5,6,b,a,8  -> 3ra opcion
                A_r_left = A_r[:ind_A[0]-1]
                A_r_middle = A_r[ind_A[0]+1:ind_A[1]+1]
                A_r_right = A_r[ind_A[1]+3:]

                A_r_drop1 = A_r[ind_A[0]-1]
                A_r_drop2 = A_r[ind_A[0]]
                A_r_drop3 = A_r[ind_A[1]+1]
                A_r_drop4 = A_r[ind_A[1]+2]

                A_r_add3 = arista_ini

                V_origen = A_r_drop1.getOrigen()
                V_destino = A_r_drop3.getDestino()
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r_add1 = Arista(V_origen, V_destino, peso)
                A_r_add1.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))

                V_origen = V_destino
                V_destino = A_r_drop2.getDestino()
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r_add2 = Arista(V_origen, V_destino, peso)
                A_r_add2.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))

                V_origen = A_r_drop2.getOrigen()
                V_destino = A_r_drop4.getDestino()
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r_add4 = Arista(V_origen, V_destino, peso)
                A_r_add4.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))
                
                if(A_r_add3.getDestino() != A_r_add4.getOrigen()):
                    arista_ini.invertir()
            else:
                # r: 1,2,3,a,4,5,6,b,7,8  -> Original
                # r: 1,2,3,6,4,5,a,b,7,8  -> 4ta opcion
                #print("Opcion ", opcion)
                A_r_left = A_r[:ind_A[0]-1]
                A_r_middle = A_r[ind_A[0]+1:ind_A[1]-1]
                A_r_right = A_r[ind_A[1]+1:]

                A_r_drop1 = A_r[ind_A[0]-1]
                A_r_drop2 = A_r[ind_A[0]]
                A_r_drop3 = A_r[ind_A[1]-1]
                A_r_drop4 = A_r[ind_A[1]]

                A_r_add4 = arista_ini

                V_origen = A_r_drop1.getOrigen()
                V_destino = A_r_drop3.getDestino()
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r_add1 = Arista(V_origen, V_destino, peso)
                A_r_add1.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))

                V_origen = V_destino
                V_destino = A_r_drop2.getDestino()
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r_add2 = Arista(V_origen, V_destino, peso)
                A_r_add2.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))

                V_origen = A_r_drop3.getOrigen()
                V_destino = A_r_drop2.getOrigen()
                peso = self._matrizDistancias[V_origen.getValue()-1][V_destino.getValue()-1]
                A_r_add3 = Arista(V_origen, V_destino, peso)
                A_r_add3.setId(V_origen.getValue()-1, V_destino.getValue()-1, len(self._matrizDistancias))

                if(A_r_add3.getDestino() != A_r_add4.getOrigen()):
                    arista_ini.invertir()

            A_r_left.append(A_r_add1)
            A_r_left.append(A_r_add2)
            A_r_left.extend(A_r_middle)
            A_r_left.append(A_r_add3)
            A_r_left.append(A_r_add4)
            A_r_left.extend(A_r_right)
            
            cap = r.cargarDesdeAristas(A_r_left)
            r.setCapacidad(cap)

        return rutas

    def swap_4optPR(self, indR1, indR2, indS, sigIndS, rutas, rutasInfactibles):
        r1 = rutas[indR1]
        r2 = rutas[indR2]
        V_r1 = r1.getV()
        V_r2 = r2.getV()
        aristaAux = copy.copy(V_r1[indS])
        V_r1[indS] = V_r2[sigIndS]
        V_r2[sigIndS] = aristaAux
        
        cap_r1 = rutas[indR1].cargarDesdeSecuenciaDeVertices(V_r1)
        rutas[indR1].setCapacidad(cap_r1)
        #print("capR1: ",cap_r1)
        
        cap_r2 = rutas[indR2].cargarDesdeSecuenciaDeVertices(V_r2)
        rutas[indR2].setCapacidad(cap_r2)
        #print("capR2: ",cap_r2)
        
        if cap_r1 > self.__capacidadMax or cap_r2 > self.__capacidadMax:
            if cap_r1 > self.__capacidadMax:
                rutasInfactibles = rutasInfactibles | set({indR1})
            else:
                rutasInfactibles = rutasInfactibles - set({indR1})
            if cap_r2 > self.__capacidadMax:
                rutasInfactibles = rutasInfactibles | set({indR2})
            else:
                rutasInfactibles = rutasInfactibles - set({indR2})

            return rutas, False, rutasInfactibles
        else:
            rutasInfactibles = rutasInfactibles - set({indR1, indR2})
            return rutas, True, rutasInfactibles

    def evaluar_Exchange(self, aristaIni, ind_rutas, ind_A, rutas):
        """
        Dos rutas distintas:
            Rutas: 
                r1: 1,2,3,a,4,5,6,7,1           r2: 1,8,9,10,b,11,12,1
            Opción 1:
                r1: 1,2,3,a,b,11,5,6,7,1          r2: 1,8,9,10,12,1
            Opción 2:
                r1: 1,2,3,10,b,a,4,11,6,7,1     r2: 1,8,9,11,12,1
            Opción 3:
                r1: 1,2,3,5,6,7,1               r2: 1,8,9,10,b,a,4,11,12,1
            Opción 4:
                r1: 1,2,4,5,6,7,1               r2: 1,8,9,10,3,a,b,11,12,1

        Misma ruta:
            Ruta:
                r1: 1,2,3,a,4,5,6,7,8,b,9,10,11,1

            Opción 1:
                r1: 1,2,3,a,b,9,4,5,6,7,8,10,11,1
            Opción 2:
                r1: 1,2,3,8,b,a,4,5,6,7,9,10,11,1
            Opción 3:
                r1: 1,2,3,5,6,7,8,b,a,4,9,10,11,1
            Opción 4:
                r1: 1,2,4,5,6,7,8,3,a,b,9,10,11,1
        """
        

        opciones = []
        DROP = []
        index_DROP = []
        ADD = []
        index_ADD = []

        distintasRutas = True
        ind_A[1]+=1
        M = self._matrizDistancias
        costoSolucion = float("inf")
        opcionRet = 0
        tam = len(self._matrizDistancias)
        if ind_rutas[0]!=ind_rutas[1]:
            r1 = rutas[ind_rutas[0]]
            r2 = rutas[ind_rutas[1]]
            nR1 = len(r1.getA())
            nR2 = len(r2.getA())

            if (0< ind_A[0] <nR1-1) and (0< ind_A[1] <nR2-2):
                opciones.append(1)
            if (1< ind_A[0] <nR1) and (2< ind_A[1] <nR2-1):
                opciones.append(2)
            if (0< ind_A[0] <nR1-2) and (0< ind_A[1] <nR2-1):
                opciones.append(3)
            if (2< ind_A[0] <nR1-1) and (1< ind_A[1] <nR2-1):
                opciones.append(4)
        else:
            distintasRutas = False
            r = rutas[ind_rutas[0]]
            N = len(r.getA())
            if (0<ind_A[0]) and (ind_A[0]+1<ind_A[1]<N-2):
                opciones.append(1)
            if (1<ind_A[0]) and (ind_A[0]+2<ind_A[1]<N-1):
                opciones.append(2)
            if (0<ind_A[0]) and (ind_A[0]+1<ind_A[1]<N-2):
                opciones.append(3)
            if (1<ind_A[0]) and (ind_A[0]+2<ind_A[1]<N-1):
                opciones.append(4)

        if distintasRutas:
            for opcion in opciones:

                aR1 = r1.getA()
                aR2 = r2.getA()
                                    
                if opcion == 1:
                    demandaR1 = r1.getCapacidad()
                    b = aR2[ind_A[1]]
                    sigB = aR2[ind_A[1]+1]
                    demR1 = demandaR1 + b.getOrigen().getDemanda() + sigB.getOrigen().getDemanda()
                    if demR1 > self.getCapacidadMax():
                        continue
                    a = aR1[ind_A[0]]
                    sigA = aR1[ind_A[0]+1]
                    antB = aR2[ind_A[1]-1]
                    sigSigB = aR2[ind_A[1]+2]
                elif opcion == 2:
                    demandaR1 = r1.getCapacidad()
                    b = aR2[ind_A[1]-1]
                    sigB = aR2[ind_A[1]]
                    demR1 = demandaR1 + b.getOrigen().getDemanda() + sigB.getOrigen().getDemanda()
                    if demR1 > self.getCapacidadMax():
                        continue
                    a = aR1[ind_A[0]-1]
                    sigA = aR1[ind_A[0]]
                    antB = aR2[ind_A[1]-2]
                    sigSigB = aR2[ind_A[1]+1]    
                elif opcion == 3:
                    demandaR1 = r2.getCapacidad()
                    b = aR1[ind_A[0]]
                    sigB = aR1[ind_A[0]+1]
                    demR1 = demandaR1 + b.getOrigen().getDemanda() + sigB.getOrigen().getDemanda()
                    if demR1 > self.getCapacidadMax():
                        continue
                    a = aR2[ind_A[1]]
                    sigA = aR2[ind_A[1]+1]
                    antB = aR1[ind_A[0]-1]
                    sigSigB = aR1[ind_A[0]+2]                        
                elif opcion == 4:
                    demandaR1 = r2.getCapacidad()
                    b = aR1[ind_A[0]-1]
                    sigB = aR1[ind_A[0]]
                    demR1 = demandaR1 + b.getOrigen().getDemanda() + sigB.getOrigen().getDemanda()
                    if demR1 > self.getCapacidadMax():
                        continue
                    a = aR2[ind_A[1]-1]
                    sigA = aR2[ind_A[1]]
                    antB = aR1[ind_A[0]-2]
                    sigSigB = aR1[ind_A[0]+1]    


                costo = M[a.getOrigen().getValue()-1][b.getOrigen().getValue()-1]
                ADD1 = Arista(a.getOrigen(),b.getOrigen(),costo, tam)
                ADD1.setId(a.getOrigen().getValue()-1, b.getOrigen().getValue()-1, len(M))

                costo = M[sigB.getOrigen().getValue()-1][sigA.getOrigen().getValue()-1]
                ADD2 = Arista(sigB.getOrigen(),sigA.getOrigen(),costo, tam)
                ADD2.setId(sigB.getOrigen().getValue()-1, sigA.getOrigen().getValue()-1, len(M))

                costo = M[antB.getOrigen().getValue()-1][sigSigB.getOrigen().getValue()-1]
                ADD3 = Arista(antB.getOrigen(),sigSigB.getOrigen(),costo, tam)
                ADD3.setId(antB.getOrigen().getValue()-1, sigSigB.getOrigen().getValue()-1, len(M))
                
                costo = M[antB.getOrigen().getValue()-1][b.getOrigen().getValue()-1]
                DROP1 = Arista(antB.getOrigen(),b.getOrigen(),costo, tam)
                DROP1.setId(antB.getOrigen().getValue()-1, b.getOrigen().getValue()-1, len(M))

                costo = M[sigB.getOrigen().getValue()-1][sigSigB.getOrigen().getValue()-1]
                DROP2 = Arista(sigB.getOrigen(),sigSigB.getOrigen(),costo, tam)
                DROP2.setId(sigB.getOrigen().getValue()-1, sigSigB.getOrigen().getValue()-1, len(M))

                costo = M[a.getOrigen().getValue()-1][sigA.getOrigen().getValue()-1]
                DROP3 = Arista(a.getOrigen(),sigA.getOrigen(),costo, tam)
                DROP3.setId(a.getOrigen().getValue()-1, sigA.getOrigen().getValue()-1, len(M))
                
                costoNuevo = self.getCostoAsociado() + ADD1.getPeso() + ADD2.getPeso() + ADD3.getPeso() - DROP1.getPeso() - DROP2.getPeso() - DROP3.getPeso()

                # print(f"opcion {opcion} => costo= {costoNuevo} ")
                if(costoNuevo < costoSolucion):
                    costoSolucion = costoNuevo
                    opcionRet = opcion
                    DROP = [DROP1,DROP2,DROP3]
                    ADD = [ADD1,ADD2,ADD3]
                    index_DROP = [DROP1.getId(), DROP2.getId(), DROP3.getId()]
                    index_ADD = [ADD1.getId(), ADD2.getId(), ADD3.getId()]

        else:
            for opcion in opciones:

                A = r.getA()
                                               
                if opcion == 1:
                    a = A[ind_A[0]]
                    sigA = A[ind_A[0]+1]
                    antB = A[ind_A[1]-1]
                    b = A[ind_A[1]]
                    sigB = A[ind_A[1]+1]
                    sigSigB = A[ind_A[1]+2]
                elif opcion == 2: 
                    a = A[ind_A[0]-1]
                    sigA = A[ind_A[0]]
                    antB = A[ind_A[1]-2]
                    b = A[ind_A[1]-1]
                    sigB = A[ind_A[1]]
                    sigSigB = A[ind_A[1]+1]          
                elif opcion == 3: 
                    a = A[ind_A[1]]
                    sigA = A[ind_A[1]+1]
                    antB = A[ind_A[0]-1]
                    b = A[ind_A[0]]
                    sigB = A[ind_A[0]+1]
                    sigSigB = A[ind_A[0]+2]     
                elif opcion == 4: 
                    a = A[ind_A[1]-1]
                    sigA = A[ind_A[1]]
                    antB = A[ind_A[0]-2]
                    b = A[ind_A[0]-1]
                    sigB = A[ind_A[0]]
                    sigSigB = A[ind_A[0]+1]              

                costo = M[a.getOrigen().getValue()-1][b.getOrigen().getValue()-1]
                ADD1 = Arista(a.getOrigen(),b.getOrigen(),costo, tam)
                ADD1.setId(a.getOrigen().getValue()-1, b.getOrigen().getValue()-1, len(M))

                costo = M[sigB.getOrigen().getValue()-1][sigA.getOrigen().getValue()-1]
                ADD2 = Arista(sigB.getOrigen(),sigA.getOrigen(),costo, tam)
                ADD2.setId(sigB.getOrigen().getValue()-1, sigA.getOrigen().getValue()-1, len(M))

                costo = M[antB.getOrigen().getValue()-1][sigSigB.getOrigen().getValue()-1]
                ADD3 = Arista(antB.getOrigen(),sigSigB.getOrigen(),costo, tam)
                ADD3.setId(antB.getOrigen().getValue()-1, sigSigB.getOrigen().getValue()-1, len(M))
                
                costo = M[antB.getOrigen().getValue()-1][b.getOrigen().getValue()-1]
                DROP1 = Arista(antB.getOrigen(),b.getOrigen(),costo, tam)
                DROP1.setId(antB.getOrigen().getValue()-1, b.getOrigen().getValue()-1, len(M))

                costo = M[sigB.getOrigen().getValue()-1][sigSigB.getOrigen().getValue()-1]
                DROP2 = Arista(sigB.getOrigen(),sigSigB.getOrigen(),costo, tam)
                DROP2.setId(sigB.getOrigen().getValue()-1, sigSigB.getOrigen().getValue()-1, len(M))

                costo = M[a.getOrigen().getValue()-1][sigA.getOrigen().getValue()-1]
                DROP3 = Arista(a.getOrigen(),sigA.getOrigen(),costo, tam)
                DROP3.setId(a.getOrigen().getValue()-1, sigA.getOrigen().getValue()-1, len(M))
                
                costoActual =self.getCostoAsociado()
                costoNuevo = costoActual + ADD1.getPeso() + ADD2.getPeso() + ADD3.getPeso() - DROP1.getPeso() - DROP2.getPeso() - DROP3.getPeso()
                # print(f"opcion {opcion} => costo= {costoNuevo} ")

                if(costoNuevo < costoSolucion):
                    costoSolucion = costoNuevo
                    opcionRet = opcion
                    DROP = [DROP1,DROP2,DROP3]
                    ADD = [ADD1,ADD2,ADD3]
                    index_DROP = [DROP1.getId(), DROP2.getId(), DROP3.getId()]
                    index_ADD = [ADD1.getId(), ADD2.getId(), ADD3.getId()]

        return costoSolucion, opcionRet, DROP, index_DROP

    def swap_Exchange(self, arista_ini, ind_rutas, ind_A, rutas, opcion):
        M = self._matrizDistancias
        tam = len(self._matrizDistancias)
        if(ind_rutas[0]!=ind_rutas[1]):
            r1 = rutas[ind_rutas[0]]
            r2 = rutas[ind_rutas[1]]
            
            aR1 = r1.getA()
            aR2 = r2.getA()
            ind_A[1]+=1
            if opcion == 1 or opcion == 2:
                if opcion == 1:
                    pass
                elif opcion == 2:
                    ind_A[0]-=1
                    ind_A[1]-=1

                antA = aR1[ind_A[0]-1]
                a = aR1[ind_A[0]]
                sigA = aR1[ind_A[0]+1]
                antB = aR2[ind_A[1]-1]
                b = aR2[ind_A[1]]
                sigB = aR2[ind_A[1]+1]
                sigSigB = aR2[ind_A[1]+2]
            elif opcion == 3 or opcion == 4:    

                if opcion == 3:
                    pass
                elif opcion == 4:
                    ind_A[0]-=1
                    ind_A[1]-=1

                antA = aR2[ind_A[1]-1]
                a = aR2[ind_A[1]]
                sigA = aR2[ind_A[1]+1]

                antB = aR1[ind_A[0]-1]
                b = aR1[ind_A[0]]
                sigB = aR1[ind_A[0]+1]
                sigSigB = aR1[ind_A[0]+2]


            peso = M[a.getOrigen().getValue()-1][b.getOrigen().getValue()-1]
            a = Arista(a.getOrigen(), b.getOrigen(), peso, tam)
            peso = M[sigB.getOrigen().getValue()-1][sigA.getOrigen().getValue()-1]
            sigB = Arista(sigB.getOrigen(), sigA.getOrigen(), peso, tam)
            peso = M[antB.getOrigen().getValue()-1][sigSigB.getOrigen().getValue()-1]
            antB = Arista(antB.getOrigen(), sigSigB.getOrigen(), peso, tam)
            if opcion == 1 or opcion == 2:
                aR1.insert(ind_A[0],a)
                aR1.pop(ind_A[0]+1)
                aR1.insert(ind_A[0]+1,b)
                aR1.insert(ind_A[0]+2,sigB)
                aR2.pop(ind_A[1])
                aR2.pop(ind_A[1])
                aR2.insert(ind_A[1]-1,antB)
                aR2.pop(ind_A[1])
            elif opcion == 3 or opcion == 4:
                aR2.insert(ind_A[1],a)
                aR2.pop(ind_A[1]+1)
                aR2.insert(ind_A[1]+1,b)
                aR2.insert(ind_A[1]+2,sigB)
                aR1.pop(ind_A[0])
                aR1.pop(ind_A[0])
                aR1.insert(ind_A[0]-1,antB)
                aR1.pop(ind_A[0])
            cap1 = r1.cargarDesdeAristas(r1.getA())
            cap2 = r2.cargarDesdeAristas(r2.getA())
            r1.setCapacidad(cap1)
            r2.setCapacidad(cap2)
        else:
            r = rutas[ind_rutas[0]]
            A = r.getA()
            ind_A[1]+=1
            if opcion == 1 or opcion == 2:
                if opcion == 1:
                    pass
                elif opcion == 2:
                    ind_A[0]-=1
                    ind_A[1]-=1
                    
                a = A[ind_A[0]]
                sigA = A[ind_A[0]+1]
                antB = A[ind_A[1]-1]
                b = A[ind_A[1]]
                sigB = A[ind_A[1]+1]
                sigSigB = A[ind_A[1]+2]

                peso = M[a.getOrigen().getValue()-1][b.getOrigen().getValue()-1]
                a = Arista(a.getOrigen(),b.getOrigen(),peso, tam)
                peso = M[sigB.getOrigen().getValue()-1][sigA.getOrigen().getValue()-1]
                sigB = Arista(sigB.getOrigen(),sigA.getOrigen(),peso, tam)
                peso = M[antB.getOrigen().getValue()-1][sigSigB.getOrigen().getValue()-1]
                antB = Arista(antB.getOrigen(),sigSigB.getOrigen(),peso, tam)

                A.insert(ind_A[0],a)
                A.pop(ind_A[0]+1)
                A.insert(ind_A[0]+1,b)
                A.insert(ind_A[0]+2,sigB)
                A.pop(ind_A[1]+2)
                A.pop(ind_A[1]+2)
                A.insert(ind_A[1]+1,antB)
                A.pop(ind_A[1]+2)
            elif opcion == 3 or opcion == 4: 
                if opcion == 3:
                    pass
                elif opcion == 4:
                    ind_A[0]-=1
                    ind_A[1]-=1

                antA = A[ind_A[1]-1]
                a = A[ind_A[1]]
                sigA = A[ind_A[1]+1]

                antB = A[ind_A[0]-1]
                b = A[ind_A[0]]
                sigB = A[ind_A[0]+1]
                sigSigB = A[ind_A[0]+2]

                peso = M[a.getOrigen().getValue()-1][b.getOrigen().getValue()-1]
                a = Arista(a.getOrigen(),b.getOrigen(),peso, tam)
                peso = M[sigB.getOrigen().getValue()-1][sigA.getOrigen().getValue()-1]
                sigB = Arista(sigB.getOrigen(),sigA.getOrigen(),peso, tam)
                peso = M[antB.getOrigen().getValue()-1][sigSigB.getOrigen().getValue()-1]
                antB = Arista(antB.getOrigen(),sigSigB.getOrigen(),peso, tam)

                A.insert(ind_A[1],a)
                A.pop(ind_A[1]+1)
                A.insert(ind_A[1]+1,b)
                A.insert(ind_A[1]+2,sigB)
                A.pop(ind_A[0])
                A.pop(ind_A[0])
                A.insert(ind_A[0]-1,antB)
                A.pop(ind_A[0])


            r.cargarDesdeAristas(A)

        return rutas

    def eliminarRutasSobrantes(self, rutas, nroVehiculos, capacidad):
        """ La idea sería:
                1)Elegir como ruta sobrante, la que tenga menos vértices, si hay más de una, ordenarlas de
                forma ascendiente, con respecto a la cantidad de elementos. En variable RS --> por rutas sobrantes
                2)Las demás rutas, se las ordena de forma descendiente, según su capacidad. En variable RF --> por rutas factibles
                3)Repetir hasta que la/s ruta/s sobrantes estén vacías.
                    1)Por cada elemento de RS. Recorrer todas las rutas de RF y ver en cuales se puede agregar, las rutas en la
                    que se pueda agregar se las agrega a la lista RC --> por rutas candidatas.
                        Si |RC| == 0
                            depurarEspacioEnRutas() --> es otra función, este sería el peor de los casos.
                            intentar de nuevo a ver si se lo puede agregar en alguna ruta. Si no se puede, a llorar a Magoya
                        Si no
                            Buscar la ubicación de menor costo para el elemento en la RC.
        """
        indRS = self.rutasSobrantes(rutas, nroVehiculos)
        RS = [rutas[i] for i in indRS]
        RF = [rutas[i] for i in range(len(rutas)) if i not in indRS]
        RF = self.rutasDemandaOrdenada(RF)
        iterac = 0
        # costoAntes = sum([x.getCostoAsociado() for x in rutas])
        # print("Costo antes ", costoAntes)
        
        for rutaSobrante in RS:
            iterac += 1
            verticesRuta, indiceV = self.demandasOrdenadas(rutaSobrante, desc=True, index=True)
            verticesRuta = verticesRuta[:-1]
            indiceV = indiceV[:-1]
            while len(verticesRuta)!=0 and len(rutas) != nroVehiculos:
                capacidadNecesaria = capacidad - verticesRuta[0].getDemanda()
                RC = self.rutasConCapacidadDisponible(RF, capacidadNecesaria)
                
                if len(RC) == 0:
                    self.depurarRutas(RF, capacidadNecesaria, capacidad, 3)
                    RC = self.rutasConCapacidadDisponible(RF, capacidadNecesaria)
                if len(RC) != 0:
                    self.insertarEnMejorUbicacion(verticesRuta[0], indiceV[0], rutaSobrante,RC)
                    verticesRuta, indiceV = self.demandasOrdenadas(rutaSobrante, desc=True, index=True)
                    verticesRuta = verticesRuta[:-1]
                    indiceV = indiceV[:-1]

            if iterac > 10:
                rutas = []
                return rutas
        for i in indRS:
            rutas.pop(i)
        for x in rutas:
            x.cargarDesdeSecuenciaDeVertices(x.getV())

        # costoDespues = sum([x.getCostoAsociado() for x in rutas])
        # print("Costo después ", costoDespues)
        
        return rutas

    def depurarRutas(self, rutas, cantidadNecesaria, capacidad, rec):
        """
            1) Buscar la ruta que más espacio disponible tenga, guardar en variable rutaConMasEspacio
            2) Armar una lista de vértices, ordenando ascendentemente según la demanda, en variable verticesDemandaDesc
            3) Hasta que la demanda de la ruta sea menor a la cantidadNecesaria
                Sea x el vértice de menor demanda de verticesConMenosDemanda
                1) Armar una lista con todas las posibles rutas donde se pueda insertar a x.
                    Si la lista está vacía:
                        Se sigue con el siguiente vértice x.
                    Si no:
                        Se busca la mejor ubicación para insertar x.
        """
        i = 0
        demandaRutaActual = float("inf")
        while i < len(rutas) and demandaRutaActual > cantidadNecesaria:
            #rutaConMasEspacio = self.rutasDemandaOrdenada(rutas)[:i+1][0]
            rutaConMasEspacio, indRutaConMasEspacio = self.rutasMasDivisibles(rutas)
            rutaConMasEspacio = rutaConMasEspacio[:i+1][0]
            indRutaConMasEspacio = indRutaConMasEspacio[:i+1][0]
            rutasRestantes = [rutas[r] for r in range(len(rutas)) if r != indRutaConMasEspacio]
            demandaRutaActual = rutaConMasEspacio.getCapacidad()
            verticesDemandaDesc, indicesV = self.demandasOrdenadas(rutaConMasEspacio, desc=True, index=True)
            verticesDemandaDesc = verticesDemandaDesc[:-1]
            indicesV = indicesV[:-1]
            seguir = True
            while len(verticesDemandaDesc) != 0 and demandaRutaActual > cantidadNecesaria and seguir:
                x = verticesDemandaDesc.pop()
                j = indicesV.pop()
                RC = self.rutasConCapacidadDisponible(rutasRestantes, capacidad - x.getDemanda())
                if len(RC) == 0:
                    if rec != 0:
                        RC = self.depurarRutas(rutasRestantes, capacidad - x.getDemanda(), capacidad, rec-1)
                        if len(RC) == 0:
                            if rec != 0:
                                return []
                            else:
                                seguir = False
                    else:
                        seguir = False
                if len(RC) != 0:
                    self.insertarEnMejorUbicacion(x, j, rutaConMasEspacio, RC)
                    verticesDemandaDesc, indicesV = self.demandasOrdenadas(rutaConMasEspacio, desc=True, index=True)
                    verticesDemandaDesc = verticesDemandaDesc[:-1]
                    indicesV = indicesV[:-1]
                    demandaRutaActual = rutaConMasEspacio.getCapacidad()
            i += 1

        return RC
    
    def rutasMasDivisibles(self, rutas):
        """ Si, algo feo el nombre de la función. Pendiente, buscar un mejor nombre.
            Esta función va a retornar una lista de rutas con sus respectivos índicas
            ordenadas según la cantidad de vértices con menor demandañ
            Se ordena las rutas por según el valor del primer cuartil.
            Las que tengan el primer cuartil más bajo, tienen clientes
            con menor demanda.
        """
        rutasConVerticesOrdenados = [self.demandasOrdenadas(r) for r in rutas] #Ordenados por demanda
        Q = [] #Indices del primer cuartil de cada ruta
        i = 0
        for r in rutasConVerticesOrdenados:
            n = len(r[1:])
            if n > 4:
                indices = list(range(1,n+1))
                if n % 2:
                    indMed = int((indices[int(n/2)] + indices[int(n/2) + 1])/2)
                    mediana = r[indMed]
                    indPriCuartil = int((indices[int(n/4)] + indices[int(n/4) + 1])/2)
                else:
                    indMed = int(n/2) + 1
                    mediana = r[indMed]
                    indPriCuartil = int(n/4) + 1
                tamQ = len(r[:indPriCuartil])
                q = (i, tamQ, r[indPriCuartil].getDemanda())
                Q.append(q)
            else:
                q = (i, float("inf"), float("inf"))
                Q.append(q)
            i+=1
            #print(f"Tamaño primer cuartil ruta {tamQ}")
        Q = sorted(Q, key=lambda x: (x[2], x[1]))
        ret = [rutas[q[0]] for q in Q]
        ind = [q[0] for q in Q]

        #[print("Ruta " + str(q[2]) + " --> primer cuartil: " + str(q[1]) + "\n") for q in Q]
        return ret, ind

    def rutasDemandaOrdenada(self, rutas, desc=False):
        """ Retorna las rutas ordenadas descendientemente por demanda """
        return sorted(rutas, key=lambda x: x.getCapacidad(), reverse=False)

    def insertarEnMejorUbicacion(self, v, ind, ruta, rutas):
        """ Inserta el vértice v buscando la ubicación con menor costo en las rutas dadas.
            También se elimina a v de su ubiación anterior (ruta)
        """
        indMejorUbicacion = 1
        indMejorRuta = 0
        costoMin = float("inf")
        M = self._matrizDistancias
        for r in range(len(rutas)):
            verticesRuta = rutas[r].getV()
            for i in range(len(verticesRuta)):
                if i < len(verticesRuta) and i == 0:
                    costo = M[i][v.getValue()-1] + M[verticesRuta[i+1].getValue()-1][v.getValue()-1]
                elif i < len(verticesRuta):
                    costoAnterior = M[verticesRuta[i-1].getValue()-1][v.getValue()-1] #Es el costo entre el vértice anterior y v
                    costoSiguiente = M[v.getValue()-1][verticesRuta[i].getValue()-1] #Es el costo entre el vértice siguiente y v
                    costo = costoAnterior + costoSiguiente
                else:
                    costo = M[i][v.getValue()-1] + M[1][v.getValue()-1] #Para que tenga en cuenta al depósito
                if costo <= costoMin:
                    costoMin = costo
                    indMejorUbicacion = i
                    indMejorRuta = r

        ruta.getV().pop(ind) #Es 1 para no borrar el depósito
        ruta.setCapacidad(ruta.getCapacidad() - v.getDemanda())
        rutas[indMejorRuta].getV().insert(indMejorUbicacion+1, v)
        rutas[indMejorRuta].setCapacidad(rutas[indMejorRuta].getCapacidad() + v.getDemanda())

    def demandasOrdenadas(self, ruta, desc=False, index=False):
        """Retorna una lista con los vértices de la ruta ordenados ascendentemente, retorna los indices"""
        if index:
            ind = list(range(len(ruta)))
            indices = sorted(ind, key=lambda x: ruta.getV()[x].getDemanda(), reverse=desc)
            vert = [ruta.getV()[r] for r in indices]
            return vert,indices
        else:
            return sorted(ruta.getV(), key=lambda x: x.getDemanda(), reverse=desc)

    def rutasConCapacidadDisponible(self, rutas, capacidadNecesaria):
        """Retorna una lista con rutas que tienen la capacidad necesaria"""
        return [r for r in rutas if r.getCapacidad() <= capacidadNecesaria]

    def rutasSobrantes(self, rutas, nroVehiculos):
        """ Retorna los/s índice/s de las ruta/s con menos demanda dependiendo de cuantas sobren
            Con "sobrar" me refiero a que la cantidad de rutas sobrepasa la cantidad de vehículos mínima
        """
        cantidadSobrante = len(rutas) - nroVehiculos
        if cantidadSobrante > 0:
            ind = []
            indicesRutas = list(range(len(rutas)))
            for i in range(cantidadSobrante):
                jMin = 0
                minimo = float("inf")
                for j in indicesRutas:
                    if(rutas[j].getCapacidad() < minimo):
                        jMin = j
                        minimo = rutas[j].getCapacidad()
                ind.append(jMin)
                indicesRutas.pop(jMin)
            return ind
        else:
            return []

    def controlaCapacidad(self, rutas, capMax):
        for r in rutas:
            print(r.getCapacidad())
            if r.getCapacidad() > r.__capacidadMax:
                print("SUPERO CAPACIDAD")
                return False
        return True
