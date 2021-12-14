import sys
import os
import csv
import re
import ntpath
class clsTxt:
    def __init__(self, nombreTxt, Carpeta, paralelismo, Subcarpeta):
        print("clsTxt: ")
        nombreTxt = nombreArchivo(nombreTxt)
        Carpeta = Carpeta+"\Resultados"
        # CarpetaGral = Carpeta+"\Resultados"
        print("nombreTxt: "+nombreTxt)
        print("Carpeta: "+Carpeta)
        # print("CarpetaGral: "+CarpetaGral)
        print (re.findall(r"[0-9A-Za-z-]+.",nombreTxt))
        nombreCarpeta = re.findall(r"[0-9A-Za-z-]+.",nombreTxt)[0]
        nombreCarpeta = nombreCarpeta[:-1]
        print("nombreCarpeta: "+nombreCarpeta)            

        # if(os.path.exists(CarpetaGral)):
        #     self.__carpeta = CarpetaGral
        # else:
        #     os.mkdir(CarpetaGral)
        #     self.__carpeta = CarpetaGral

        if(os.path.exists(Carpeta)):
            self.__carpeta = Carpeta
        else:
            os.mkdir(Carpeta)
            self.__carpeta = Carpeta
        print(self.__carpeta)

        nombreCarpeta = self.__carpeta +"/"+nombreCarpeta
        print("nombreCarpeta2: "+nombreCarpeta)            
        
        if(os.path.exists(nombreCarpeta)):
            self.__nombre = "%s/%s" %(nombreCarpeta,nombreTxt)
        else:
            os.mkdir(nombreCarpeta)
            self.__nombre = "%s/%s" %(nombreCarpeta,nombreTxt)    
        
        i = 0
        while os.path.exists("%s (%i).txt" %(self.__nombre ,i)):
            i += 1
        self.__nombre = "%s (%i)" %(self.__nombre,i)
        self.__txt = open(str(self.__nombre)+".txt", "w")

        self.__st = ""
    
    def setTxtName(self, newname):
        os.rename(self.__nombre+".txt", newname+".txt")
        self.__nombre = newname

    def getTxtName(self):
        return self.__nombre

    def escribir(self, st):
        self.__st = self.__st + st+"\n"
    
    def CSV(self,iteracion,Vertices,Aristas,costo,intercambios,tenureADD,tenureDROP,tiempo):
        #self.__CSV.writerow({'iteración':str(iteracion),
        #'Vertices':str(Vertices),
        #'Aristas':str(Aristas),
        #'costo':str(costo),
        #"intercambios":str(intercambios),
        #"tenureADD":str(tenureADD),
        #"tenureDROP":str(tenureDROP),
        #"tiempo":str(tiempo)}) 
        pass

    def imprimir(self):
        try:
            print("nombre: "+self.__nombre)
            self.__txt = open(self.__nombre+".txt", "w")
            self.__txt.write(self.__st)
            self.__txt.close()
        except IOError:
            print ("No se pudo abrir el txt para imprimir")
    
def nombreArchivo(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)