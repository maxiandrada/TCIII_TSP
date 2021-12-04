import numpy as np
class Tabu:
    def __init__(self, E, T):
        self.__elemento = E 
        self.__tenure = T
    
    def setElemento(self, E):
        self.__elemento = E
    
    def setTenure(self, T):
        self.__tenure = T
        
    def getElemento(self):
        return self.__elemento
    
    def getTenure(self):
        return self.__tenure

    def __eq__(self,E):
        return (self.getElemento() == E.getElemento())

    def __str__(self):
        return "("+str(self.__elemento)+","+str(self.__tenure)+")"  

    def __repr__(self):
        return "("+str(self.__elemento)+","+str(self.__tenure)+")" 
    
    def decrementaT(self):
        self.__tenure = self.__tenure -1
    
    def incrementaT(self):
        self.__tenure = self.__tenure +1


class ListaTabu:
    def __init__(self):
        self.__L = []

    def limpiarLista(self):
        self.__L.clear()
    
    def agregarTabu(self, T):
        """
            Agrega un elemento Tabú a la lista
        """
        self.__L.append(T)

    def agregarTabues(self, T, tenure):
        """
            Agrega a la lista Tabú una lista de Aristas
        """
        for t in T:
            self.__L.append(Tabu(t, tenure))
       

    def __getitem__(self, i):
        return self.__L[i]

    def decrementaTenure(self, ind_permitidos):
        """
            Decrementa el Tenure en caso de que no sea igual a -1. 
            Si luego de decrementar es 0, se elimina de la lista tabu
        """

        i=0
        while (i < len(self)):
            elemTabu = self.__L[i]
            elemTabu.decrementaT()
            if(elemTabu.getTenure()==0):
                ind_permitidos = np.append(ind_permitidos, elemTabu.getElemento().getId())
                self.__L.pop(i)
                i-=1
            i+=1

    def __len__(self):
        return len(self.__L)

    def __str__(self):
        return str(self.__L)