from Vertice import Vertice
from Arista import Arista
from Grafo import Grafo
from Solucion import Solucion
from Tabu import Tabu, ListaTabu
import random 
import sys
import re
import math 
import copy
import numpy as np
from clsTxt import clsTxt
from time import time
import datetime
import DB
import json

class TSP:
    def __init__(self,
                 M,
                 D,
                 archivo,
                 carpeta,
                 solI,
                 tADD,
                 tDROP,
                 tiempo,
                 porcentaje,
                 optimo,
                 cargarEnDB=None,
                 idInstancia=None,
                 criterioTenure=None,
                 coordenadas=None,
                 cantidad=None,
                 orden=None,
                 indBarra=None):
        
        self.__solInicial = ['Clark & Wright', 'Vecino cercano', 'Secuencial', 'Al azar']
        self._G = Grafo(M, D)                #Grafo original
        self.__S = Solucion(M, D, sum(D))    #Solucion general del TSP
        self.__Distancias = M                #Matriz de distancias
        self.__rutas = []                    #Soluciones por vehiculo (lista de soluciones)
        self.__tipoSolucionIni = solI        #Tipo de solucion inicial (Clark & Wright, Vecino cercano, Secuencial o al Azar)
        self.__beta = 1                      #Parametro de dispersion
        self.__umbralMin = 0                 #Umbral de granularidad minimo
        self.__optimosLocales = []           #Lista de optimos locales 
        self.__porcentajeParada = float(porcentaje) #Porcentaje de desvio minimo como condicion de parada
        self.__optimo = optimo               #Mejor valor de la instancia
        self.__tenureADD =  tADD
        self.__tenureMaxADD = int(tADD*1.7)
        self.__tenureDROP =  tDROP
        self.__tenureMaxDROP = int(tDROP*1.7)
        self.__txt = clsTxt(str(archivo), str(carpeta), "nada", "nada")
        self.__tiempoMaxEjec = float(tiempo)
        self.escribirDatos()
        
        self.__S.setCapacidadMax(self.__capacidadMax)
        tiempoIni = time()
        
        """
        Se obtienen las rutas correspondiente a la solución inicial seleccionada, solo si es factible.
        En caso contrario, se elige una solución inicial que sea factible.
        """
        self.__rutas, self.__tipoSolucionIni = self.__S.rutasIniciales(self.__tipoSolucionIni, self.__nroVehiculos, self.__Demandas, self.__capacidadMax, self._G)
        self.__tiempoMaxEjec = self.__tiempoMaxEjec - ((time()-tiempoIni)/60)
        #tiempoIni = time()
        self.__S, strText = self.cargaSolucion(self.__rutas)
        print("costo Total sol inicial", sum([x.getCostoAsociado() for x in self.__rutas ]))
        self.__txt.escribir(strText)
        self.__costosOptimosLocales = []
        #print("tiempo carga solucion: ", time()-tiempoIni)
        self.c = None

        if idInstancia is not None:
            self.idInstancia = idInstancia
        if criterioTenure is not None:
            self.criterioTenure = criterioTenure
        if coordenadas is not None:
            self.coord = coordenadas
        
        self.conn = DB.DB()
        #self.tabuSearch()
        self.swaps = [0]*4
        self.__swapOptimoLocal = []   #tipo de swap que usó para el óptimo local N
        self.__iteracionOptimoLocal = []          #iteración en la que se encontró el optimo local
        if cargarEnDB is None:
            self.cargarEnDB = False
        else:
            self.cargarEnDB = cargarEnDB

        if cantidad is not None and orden is not None:
            if cantidad is not None:
                self.cantidad = cantidad
            
            if orden is not None:
                self.orden = orden
            self.usarBarra = True
        else:
            self.usarBarra = False

        if indBarra is not None:
            self.indBarra = indBarra

    def getRutas(self):
        return self.__rutas

    def setHilo(self,H):
        self.hilo = H

    #Escribe los datos iniciales: el grafo inicial y la demanda
    def escribirDatos(self):
        self.__txt.escribir("+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ GRAFO CARGADO +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-")
        #self.__txt.escribir(str(self._G))
        cad = "\nDemandas:"
        for v in self._G.getV():
            cad_aux = str(v)+": "+str(v.getDemanda())
            cad+="\n"+ cad_aux
        self.__txt.escribir(cad)
        print("\n+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ GRAFO CARGADO +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-")
        print("Nro vehiculos: ",self.__nroVehiculos)
        self.__txt.escribir("+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ SOLUCION INICIAL +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-")

    #Carga la solucion general a partir de las rutas
    def cargaSolucion(self, rutas):
        # t = time()
        S = Solucion(self.__Distancias, self.__Demandas, sum(self.__Demandas),self._G,True)
        cap = 0
        costoTotal = 0
        sol_ini = ""
        
        #print("+-+-++-+-++-+-++-+-+Rutas+-+-++-+-++-+-++-+-+")
        for i in range(0, len(rutas)):
            s = rutas[i]
            try:
                costoTotal += float(s.getCostoAsociado())
            except AttributeError:
                print("s: "+str(s))
                print("rutas: "+str(rutas))
                print("i: ", i)
                #a = 1/0
            cap += s.getCapacidad()
            S.getA().extend(s.getA())
            S.getV().extend(s.getV())
            sol_ini+="\nRuta #"+str(i+1)+": "+str(s.getV())
            #sol_ini+="\nAristas: "+str(s.getA())
            sol_ini+="\nCosto asociado: "+str(s.getCostoAsociado())+"      Capacidad: "+str(s.getCapacidad())+"\n"
        sol_ini+="\n--> Costo total: "+str(costoTotal)+"          Capacidad total: "+str(cap)
        # print(sol_ini)
        # print("+-+-++-+-++-+-++-+-++-+-++-+-++-+-++-+-+")
        costoTotal = round(costoTotal, 5)
        S.setCostoAsociado(costoTotal)
        S.setCapacidad(cap)
        S.setCapacidadMax(self.__capacidadMax)
        # print(f"cargaSolucion: {time()-t}")
        return S, sol_ini

    def enviarRutasHilo(self,rutas,indRutas=None):
        if indRutas is None:
            return self.hilo.signals.rutaLista.emit(rutas)
        return self.hilo.signals.ruta.emit({'rutas':rutas,"indRutas": indRutas})

    def enviarProgreso(self, tiempoTotal, tiempoTranscurrido):
        """Se envía la señal de progreso teniendo en cuenta el total del progreso"""
        if self.usarBarra:
            progreso = (tiempoTotal * self.orden + tiempoTranscurrido)/(tiempoTotal * self.cantidad)
            if int(progreso)*100 % 2 == 0:
                if self.hilo is not None:
                    return self.hilo.signals.valorBarra.emit((progreso, self.indBarra))

    #Umbral de granularidad: phi = Beta*(c/(n+k))
    #Beta = 1  parametro de dispersion. Sirve para modificar el grafo disperso para incluir la diversificación y la intensificación
    #          durante la búsqueda.
    #c = valor de una sol. inicial
    #k = nro de vehiculos
    #n = nro de clientes
    def calculaUmbral(self, costo):
        c = costo
        k = self.__nroVehiculos
        n = len(self.__Distancias)-1
        phi = c/(n+k)
        phi = phi*self.__beta
        return round(phi,3)

    """
    +-+-+-+-+-+-+- Empezamos con Tabu Search +-+-+-+-+-+-+-+-+
    lista_tabu: tiene objetos de la clase Tabu (una arista con su tenure)
    Lista_permitidos: o grafo disperso tiene elementos del tipo Arista que no estan en la lista tabu y su distancia es menor al umbral
    nuevas_rutas: nuevas rutas obtenidas a partir de los intercambios
    nueva_solucion: nueva solucion obtenida a partir de los intercambios
    rutas_refer: rutas de referencia que sirve principalmente para evitar estancamiento, admitiendo una solucion peor y hacer los intercambios
    a partir de esas
    solucion_refer: idem al anterior
    tiempoIni: tiempo inicial de ejecucion - tiempoMax: tiempo maximo de ejecucion - tiempoEjecuc: tiempo de ejecución actual
    iteracEstancamiento: iteraciones de estancamiento para admitir una solución peor, modificar Beta y escapar del estancamiento
    iterac: cantidad de iteraciones actualmente
    """
    def tabuSearch(self):
        lista_tabu = ListaTabu()
        ind_permitidos = np.array([], dtype = int)
        rutas_refer = copy.deepcopy(self.__rutas)
        nuevas_rutas = rutas_refer
        solucion_refer = copy.deepcopy(self.__S)
        nueva_solucion = solucion_refer
        nuevo_costo = self.__S.getCostoAsociado()
        S = []
        G = []

        #Atributos de tiempo e iteraciones
        tiempoIni = time()
        tiempoMax = float(self.__tiempoMaxEjec*60)
        tiempoEstancamiento = tiempoIni
        tiempoEjecuc = 0
        iteracEstancamiento = 1
        #iteracEstancamiento_Opt = 1
        iteracPeorSol = 0

        if len(self.__Distancias) < 100:
            iteracEstancMax = 300
        elif len(self.__Distancias) < 200:
            iteracEstancMax = 400
        elif len(self.__Distancias) < 500:
            iteracEstancMax = 500
        elif len(self.__Distancias) < 1000:
            iteracEstancMax = 700
        else:
            iteracEstancMax = 800

        iterac = 1
        indOptimosLocales = -2
        umbral = self.calculaUmbral(self.__S.getCostoAsociado())
        cond_Optimiz = True
        cond_Estancamiento = False
        condPathRelinking = False
        condEstancPathRelinking = True
        condPeorSolucionNueva = False
        #costoAux = None
        iteracEstancamientoPR = 0
        tiempo = time()
        Aristas_Opt = np.array([], dtype = object)
        for EP in self._G.getA():
            if(EP.getOrigen().getValue() < EP.getDestino().getValue() and EP.getPeso() <= umbral):
                Aristas_Opt = np.append(Aristas_Opt, EP)
                ind_permitidos = np.append(ind_permitidos, EP.getId())
        ind_AristasOpt = copy.deepcopy(ind_permitidos)
        print("Tiempo get AristasOpt: "+str(time()-tiempo))
        
        self.almacenarOptimoLocal(nuevas_rutas, iterac, [0,0])

        porcentaje = round(self.__S.getCostoAsociado()/self.__optimo -1.0, 3)
        print("Costo sol Inicial: "+str(self.__S.getCostoAsociado())+"      ==> Optimo: "+str(self.__optimo)+"  Desvio: "+str(round(porcentaje*100,3))+"%")
        
        while(tiempoEjecuc < tiempoMax and porcentaje*100 > self.__porcentajeParada):
            if(cond_Optimiz):
                ind_permitidos = self.getPermitidos(Aristas_Opt, umbral, solucion_refer)    #Lista de elementos que no son tabu
                self.__umbralMin = 0
            cond_Optimiz = False
            ADD = []
            DROP = []
            
            ind_random = np.arange(0,len(ind_permitidos))
            random.shuffle(ind_random)
            
            #Evaluar si un movimiento trae consigo una mejor solución
            indRutas = indAristas = []
            nuevo_costo, k_Opt, indRutas, indAristas, aristasADD, aristasDROP, ind_permitidos = nueva_solucion.evaluarOpt(self._G.getA(), ind_permitidos, ind_random, rutas_refer, cond_Estancamiento)
            nuevo_costo = round(nuevo_costo, 5)

            tenureADD = self.__tenureADD
            tenureDROP = self.__tenureDROP
            
            costoSolucion = round(self.__S.getCostoAsociado(), 5)
            
            #Si encontramos una mejor solucion que la tomada como referencia
            if(nuevo_costo < solucion_refer.getCostoAsociado() and aristasADD != []):
                nuevas_rutas = nueva_solucion.swap(k_Opt, aristasADD[0], rutas_refer, indRutas, indAristas)
                nueva_solucion, strText = self.cargaSolucion(nuevas_rutas)
                rutas_refer = nuevas_rutas
                solucion_refer = nueva_solucion
                porcentaje = round(nuevo_costo/self.__optimo -1.0, 3)

                #Si la nueva solucion es mejor que la obtenida hasta el momento
                if(nuevo_costo < costoSolucion):
                    self.__S = nueva_solucion
                    self.__rutas = nuevas_rutas
                    self.__beta = 1
                    tiempoTotal = time()-tiempoEstancamiento
                    tiempoEstancamiento = time()

                    if len(self.__optimosLocales) >= 20 and len(self.__Distancias) > 500:
                        self.__optimosLocales.pop(0)
                    self.almacenarOptimoLocal(nuevas_rutas, iterac, k_Opt)

                    self.contarSwaps(k_Opt)
                    indOptimosLocales = -2
                    cond_Estancamiento = False
                    condPathRelinking = False
                    condEstancPathRelinking = True
                    iteracPeorSol = 0
                    self.escribirDatosActuales(nuevas_rutas, nuevo_costo, k_Opt, tiempoEstancamiento, aristasADD, aristasDROP, iterac, strText)

                umbral = self.calculaUmbral(nueva_solucion.getCostoAsociado())
                tenureADD = self.__tenureMaxADD
                tenureDROP = self.__tenureMaxDROP
                cond_Optimiz = True
                iteracEstancamiento = 1
                # iteracEstancMax = 300
            
            #Si se estancó, tomamos a beta igual a 2
            elif(iteracEstancamiento > iteracEstancMax and self.__beta < 2  and ind_permitidos != []):
                tiempoTotal = time()-tiempoEstancamiento
                print("Se estancó durante %d min %d seg. Incrementanos Beta para diversificar" %(int(tiempoTotal/60), int(tiempoTotal%60)))
                self.__beta = 2
                self.__umbralMin = umbral
                umbral = self.calculaUmbral(nueva_solucion.getCostoAsociado())
                cond_Optimiz = True
                #cond_Estancamiento = True
                iteracEstancamiento = 1
                # iteracEstancMax = 300
                
            #Si se estancó con la sol anterior y el Beta incrementado, aplicamos Path Relinking
            elif iteracEstancamiento > iteracEstancMax and len(self.__optimosLocales) >= indOptimosLocales*(-1) and ind_permitidos != [] and not condPeorSolucionNueva:
                cad = "\n+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+- Iteracion %d  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-\n" %(iterac)
                self.__txt.escribir(cad)

                if condPathRelinking or not condEstancPathRelinking:
                    if iteracEstancamientoPR < 5:
                        nuevas_rutas = self.pathRelinking(S, G)
                    else:
                        nuevas_rutas = []

                    if(nuevas_rutas == []):
                        condEstancPathRelinking = True
                        condPathRelinking = False
                    else:
                        condEstancPathRelinking = False
                        condPathRelinking = True
                        nueva_solucion, strText = self.cargaSolucion(nuevas_rutas)
                        self.__txt.escribir(strText)
                        costo = nueva_solucion.getCostoAsociado()
                        tiempoTotal = time()-tiempoEstancamiento
                        cad = "Se estancó durante %d min %d seg. Aplicamos path relinking para admitir otro optimo local" %(int(tiempoTotal/60), int(tiempoTotal%60))
                        print(cad + "-->    Costo: "+str(costo))
                    
                        self.__txt.escribir("\n"+cad)                
                        self.__beta = 4
                        self.__umbralMin = 0
                        iteracEstancamientoPR += 1

                if not condPathRelinking and condEstancPathRelinking:
                    S = copy.deepcopy(self.__optimosLocales[(-1)*indOptimosLocales - 1])
                    G = copy.deepcopy(self.__optimosLocales[indOptimosLocales+1])
                    
                    nuevas_rutas = self.__optimosLocales[indOptimosLocales]
                    nueva_solucion, strText = self.cargaSolucion(nuevas_rutas)
                    self.__txt.escribir(strText)
                    costo = nueva_solucion.getCostoAsociado()

                    self.__umbralMin = 0
                    umbral = self.calculaUmbral(nueva_solucion.getCostoAsociado())

                    tiempoTotal = time()-tiempoEstancamiento
                    cad = "Se estancó durante %d min %d seg. Admitimos el penultimo optimo local " %(int(tiempoTotal/60), int(tiempoTotal%60))
                    print("\n"+ cad + "-->    Costo: "+str(costo))
                    self.__txt.escribir("\n"+cad)

                    indOptimosLocales -= 1
                    self.__beta = 4
                    condPathRelinking = True
                    condEstancPathRelinking = False
                    cond_Estancamiento = False
                    iteracEstancamientoPR = 0

                    iteracPeorSol += 1
                    if iteracPeorSol == 2:
                        condPeorSolucionNueva = True
                        iteracPeorSol = 0


                if(len(self.__optimosLocales)-1 <= indOptimosLocales*(-1)):
                    print("\nReiniciamos la lista de Optimos Locales\n")
                    condPathRelinking = False
                    condEstancPathRelinking = True
                    iteracEstancamientoPR = 0
                    indOptimosLocales = -2

                lista_tabu.limpiarLista()
                ind_permitidos = ind_AristasOpt
                umbral = self.calculaUmbral(costo)
                solucion_refer = nueva_solucion
                rutas_refer = nuevas_rutas
                cond_Optimiz = True
                iteracEstancamiento = 1
                # iteracEstancMax = 300
                # cond_Estancamiento = True

            #Si se estancó con path Relinking tomamos el proximo peor
            elif iteracEstancamiento > iteracEstancMax and aristasADD != [] and ind_permitidos != []:
                tiempoTotal = time()-tiempoEstancamiento
                print("Se estancó durante %d min %d seg. Tomamos la primera solucion peor" %(int(tiempoTotal/60), int(tiempoTotal%60)))
                
                nuevas_rutas = nueva_solucion.swap(k_Opt, aristasADD[0], rutas_refer, indRutas, indAristas)
                nueva_solucion, strText = self.cargaSolucion(nuevas_rutas)
                rutas_refer = nuevas_rutas
                solucion_refer = nueva_solucion
            
                self.__beta = 5
                self.__umbralMin = 0
                umbral = self.calculaUmbral(nueva_solucion.getCostoAsociado())
                tenureADD = self.__tenureMaxADD
                tenureDROP = self.__tenureMaxDROP
                cond_Optimiz = True
                iteracEstancamiento = 1
                # iteracEstancMax = 300
                # indOptimosLocales = -2
                condPeorSolucionNueva = False

            #Si se terminaron los permitidos
            elif(ind_permitidos == []):
                cad = "\n+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+- Iteracion %d  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-\n" %(iterac)
                cad += "Se terminaron los permitidos"
                self.__txt.escribir(cad)
                nuevas_rutas = nueva_solucion.swap(k_Opt, aristasADD[0], rutas_refer, indRutas, indAristas)
                nueva_solucion, strText = self.cargaSolucion(nuevas_rutas)
                self.__txt.escribir(strText)
                solucion_refer = nueva_solucion
                rutas_refer = nuevas_rutas
                umbral = self.calculaUmbral(nueva_solucion.getCostoAsociado())
                cond_Optimiz = True
                self.__beta = 3
                lista_taba.limpiarLista()
                ind_permitidos = ind_AristasOpt
                # Aristas = Aristas_Opt
                umbral = self.calculaUmbral(costo)
            
            #Si no pasa nada, tomamos la ruta y sol de referencia
            else:
                nuevas_rutas = rutas_refer
                nueva_solucion = solucion_refer


            #Añado y elimino de la lista tabu
            if (aristasADD != []):
                lista_tabu.agregarTabues(aristasADD, self.__tenureADD)
                lista_tabu.agregarTabues(aristasDROP, self.__tenureDROP)
                lista_tabu.decrementaTenure(ind_permitidos)
            else:
                lista_tabu.limpiarLista()
                ind_permitidos = ind_AristasOpt
                # Aristas = Aristas_Opt
                cond_Optimiz = True
            
            tiempoEjecuc = time()-tiempoIni
            iterac += 1
            iteracEstancamiento += 1
            self.enviarProgreso(tiempoMax, tiempoEjecuc)

        #Fin del while. Imprimo los valores obtenidos
        self.escribirDatosFinales(tiempoIni, iterac, tiempoEstancamiento)
        
        if(self.cargarEnDB):
            self.enviarRutasHilo(rutas_refer)
            t = time()
            print("inicio carga base de datos")
            self.datosParaDB(iterac, tiempoEjecuc)
            print(f"tiempo en cargar en DB: {time()-t}")
        self.enviarProgreso(tiempoMax, tiempoMax)

    def datosParaDB(self, iterac, tiempo):
        s = self
        optimoEncontrado = self.__S.getCostoAsociado()
        porcentaje = optimoEncontrado/self.__optimo -1.0
        resolucion = (
            iterac,
            optimoEncontrado,
            s.__tenureADD,
            s.__tenureDROP,
            porcentaje*100,
            tiempo,
            json.dumps(s.swaps),
            s.__tipoSolucionIni,
            s.criterioTenure
            )
        idResolucion = DB.insert_resolucion(self.conn, resolucion)
        print("Id instancia: ", self.idInstancia)
        DB.insert_resolucionXInstancia(self.conn, (idResolucion, self.idInstancia))
        idSoluciones = []
        for i in range(len(self.__optimosLocales)):
            costo = sum([c.getCostoAsociado() for c in self.__optimosLocales[i]])
            rutas = []
            for r in self.__optimosLocales[i]:
                rutas.append(str(r.getV()))
            S = (
                costo,
                json.dumps(rutas),
                json.dumps(self.__swapOptimoLocal[i]),
                self.__iteracionOptimoLocal[i],
                json.dumps(self.__costosOptimosLocales[i])
            )
            idSol = DB.insert_solucion(self.conn, S)
            idSoluciones.append(idSol)

        for j in idSoluciones:
            DB.insert_solucionXResolucion(self.conn, (idResolucion,j)) 
      
    def getPermitidos(self, Aristas, umbral, solucion):
        AristasNuevas = []
        ind_permitidos = np.array([], dtype = int)
        claves = [hash(a) for a in solucion.getA()]
        dictA = dict(zip(claves,solucion.getA()))
        
        #No tengo en consideracion a las aristas que exceden el umbral y las que pertencen a S
        for EP in Aristas:
            pertS = False
            h = hash(EP)
            hInverso = hash(EP.getAristaInvertida())
            try:
                arista = dictA[h]
            except KeyError:
                arista = None

            try:
                aristaInv = dictA[hInverso]
            except KeyError:
                aristaInv = None 

            if arista is not None:
                pertS = True
                del dictA[h]

            if aristaInv is not None:
                pertS = True
                del dictA[hInverso]

            if(not pertS and self.__umbralMin <= EP.getPeso() and EP.getPeso() <= umbral):
                AristasNuevas.append(EP)
                ind_permitidos = np.append(ind_permitidos, EP.getId())
        #ind_permitidos = np.unique(ind_permitidos)

        return ind_permitidos

    def getVariacionTenure(self, variacionADD, variacionDROP):
        """
            Retorna una tupla con la variación del ternuer ADD y DROP
        """
        return self.__tenureADD*variacionADD, self.__tenureDROP*variacionDROP
    
    def pathRelinking(self, S, G):
        '''
        (con mismo tamaño)
        Antes:
        S -> r1: 1-2-3-4-5   r2: 1-6-7-8-9-10
        G -> r1: 1-2-5-4-6   r2: 1-3-9-10-7-8
        Despues:
        S -> r1: 1-2-5-4-3   r2: 1-6-7-8-9-10
        G -> r1: 1-2-5-4-6   r2: 1-3-9-10-7-8
        (con distinto tamaño)
        Antes:
        S -> r1: 1-2-3-4-5   r2: 1-6-7-8-9-10
        G -> r1: 1-2-5-4     r2: 1-3-9-10-7-8-6
        Despues:
        S -> r1: 1-2-5-4-3   r2: 1-6-7-8-9-10
        G -> r1: 1-2-5-4     r2: 1-3-9-10-7-8-6
        '''
        #indS e indG = [Ri, Vi] mostraran el indice de la 1ra ruta y el 1er vertice el cual difieran
        #IndDistTam: indica la primera ruta de S que tiene un distinto
        #sigIndS: el ind del vertice de S para realizar el swap
        #rutasInfactibles: conjunto de indices de las rutas que son infactibles
        esFactible = False
        igualRec = False
        indDistTam = -1    
        sigIndS = [0, 1]
        indS = [0, 1]
        indG = [0, 1]
        newS = []
        rutasInfactibles = set()
        indDistTam = self.igualesTam(S, G, indDistTam)
        
        if not igualRec:
            igualRec, indS, indG = self.igualesRec(S, G, indS, indG)
            
        while not esFactible:    
            #No son de igual recorrido
            if not igualRec:
                V_S = S[indS[0]].getV()
                V_G = G[indG[0]].getV()
                sigIndS = self.buscarSigVertice(S, G[indG[0]].getV()[indG[1]])
                
                #Si los vertices a cambiar de S pertenecen a la misma ruta
                if sigIndS[0] == indS[0]:
                    aristaAux = copy.copy(V_S[indS[1]])
                    V_S[indS[1]] = V_G[indG[1]]
                    V_S[sigIndS[1]] = aristaAux
                    capS = S[indS[0]].cargarDesdeSecuenciaDeVertices(V_S)
                    S[indS[0]].setCapacidad(capS)
                    if rutasInfactibles == set():
                        esFactible = True
                
                #No pertenecen a la misma ruta
                else:
                    newS, esFactible, rutasInfactibles = self.__S.swap_4optPR(indS[0], sigIndS[0], indS[1], sigIndS[1], S, rutasInfactibles)
                    
                    if esFactible and rutasInfactibles == set():
                        esFactible = True
                        S = newS
                    else:
                        esFactible = False
                    
                igualRec, indS, indG = self.igualesRec(S, G, indS, indG)
            
            #Son de igual recorrido
            else:          
                if rutasInfactibles == set():
                    esFactible = True

                if indDistTam == -1:
                    esFactible = True
                    break

                ind = indDistTam
                V_S = S[ind].getV()
                proxInd = ind+1
                V_sigS = S[proxInd].getV()
                
                #S: 1-2-3       1-4-5-6-7
                #G: 1-2-3-4-5   1-6-7
                if len(G[ind].getV()) > len(S[ind].getV()):
                    while len(V_sigS) == 1:
                        proxInd+=1
                        V_sigS = S[proxInd].getV()
                    try:
                        aristaAux = V_sigS.pop(1)
                    except IndexError:
                        print("V_sigS: "+str(V_sigS))
                        print("S: "+str(S))
                        print("G: "+str(G))
                        indDistTam == -1
                        break
                    V_S.append(aristaAux)
                
                #S: 1-2-3-4-5  1-6-7
                #G: 1-2-3      1-4-5-6-7
                else:
                    aristaAux = V_S.pop(-1)
                    V_sigS.insert(1, aristaAux)
                
                capS = S[ind].cargarDesdeSecuenciaDeVertices(V_S)
                S[ind].setCapacidad(capS)
                
                capSigS = S[proxInd].cargarDesdeSecuenciaDeVertices(V_sigS)
                S[proxInd].setCapacidad(capSigS)
                
                if capS > self.__capacidadMax or capSigS > self.__capacidadMax:
                    if capS > self.__capacidadMax:
                        rutasInfactibles = rutasInfactibles | set({ind})
                    else:
                        rutasInfactibles = rutasInfactibles - set({ind})

                    if capSigS > self.__capacidadMax:
                        rutasInfactibles = rutasInfactibles | set({ind+1})
                    else:
                        rutasInfactibles = rutasInfactibles - set({ind+1})
                else:
                    rutasInfactibles = rutasInfactibles - set({ind, ind+1})
                
                indDistTam = self.igualesTam(S, G, indDistTam)

        return [] if (indDistTam == -1 and igualRec) else S

    #Son de iguales Tamaño y/o Recorrido (ale: Calcula a partir de que ruta son de distinto tamaño >:V)
    def igualesTam(self, S, G, indDistTam):
        i = 0
        
        while i < self.__nroVehiculos:
            S_V = S[i].getV()
            G_V = G[i].getV()
            lenSV = len(S_V)
            lenGV = len(G_V)
            if lenSV != lenGV:
                indDistTam = i
                break
            i+=1
        
        return indDistTam if i < self.__nroVehiculos else -1

    def igualesRec(self, S, G, indS, indG):
        igualRec = True
        
        while igualRec and indS!=None and indG!=None:
            S_V = S[indS[0]].getV()
            G_V = G[indG[0]].getV()
            lenSV = len(S_V)
            lenGV = len(G_V)
            
            if S_V[indS[1]] != G_V[indG[1]]:
                #print("S_V: "+str(S_V))
                #print("G_V: "+str(G_V))
                igualRec = False
            else:
                indS = self.incInd(indS, lenSV)
                indG = self.incInd(indG, lenGV)

            # print("indS: "+str(indS))
            # print("indG: "+str(indG))

        return igualRec, indS, indG

    def getRutasInfact(self, S, indInfact):
        i = indInfact
        
        while i < self.__nroVehiculos:
            if S[i].getCapacidad() > self.__capacidadMax:
                break
            i+=1
        
        return i if i < self.__nroVehiculos else -1

    def incInd(self, ind, lenV):
        #indS
        #print("ind: "+str(ind))
        if ind[1]+1 < lenV:
            ind[1]+=1
            #print("ind: "+str(ind))
            return ind
        elif ind[0]+1 < self.__nroVehiculos:
            ind[0]+=1
            ind[1]=1
            #print("ind: "+str(ind))
            return ind
        else:
            return None #es el último de la secuencia
    
    def buscarSigVertice(self, S, vertG):
        sigIndS = [0,1]
        # print("Vert G: "+str(vertG))
        # print("S: "+str(S))
        while sigIndS != None:
            lenVS = len(S[sigIndS[0]].getV())
            vertS = S[sigIndS[0]].getV()[sigIndS[1]]
            #print("vertS: "+str(vertS))
            if  vertS == vertG:
                return sigIndS
            sigIndS = self.incInd(sigIndS, lenVS)
            #print("ind: "+str(sigIndS))
        print("No encontre el vertice")
        print(S)
        print(vertG)
        a = 1/0
    
    def escribirDatosActuales(self, nuevas_rutas, nuevo_costo, k_Opt, tiempoEstancamiento, aristasADD, aristasDROP, iterac, strText = None):
        cad = "\n+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+- Iteracion %d  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-\n" %(iterac)
        self.__txt.escribir(cad)
        if strText is not None:
            self.__txt.escribir(strText)

        porcentaje = round(nuevo_costo/self.__optimo -1.0, 3)
        if porcentaje < round(nuevo_costo/self.__optimo -1.0, 3):
            print("rutas: "+str(self.__rutas))
            print("Nuevas rutas: "+str(nuevas_rutas))
            print("%d_Opt Opcion: %d" %(k_Opt[0], k_Opt[1]))
        
        tiempoTotal = time()-tiempoEstancamiento
        print(cad)
        cad = "\nLa solución anterior duró " + str(int(tiempoTotal/60))+"min "+ str(int(tiempoTotal%60))
        cad += "seg    -------> Nuevo optimo local. Costo: "+str(nuevo_costo)
        cad += "       ==> Optimo: "+str(self.__optimo)+"  Desvio: "+str(porcentaje*100)+"%"
        #cad += "\n\nLista tabu: "+str(lista_tabu)
        self.__txt.escribir(cad)
        self.__txt.escribir("\n%d-Opt Opcion: %d" %(k_Opt[0], k_Opt[1]))
        self.__txt.escribir("ADD: "+str(aristasADD))
        self.__txt.escribir("DROP: "+str(aristasDROP))
        print(cad)
        return cad

    def escribirDatosFinales(self, tiempoIni, iterac, tiempoEstancamiento):
        tiempoTotal = time() - tiempoIni
        print("\nMejor solucion obtenida: "+str(self.__rutas))
        print("\nTermino!! :)")
        print("Tiempo total: " + str(int(tiempoTotal/60))+"min "+str(int(tiempoTotal%60))+"seg\n")
        self.__txt.escribir("\n+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+- Solucion Optima +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-")
        sol_ini = ""
        for i in range(0, len(self.__rutas)):
            sol_ini+="\nRuta #"+str(i+1)+": "+str(self.__rutas[i].getV())
            sol_ini+="\nCosto asociado: "+str(self.__rutas[i].getCostoAsociado())+"      Capacidad: "+str(self.__rutas[i].getCapacidad())+"\n"
        self.__txt.escribir(sol_ini)
        porcentaje = round(self.__S.getCostoAsociado()/self.__optimo -1.0, 3)
        self.__txt.escribir("\nCosto total:  " + str(self.__S.getCostoAsociado()) + "        Optimo real:  " + str(self.__optimo)+
                            "      Desviación: "+str(porcentaje*100)+"%")
        self.__txt.escribir("\nSolucion inicial: "+str(self.__solInicial[self.__tipoSolucionIni]))
        self.__txt.escribir("Cantidad de iteraciones: "+str(iterac))
        self.__txt.escribir("Nro de clientes: "+str(len(self.__Distancias)-1))
        self.__txt.escribir("Nro de vehiculos: "+str(self.__nroVehiculos))
        self.__txt.escribir("Capacidad Maxima/Vehiculo: "+str(self.__capacidadMax))
        self.__txt.escribir("Tiempo total: " + str(int(tiempoTotal/60))+"min "+str(int(tiempoTotal%60))+"seg")
        tiempoTotal = time()-tiempoEstancamiento
        self.__txt.escribir("Tiempo de estancamiento: "+str(int(tiempoTotal/60))+"min "+str(int(tiempoTotal%60))+"seg")
        self.__txt.imprimir()

    def contarSwaps(self,k_Opt):
        swap = k_Opt[0]
        if(swap == 2):
            self.swaps[0]+=1
        elif(swap == 3):
            self.swaps[1]+=1
        elif(swap == 4):
            self.swaps[2]+=1
        elif(swap == 5):
            self.swaps[3]+=1

    def almacenarOptimoLocal(self, OL, iteracion, swap):
        self.__optimosLocales.append(OL)
        self.__swapOptimoLocal.append(swap)
        self.__iteracionOptimoLocal.append(iteracion)
        costos = [x.getCostoAsociado() for x in OL]
        self.__costosOptimosLocales.append(costos)

    def eliminarOptimoLocal(self, indice):
        self.__optimosLocales.pop(indice)
        self.__swapOptimoLocal.pop(indice)
        self.__iteracionOptimoLocal.pop(indice)

