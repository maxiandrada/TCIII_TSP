import re
import math
from time import time
from CVRP import CVRP
from Vertice import Vertice
import os
from os import listdir
from os.path import isfile, join
import ntpath
import DB
import sqlite3
import json
import numpy as np
import sys
import xlsxwriter
import csv
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize, QRunnable, pyqtSlot, QObject, pyqtSignal, QThread, QThreadPool
from PyQt5.QtGui import QPen, QBrush
from PyQt5.Qt import Qt
from PyQt5.QtGui import QDoubleValidator
import PySide2
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib as mpl
from pyqtgraph.Qt import QtGui
import pyqtgraph as pg

class Hilo(QThread):
    progreso = pyqtSignal(int)

    def run(self):
        contador = 0
        while contador < 100:
            contador += 1

            time.sleep(0.3)
            self.progreso.emit(contador)


class GUI(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        
        # Conexión base de datos
        self.conn = DB.DB()

        self.setMinimumSize(QSize(1000, 600))
        self.setWindowTitle("Capacited Vehicle Routing Problem - Tabu Search")

        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)


        self.criteriosTenure = ["sqrt(n)/2","10/% de n", "5% de n"]
        self.gridLayout = QGridLayout(self)
        self.centralWidget.setLayout(self.gridLayout)
        self.seleccionarProblema()
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1) #Para que ejecute un solo hilo
        self.rutasDict = {}
        print("Multithreading with maximum %d threads" %
              self.threadpool.maxThreadCount())

    def seleccionarProblema(self):

        # Layout's
        layoutPrincipal = QVBoxLayout()
        layoutTablaSets = QGridLayout()
        layoutAcciones = QHBoxLayout()
        layoutTablaInstancias = QGridLayout()
        # QGroups
        gBTablaSets = QGroupBox("Sets de Problemas")
        gBTablaInstancias = QGroupBox("Instancias")
        gBAcciones = QGroupBox("Acciones")

        gBTablaSets.setLayout(layoutTablaSets)
        gBAcciones.setLayout(layoutAcciones)
        gBTablaInstancias.setLayout(layoutTablaInstancias)

        # Botón para abrir ventana para cargar sets
        botonNuevoSet = QPushButton("Nuevo Set")
        botonNuevoSet.clicked.connect(self.ventanaCargaSet)

        # Botón para abrir ventana para cargar ventanas
        botonNuevaInstancia = QPushButton("Nueva Instancias")
        botonNuevaInstancia.clicked.connect(self.ventanaCargaInstancia)

        # Botón resolver instancia
        botonResolverInstancia = QPushButton("ResolverInstancia")
        botonResolverInstancia.clicked.connect(
            lambda: self.ventanaResolverInstancia())
        # Boton ver Resultados
        botonVerResultados = QPushButton("Ver Resultados")

        # Tabla Sets
        tablaSetProblema = QTableWidget()
        tablaSetProblema.setColumnCount(1)
        filasSets = DB.select_sets(self.conn)
        tablaSetProblema.setRowCount(len(filasSets))
        tablaSetProblema.setHorizontalHeaderLabels(['Nombre Set'])
        for i in range(len(filasSets)):
            tablaSetProblema.setItem(i, 0, QTableWidgetItem(filasSets[i][1]))
            tablaSetProblema.setColumnWidth(i, 200)
        tablaSetProblema.setSelectionBehavior(QTableView.SelectRows)
        tablaSetProblema.itemSelectionChanged.connect(
            lambda: self.establecerSetSeleccionado(tablaSetProblema, tablaInstancia))
        # Tabla Instancias
        tablaInstancia = QTableWidget()
        tablaInstancia.resizeColumnsToContents()
        tablaInstancia.setSelectionBehavior(QTableView.SelectRows)
        tablaInstancia.itemSelectionChanged.connect(
            lambda: self.establecerInstanciaSeleccionada(tablaInstancia))
        #Seleccionar primera fila en tablaInstancia
        tablaSetProblema.selectRow(0)
        tablaInstancia.selectRow(0)
        #Configuración de Layouts
        layoutTablaSets.addWidget(tablaSetProblema, 0, 0)
        layoutTablaSets.addWidget(botonNuevoSet, 1, 0)
        layoutTablaInstancias.addWidget(tablaInstancia, 0, 0)
        layoutTablaInstancias.addWidget(botonNuevaInstancia, 1, 0)
        layoutAcciones.addWidget(botonResolverInstancia)
        layoutAcciones.addWidget(botonVerResultados)

        botonVerResultados.clicked.connect(lambda: self.ventanaVerResultado(
            self.instanciaSeleccionada, tablaInstancia.item(tablaInstancia.currentRow(), 1).text()))

        #Acciones
        #Programar resolver un conjunto
        botonResolverConjunto = QPushButton("Resolver Conjunto")
        botonResolverConjunto.clicked.connect(self.resolverSetSeleccionado)
        botonReporteTotal = QPushButton("Reporte Total Resultados")
        botonReporteTotal.clicked.connect(lambda: self.reporte_total("XLSX"))
        layoutAcciones.addWidget(botonResolverConjunto)
        layoutAcciones.addWidget(botonReporteTotal)
        layoutPrincipal.addLayout(layoutTablaSets)
        layoutPrincipal.addLayout(layoutTablaInstancias)
        layoutPrincipal.addLayout(layoutAcciones)


        #self.gridLayout.addLayout(layoutPrincipal, 0, 0)
        self.gridLayout.addWidget(gBTablaSets, 0, 0)
        self.gridLayout.addWidget(gBTablaInstancias, 0, 1)
        self.gridLayout.addWidget(gBAcciones, 1, 0, 1, 2)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)

        gBTablaSets.setMaximumHeight(600)
        gBTablaSets.setMaximumWidth(210)
        gBTablaInstancias.setMaximumHeight(600)
        gBTablaInstancias.setMaximumWidth(800)
        gBAcciones.setMaximumWidth(700)

    def resolverSetSeleccionado(self):
        sets = []
        for s in self.setsSeleccionados:
            filas = DB.select_sets_con_nombre(self.conn, s.text())
            sets.extend(filas)
        instancias = []
        for s in sets:
            filas = DB.select_instanciaXSet(self.conn, s[0])
            instancias.extend(filas)
        #print("sets query: ", sets)
        #print("instancias query: ", instancias)
        self.programarResolucion(instancias)

    def aplicarCriterioTenure(self, criterio, n):
        if criterio == 0:
            return int(math.sqrt(n) / 2), int(math.sqrt(n) / 2)
        elif criterio == 1:
            return int(n*0.1), int(n*0.1)
        elif criterio == 2:
            return int(n*0.05), int(n*0.05)

    def programarResolucion(self, instancias):
        """
            Esta función es para prgramar las instancias
            a resolver, recibe como parámetro las instancias
            y se lo puede invocar desde distintas partes de la GUI
        """
        print("Instancias a resolver: ", instancias)

        ventanaProgramacion = QDialog(self)
        ventanaProgramacion.setWindowTitle("Resolver conjunto")
        ventanaProgramacion.setMinimumSize(QSize(590, 400))
        layoutPrincipal = QGridLayout()
        ventanaProgramacion.setLayout(layoutPrincipal)
        #Tabla para ver instancias a resolver
        tablaInstancias = QTableWidget()
        tablaInstancias.setColumnCount(5)
        tablaInstancias.setHorizontalHeaderLabels(["Nombre", "Clientes", "Vehículos", "Capacidad", "Progreso"])
        tablaInstancias.setRowCount(len(instancias))
        self.barrasCargaInstancia = []
        for i in range(len(instancias)):
            barra = QProgressBar()
            tablaInstancias.setItem(i, 0, QTableWidgetItem(instancias[i][1]))
            tablaInstancias.setItem(i, 1, QTableWidgetItem(instancias[i][2]))
            tablaInstancias.setItem(i, 2, QTableWidgetItem(instancias[i][3]))
            tablaInstancias.setItem(i, 3, QTableWidgetItem(instancias[i][5]))
            tablaInstancias.setCellWidget(i, 4, barra)
            self.barrasCargaInstancia.append(barra)

        layoutTabla = QGridLayout()
        layoutTabla.addWidget(tablaInstancias)
        gBTablaInstancias = QGroupBox("Instancias a Resolver")
        gBTablaInstancias.setLayout(layoutTabla)
        
        #Formularios
        layoutOpciones = QFormLayout()
        spinBoxCantidad = QSpinBox()
        tiempo = QLineEdit()
        tiempo.setText("1")
        layoutOpciones.addRow("Tiempo por Instancia", tiempo)
        tiempo.setValidator(QDoubleValidator(0.0, 100.0, 2))
        criterioTenure = QComboBox()
        criterioTenure.addItems(self.criteriosTenure)
        botonIniciar = QPushButton("Iniciar")
        cbSolucionInicial = QComboBox()
        cbSolucionInicial.addItems(["Clarke Wright", "Vecino Cercano", "Secuencial"])
        spPorcentaje = QSpinBox()
        checkBoxPorcenaje = QCheckBox()
        checkBoxConcurrente = QCheckBox()
        self.estadoParada = False
        checkBoxPorcenaje.stateChanged.connect(lambda: self.cambiarEstadoParada(layoutOpciones, checkBoxPorcenaje, 1))
        layoutOpciones.addRow("Cantidad de Veces a Resolver ", spinBoxCantidad)
        layoutOpciones.addRow("Criterio Tenure ", criterioTenure)
        layoutOpciones.addRow("Solución Inicial", cbSolucionInicial)
        layoutOpciones.addRow("Usar porcentaje como parada", checkBoxPorcenaje)
        layoutOpciones.addRow(botonIniciar)
        layoutPrincipal.addWidget(gBTablaInstancias, 0, 0)
        layoutPrincipal.addLayout(layoutOpciones, 1, 0)
        botonIniciar.clicked.connect(lambda: self.resolverCVRPMejorado(instancias,
                                                                       float(tiempo.text()),
                                                                       criterioTenure.currentIndex(),
                                                                       cbSolucionInicial.currentIndex(),
                                                                       spinBoxCantidad.value(),
                                                                       self.barrasCargaInstancia
                                                                       ))

        ventanaProgramacion.exec()

    def cambiarEstadoParada(self, layout, checkBox, posi):
        """Elimina o agrega el spinbox para el porcenaje, en la posición que se indica, con respecto al último"""
        cantidadElementos = layout.rowCount()
        if checkBox.isChecked():
            self.spinBoxParada = QSpinBox()
            layout.insertRow(cantidadElementos-posi, "Porcentaje de parada: ", self.spinBoxParada)
        else:
            layout.removeRow(self.spinBoxParada)


    def resolverCVRPMejorado(self, instancias, tiempo, criterioTenure, solucionInicial, cantidad, barras):
        if self.estadoParada == False:
            porcentaje = float("-inf")
        else:
            porcentaje = self.spinBoxParada.value()
        print("Se resolverá ", cantidad)
        print("Demandas: ", instancias[4])
        indBarra = 0
        for inst in instancias:
            instancia = DB.select_instancia(self.conn, inst[0])[0]
            print("Resolviendo: ", instancia)
            for _ in range(cantidad):
                print("cantidad ", _)
                idInstancia = instancia[0]
                n = instancia[2]
                k = instancia[3]
                D = json.loads(instancia[4])
                C = instancia[5]
                optimo = instancia[6]
                coordenadas = json.loads(instancia[7])
                M = self.cargaMatrizDistancias(coordenadas)
                tenureADD, tenureDROP = self.aplicarCriterioTenure(criterioTenure, n)
                cvrp = CVRP(
                    M,
                    D,
                    k,
                    C,
                    instancia[1]+"_"+str(tiempo)+"min",
                    os.getcwd(),
                    solucionInicial,
                    tenureADD,
                    tenureDROP,
                    tiempo,
                    porcentaje,
                    optimo,
                    True,#Este es para indicar de que cargue los datos en la DB
                    idInstancia,
                    criterioTenure, #Criterio que se tomó para calcular el tenure,
                    coordenadas,
                    cantidad=cantidad,
                    orden=_,
                    indBarra=indBarra
                )
                self.hiloGrafico = Worker(cvrp.tabuSearch)
                self.hiloGrafico.signals.valorBarra.connect(self.establecerProgresoBarra)
                cvrp.setHilo(self.hiloGrafico)
                self.threadpool.start(self.hiloGrafico)
            indBarra += 1

    def reporte_total(self, formato):
        encabezado = [
            "Nombre",
            "Nº Vehículos",
            "Cantidad Clientes",
            "Óptimo Promedio",
            "Mejor Óptimo",
            "Óptimo conocido",
            "Desvío Promedio",
            "Cantidad de veces resuelto"
        ]
        sets = DB.select_sets(self.conn)
        criterios = self.criteriosTenure
        if formato == "XLSX":
            XLSX = xlsxwriter.Workbook("Reporte Resultados.xlsx")
            hoja = XLSX.add_worksheet()
            dataFormat = XLSX.add_format({'bg_color': '#9fc5e8'})
            for j in range(len(encabezado)):
                hoja.write(0, j, encabezado[j])
            hoja.set_column(0, j, 17)
            hoja.set_row(0, cell_format=dataFormat)
            contadorFilas = 2
            contadorSets = 1
            for s in sets:
                print("Se escribió set", s)
                hoja.write(contadorSets, 0, s[1])
                hoja.set_row(contadorSets, cell_format=dataFormat)
                instancias = DB.select_instanciaXSet(self.conn, s[0])
                for i in instancias:
                    filas = DB.select_reporte_total(self.conn, i[0])
                    for elem in filas:
                        for k in range(len(elem)):
                            hoja.write(contadorFilas, k, elem[k])
                        contadorFilas += 1
                contadorSets = contadorFilas
                contadorFilas += 1
            XLSX.close()

    def establecerProgresoBarra(self, T):
        """Recibe una tupla, en la que el primer elemento es el progreso total de la instancia"""
        #print(f"tiempo: {T[0]}, barra: {T[1]}")

        self.barrasCargaInstancia[T[1]].setValue(T[0]*100)

    def ventanaCargaInstancia(self):
        # Definiciones
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        instancias, _ = QFileDialog.getOpenFileNames(
            self, "QFileDialog.getOpenFileNames()", "", "Archivos VRP (*.vrp)", options=options)
        if instancias:
            for i in instancias:
                self.cargarDesdeFile(i)
                filaInstancia = (self.nombreArchivo, int(self.cantidadClientes), self.__nroVehiculos, json.dumps(
                    self.__demanda), self.__capacidad, self.__optimo, json.dumps(self.coordenadas))

                # print(filaInstancia)
                idFila = DB.insert_instancia(self.conn, filaInstancia)
                setSeleccionado = self.setsSeleccionados[-1].text()
                setSeleccionado = DB.select_sets_con_nombre(self.conn, setSeleccionado)[0]
                # print(idFila)
                DB.insert_instanciaXSet(
                    self.conn, (idFila, int(setSeleccionado[0]))
                    )

    def ventanaCargaSet(self):
        # Definiciones
        ventanaCargarSet = QDialog(self)
        ventanaCargarSet.setWindowTitle("Cargar Nuevo Conjunto")
        ventanaCargarSet.setModal(True)
        layoutCargaSet = QGridLayout()

        labelNombreSet = QLabel("Ingresar Nombre Set")
        textEditNombreSet = QLineEdit()
        botonOK = QPushButton("OK")
        botonCancelar = QPushButton("Cancelar")

        # fijar en layout
        # Eventos
        botonOK.clicked.connect(lambda: self.cargarSetDB(textEditNombreSet.text(), ventanaCargarSet))
        botonCancelar.clicked.connect(lambda: ventanaCargarSet.close())

        layoutCargaSet.addWidget(labelNombreSet, 0, 0)
        layoutCargaSet.addWidget(textEditNombreSet, 0, 1)
        layoutCargaSet.addWidget(botonOK, 1, 0)
        layoutCargaSet.addWidget(botonCancelar, 1, 1)
        ventanaCargarSet.setLayout(layoutCargaSet)
        ventanaCargarSet.exec()

    def cargarSetDB(self, nombre, ventana):
        if(nombre != ""):
            # print("NOMBRE; ", nombre)
            DB.insert_set(self.conn, (nombre,))
            ventana.close()
        else:
            error_dialog = QErrorMessage()
            error_dialog.setWindowTitle("ERROR")
            error_dialog.showMessage('Debe ingresar un nombre')
            error_dialog.exec()

    def establecerSetSeleccionado(self, tabla, tablaInstancia):
        index = tabla.currentIndex()
        
        self.setSeleccionado = str(index.row()+1)
        self.setsSeleccionados = tabla.selectedItems()
        print("Sets Seleccionados: ", self.setsSeleccionados)
        for t in self.setsSeleccionados:
            print("Set :", t.text())
        print("Set Seleccionado: ", self.setSeleccionado)
        self.llenarTablaInstancias(tablaInstancia)

    def establecerInstanciaSeleccionada(self, tabla):
        #print("instancia Seleccionada: ", tabla.selectedItems())
        itemsSeleccionados = tabla.selectedItems()
        if len(itemsSeleccionados) != 0:
            self.instanciaSeleccionada = int(tabla.selectedItems()[0].text())
        else:
            self.instanciaSeleccionada = 0
        self.instanciasSeleccionadas = tabla.selectedItems()
        print("Instancia Seleccionada: ", self.instanciaSeleccionada)
        print("Instancias Seleccionadas: ", self.instanciasSeleccionadas)

    def llenarTablaInstancias(self, tablaInstancia):
        # Consulta a base de datos
        setSeleccionado = DB.select_sets_con_nombre(self.conn, self.setsSeleccionados[-1].text())[0]
        print("Set consulta: ", setSeleccionado)
        filasInstancias = DB.select_instanciaXSet(
            self.conn, setSeleccionado[0])
        tablaInstancia.setRowCount(len(filasInstancias))
        tablaInstancia.setColumnCount(6)
        tablaInstancia.setHorizontalHeaderLabels(
            ["ID Instancia", 'Nombre ', 'Clientes', "Vehículos", "Capacidad", "Óptimo Conocido"])
        for i in range(len(filasInstancias)):
            tablaInstancia.setItem(
                i, 0, QTableWidgetItem(str(filasInstancias[i][0])))
            tablaInstancia.setItem(
                i, 1, QTableWidgetItem(filasInstancias[i][1]))
            tablaInstancia.setItem(
                i, 2, QTableWidgetItem(str(filasInstancias[i][2])))
            tablaInstancia.setItem(
                i, 3, QTableWidgetItem(str(filasInstancias[i][3])))
            tablaInstancia.setItem(
                i, 4, QTableWidgetItem(str(filasInstancias[i][4])))
            tablaInstancia.setItem(
                i, 5, QTableWidgetItem(str(filasInstancias[i][5])))
        self.instanciaSeleccionada = filasInstancias[0][0]
        #tablaInstancia.selectRow(0)
        #tablaInstancia.setCurrentIndex(QtCore.QModelIndex().child(0,0))

    def ventanaResolverInstancia(self):
        instancia = DB.select_instancia(
            self.conn, self.instanciaSeleccionada)[0]
        print(instancia)
        ventanaResolverInstancia = QDialog(self)

        ventanaResolverInstancia.setWindowTitle("Resolviendo " + instancia[1])
        labelTitulo = QLabel(str(instancia[1]))
        labelTitulo.setFont(QtGui.QFont('Arial', 20))
        labelTitulo.setAlignment(QtCore.Qt.AlignCenter)
        layoutVRI = QGridLayout(ventanaResolverInstancia)
        ventanaResolverInstancia.setLayout(layoutVRI)
        layoutVRI.addWidget(labelTitulo, 0, 0)
        ventanaResolverInstancia.setGeometry(100, 100, 1100, 600)
        ventanaResolverInstancia.setMinimumSize(QSize(1000, 600))
        # Gráfico
        coordenadas = json.loads(instancia[7])
        self.grafico = self.graficoInstancia(layoutVRI, coordenadas, 1, 0)
        # Layout Vertical Derecha
        layoutV = QVBoxLayout()
        layoutVG = QFormLayout()
        layoutVRI.addLayout(layoutV, 0, 1, 2, 1)
        layoutBotones = QHBoxLayout()
        #GroupBox's
        gBDatosInstancia = QGroupBox("Datos Instancia")
        gBResolver = QGroupBox("Resolver")
        gBReportes = QGroupBox("Reportes")
        gBResolver.setLayout(layoutVG)
        layoutV.addWidget(gBDatosInstancia)
        layoutV.addWidget(gBResolver)
        layoutV.addWidget(gBReportes)
        layoutV.addLayout(layoutBotones)
        # Solución Inicial
        labelSolucionInicial = QLabel("Seleccione Solución Inicial")
        cbSolucionInicial = QComboBox()
        cbSolucionInicial.addItems(
            ["Clarke Wright", "Vecino Cercano", "Secuencial"])
        #Criterio Tenure
        cbCriterioTenure = QComboBox()
        cbCriterioTenure.addItems(self.criteriosTenure)
       # Tenures
        sbTenureADD = QSpinBox()
        criteriosTenure = self.aplicarCriterioTenure(cbCriterioTenure.currentIndex(), instancia[2])
        sbTenureADD.setValue(criteriosTenure[0])
        sbTenureDROP = QSpinBox()
        sbTenureDROP.setValue(criteriosTenure[1])
        cbCriterioTenure.currentIndexChanged.connect(
            lambda: self.establecerCriterioSeleccionado(cbCriterioTenure, sbTenureADD,sbTenureDROP, instancia[2]))
        # Tiempo ejecución
        labelTiempoEjecucion = QLabel("Tiempo Ejecución")
        leTiempoEjecucion = QLineEdit()
        leTiempoEjecucion.setValidator(QDoubleValidator(0.0, 100.0, 2))
        leTiempoEjecucion.setText("0.1")
        labelMinutos = QLabel("Minutos")
        # Porcentaje de parada
        labelParada = QLabel("Error respecto a óptimo conocido")
        sbParada = QSpinBox()
        # Boton resolver
        botonResolver = QPushButton("Resolver")
        botonVerResultados = QPushButton("Ver Resultados")

        layoutVG.addRow("Seleccionar Solución Inicial: ", cbSolucionInicial)
        layoutVG.addRow("Criterio Tenure ", cbCriterioTenure)
        layoutVG.addRow("Tenure ADD", sbTenureADD)
        layoutVG.addRow("Tenure DROP", sbTenureDROP)
        layoutVG.addRow("Tiempo en minutos", leTiempoEjecucion)
        layoutVG.addRow("Porcentaje de parada: ", sbParada)

        #Botones Grafico
        botonGraficoHistoria = QPushButton("Historia Instancias")
        botonGraficoHistoria.clicked.connect(lambda: self.graficarHistoriaInstancia(instancia))
        layoutBotones.addWidget(botonGraficoHistoria)

        layoutBotones.addWidget(botonResolver)
        layoutBotones.addWidget(botonVerResultados)

        resolver = lambda: self.resolverCVRP(instancia,
                                                        cbSolucionInicial,
                                                        sbTenureADD,
                                                        sbTenureDROP,
                                                        leTiempoEjecucion,
                                                        sbParada,
                                                        coordenadas,
                                                        self.conn,
                                                        cbCriterioTenure.currentIndex()
                                                        )
        botonResolver.clicked.connect(resolver)
        verResultados = lambda: self.ventanaVerResultado(instancia[0], instancia[1])
        botonVerResultados.clicked.connect(verResultados)
        ventanaResolverInstancia.show()

    def graficarHistoriaInstancia(self, instancia):
        """Se lo podría hacer sin necesidad de hacer este método, pero es para no realizar siempre esta consulta a la DB"""
        resoluciones = DB.select_resolucionesXInstancia(self.conn, instancia[0])
        print(resoluciones)
        self.graficoHistoria(resoluciones, instancia)

    def establecerCriterioSeleccionado(self, cbCriterioTenure, sbTenureADD, sbTenureDROP, n):
        criteriosTenure = self.aplicarCriterioTenure(cbCriterioTenure.currentIndex(), n)
        sbTenureADD.setValue(criteriosTenure[0])
        sbTenureDROP.setValue(criteriosTenure[1])

    def resolverCVRP(self, instancia, cbSolucionInicial, sbTenureADD, sbTenureDROP, leTiempoEjecucion, sbParada, coordenadas, db, criterioTenure):
        # Parámetros iniciales ingresados por el usuario
        solucionInicial = cbSolucionInicial.currentIndex()
        tenureADD = sbTenureADD.value()
        tenureDROP = sbTenureDROP.value()
        tiempo = float(leTiempoEjecucion.text())
        porcentaje = sbParada.value()
        # Datos de la instancia
        idInstancia = instancia[0]
        self.n = instancia[2]
        self.k = instancia[3]
        self.D = json.loads(instancia[4])
        self.C = instancia[5]
        optimo = instancia[6]
        self.coordenadas = json.loads(instancia[7])
        self.M = self.cargaMatrizDistancias(self.coordenadas)
        cvrp = CVRP(
            self.M,
            self.D,
            self.k,
            self.C,
            instancia[1]+"_"+str(tiempo)+"min",
            os.getcwd(),
            solucionInicial,
            tenureADD,
            tenureDROP,
            tiempo,
            porcentaje,
            optimo,
            True,#Este es para indicar de que cargue los datos en la DB
            idInstancia,
            criterioTenure, #Criterio que se tomó para calcular el tenure
            coordenadas=self.coordenadas
        )
        self.dibujarRutaInicial(cvrp.getRutas())
        self.hiloGrafico = Worker(cvrp.tabuSearch)
        self.hiloGrafico.signals.ruta.connect(self.dibujarRutasNuevas)
        self.hiloGrafico.signals.rutaLista.connect(self.dibujarRutaInicial)
        cvrp.setHilo(self.hiloGrafico)
        self.threadpool.start(self.hiloGrafico)
        self.dibujarRutaInicial(cvrp.getRutas())

    def datosParaDB(self, iterac, tiempo):
        s = self
        optimoEncontrado = self.__S.getCostoAsociado()
        porcentaje = optimoEncontrado/self.__optimo - 1.0
        resolucion = (
            iterac,
            optimoEncontrado,
            s.__tenureADD,
            s.__tenureDROP,
            porcentaje*100,
            tiempo,
            json.dumps(s.swaps),
            s.__tipoSolucionIni
        )
        idResolucion = DB.insert_resolucion(self.conn, resolucion)
        DB.insert_resolucionXInstancia(
            self.conn, (idResolucion, self.idInstancia))
        idSoluciones = []
        for i in range(len(self.__optimosLocales)):
            t = time()
            costo = sum([c.getCostoAsociado()
                         for c in self.__optimosLocales[i]])
            rutas = []
            for r in self.__optimosLocales[i]:
                rutas.append(str(r.getV()))
            S = (
                costo,
                json.dumps(rutas),
                json.dumps(self.__swapOptimoLocal[i]),
                self.__iteracionOptimoLocal[i],
            )
            idSol = DB.insert_solucion(self.conn, S)
            idSoluciones.append(idSol)

        for j in idSoluciones:
            DB.insert_solucionXResolucion(self.conn, (idResolucion, j))

    def ventanaVerResultado(self, instanciaId, nombreInstancia):
        instancia = DB.select_instancia(self.conn, str(instanciaId))[0]
        ventanaResultados = QDialog(self)

        # QBox
        gBResultados = QGroupBox("Resultados")
        gBGrafico = QGroupBox("Grafico")
        gBAcciones = QGroupBox("Acciones")
        gBSoluciones = QGroupBox("Soluciones")

        ventanaResultados.setWindowTitle("Resultados" + nombreInstancia)
        layoutPrincipal = QGridLayout()
        layoutAcciones = QGridLayout()
        layoutResultados = QHBoxLayout()
        layoutGrafico = QVBoxLayout()
        layoutSoluciones = QVBoxLayout()

        # layoutResultados.addLayout(layoutGrafico)
        # Grafico
        graficoSoluciones = pg.PlotWidget()
        botonSolInicial = QPushButton("Solución Inicial")
        botonSolAnterior = QPushButton("<")
        botonSolSiguiente = QPushButton(">")
        botonSolFinal = QPushButton("Solución Final")
        # Botones para ver soluciones
        layoutBotones = QHBoxLayout()
        layoutBotones.addWidget(botonSolInicial)
        layoutBotones.addWidget(botonSolAnterior)
        layoutBotones.addWidget(botonSolSiguiente)
        layoutBotones.addWidget(botonSolFinal)
        layoutGrafico.addWidget(graficoSoluciones)
        # Layout botones para ver solucion
        layoutGrafico.addLayout(layoutBotones)
        #Botones Acciones

        # Tabla Resoluciones
        tablaResoluciones = QTableWidget()
        self.llenarTablaResoluciones(tablaResoluciones, instanciaId)
        # TreeView Resultados
        treeSoluciones = QTreeWidget()
        layoutSoluciones.addWidget(treeSoluciones)
        treeSoluciones.setHeaderLabels(['Iteración', 'Costo', "Origen"])
        treeSoluciones.itemClicked.connect(lambda: self.establecerSolucionSeleccionada(
                                        graficoSoluciones,
                                        instancia[7],
                                        treeSoluciones,
                                        instancia[3])
                                    )
        # Eventos de Tabla Resoluciones
        tablaResoluciones.resizeRowToContents(5)
        tablaResoluciones.setSelectionBehavior(QTableView.SelectRows)
        tablaResoluciones.itemSelectionChanged.connect(
            lambda: self.establecerResolucionSeleccionada(tablaResoluciones,
                                                          treeSoluciones,
                                                          graficoSoluciones,
                                                          instancia))
        layoutTablas = QVBoxLayout()
        layoutTablas.addWidget(tablaResoluciones)
        #Seleccionar Filas
        tablaResoluciones.selectRow(0)
        self.establecerResolucionSeleccionada(tablaResoluciones,
                                              treeSoluciones,
                                              graficoSoluciones,
                                              instancia)
        self.seleccionarPrimerFilaTW(treeSoluciones, graficoSoluciones, instancia)
        #Acciones
        botonAbrirTxt = QPushButton("Subir Txt")
        botonAbrirTxt.clicked.connect(lambda: self.abrirYCargarTxt(tablaResoluciones, instancia[0]))
        # Eventos Botones
        #Botonones para navegar entre las distintas soluciones
        args = (
            treeSoluciones,
            graficoSoluciones,
            instancia
        )
        botonSolInicial.clicked.connect(lambda: self.seleccionarPrimerFilaTW(*args))
        botonSolFinal.clicked.connect(lambda: self.seleccionarUltimaFilaTW(*args))
        botonSolAnterior.clicked.connect(lambda: self.seleccionarFilaTW(*args, "anterior"))
        botonSolSiguiente.clicked.connect(lambda: self.seleccionarFilaTW(*args, "siguiente"))
        #Botones para otros gráficos
        botonGraficoHistoria = QPushButton("Historia de Resolución")
        botonGraficoHistoria.clicked.connect(lambda: self.graficoResolucionSeleccionada(instancia))
        
        #Botón swaps
        botonGraficoSwaps = QPushButton("Influencia Swaps")
        botonGraficoSwaps.clicked.connect(lambda: self.graficoSwapsResolucionSeleccionada(None))

        #Botón swaps resultados instancias
        botonGraficoSwapsInstancia = QPushButton("Influencia Swaps en Instancia")
        botonGraficoSwapsInstancia.clicked.connect(lambda: self.graficoSwapsResolucionSeleccionada(instancia[0]))

        # Configurando Layouts
        gBResultados.setLayout(layoutTablas)
        gBGrafico.setLayout(layoutGrafico)
        gBAcciones.setLayout(layoutAcciones)
        gBSoluciones.setLayout(layoutSoluciones)

        gBResultados.setMinimumSize(600, 250)
        gBResultados.setMaximumSize(800, 250)
        gBSoluciones.setMinimumSize(500, 400)
        gBGrafico.setMaximumSize(400, 400)

        layoutAcciones.addWidget(botonAbrirTxt, 0, 0)
        layoutAcciones.addWidget(botonGraficoHistoria, 1, 0)
        layoutAcciones.addWidget(botonGraficoSwaps, 2, 0)
        layoutAcciones.addWidget(botonGraficoSwapsInstancia, 3, 0)
        layoutResultados.addWidget(gBSoluciones)
        layoutResultados.addWidget(gBGrafico)
        layoutPrincipal.addLayout(layoutResultados, 0, 0, 1, 2)
        layoutPrincipal.addWidget(gBResultados, 1, 0)
        layoutPrincipal.addWidget(gBAcciones, 1, 1)
        ventanaResultados.setLayout(layoutPrincipal)
        ventanaResultados.exec()

    def graficoSwapsResolucionSeleccionada(self, instanciaId=None):
        if instanciaId is None:
            res = DB.select_resoluciones(self.conn, self.resolucionSeleccionada)[0]
            self.graficoSwaps(json.loads(res[7]))
        else:
            res = DB.selectSwapsInstancia(self.conn, instanciaId)
            swaps = [0]*4
            for r in res:
                sw = json.loads(r[0])
                for i in range(len(sw)):
                    swaps[i] += sw[i]
            self.graficoSwaps(swaps)

    def graficoResolucionSeleccionada(self, instancia):
        print(self.resolucionSeleccionada)
        res = DB.select_resoluciones(self.conn, self.resolucionSeleccionada)
        print("Resolución a graficar ", res)
        self.graficoHistoria(res, instancia)
    
    def graficoHistoria(self, resoluciones, instancia):
        ventanaGrafico = QDialog(self)
        ventanaGrafico.setWindowTitle("Historial de Resolución")
        layoutPrincipal = QGridLayout()
        grafico = pg.PlotWidget()
        #grafico.setBackground("w")
        grafico.showGrid(x=True, y=True)
        layoutPrincipal.addWidget(grafico)
        
        ind = 0
        for r in resoluciones:
            soluciones = DB.select_solucionesXResolucion(self.conn, r[0])
            iteraciones = [s[4] for s in soluciones]
            costos = [s[1] for s in soluciones]
            lapiz = pg.mkPen((ind, len(resoluciones)), width=1.5)
            grafico.plot(iteraciones, costos, pen=lapiz, symbol="o", symbolSize="5", symbolBrush=(ind, len(resoluciones)))
            ind += 1
        lapiz = pg.mkPen("w", width=2)
        lineaOptimo = pg.InfiniteLine(instancia[6], angle=0, pen=lapiz, bounds=[0, iteraciones[-1]])
        grafico.addItem(lineaOptimo)
        ventanaGrafico.setLayout(layoutPrincipal)
        ventanaGrafico.exec()

    def llenarTablaResoluciones(self, tablaResoluciones, instanciaId):
        filasResoluciones = DB.select_resolucionesXInstancia(
            self.conn, instanciaId)


        tablaResoluciones.setColumnCount(11)
        tablaResoluciones.setRowCount(len(filasResoluciones))
        tablaResoluciones.setHorizontalHeaderLabels([
            "Iteraciones",
            "Óptimo",
            "T ADD",
            "T DROP",
            "error",
            "tiempo",
            "2-OPT",
            "3-OPT",
            "4-OPT",
            "Sol Inicial",
        ])
        tablaResoluciones.horizontalHeader().setStyleSheet(
            "QHeaderView { font-size: 10pt; }")
        for i in range(len(filasResoluciones)):
            swaps = json.loads(filasResoluciones[i][7])
            tablaResoluciones.setItem(
                i, 0, QTableWidgetItem(str(filasResoluciones[i][1])))
            tablaResoluciones.setItem(
                i, 1, QTableWidgetItem(str(filasResoluciones[i][2])))
            tablaResoluciones.setItem(
                i, 2, QTableWidgetItem(str(filasResoluciones[i][3])))
            tablaResoluciones.setItem(
                i, 3, QTableWidgetItem(str(filasResoluciones[i][4])))
            tablaResoluciones.setItem(
                i, 4, QTableWidgetItem(str(round(filasResoluciones[i][5], 2)) + "%"))
            tablaResoluciones.setItem(
                i, 5, QTableWidgetItem(self.formatearTiempo(filasResoluciones[i][6])))
            tablaResoluciones.setItem(i, 6, QTableWidgetItem(str(swaps[0])))
            tablaResoluciones.setItem(i, 7, QTableWidgetItem(str(swaps[1] + swaps[3])))
            tablaResoluciones.setItem(i, 8, QTableWidgetItem(str(swaps[2])))
            tablaResoluciones.setItem(i, 9, QTableWidgetItem(
                self.getSolucionInicial(filasResoluciones[i][8])))
            tablaResoluciones.setItem(
                i, 10, QTableWidgetItem(str(filasResoluciones[i][0])))
        for i in range(tablaResoluciones.columnCount()):
            tablaResoluciones.setColumnWidth(i, 70)

    def formatearTiempo(self, tiempo):
        segundos = int(tiempo)
        minutos = int(segundos / 60)
        horas = int(segundos / 3600)
        if horas!=0 and minutos!=0:
            return str(horas) + " hs " + str(minutos) + " min " + str(segundos) + " seg"
        elif minutos!=0:
            return str(minutos) + " min " + str(segundos) + " seg"
        else:
            return str(segundos) + " seg"


    def seleccionarPrimerFilaTW(self, treeSoluciones, graficoSoluciones, instancia):
        primeraFila = treeSoluciones.invisibleRootItem().child(0)
        treeSoluciones.setCurrentItem(primeraFila)
        self.establecerSolucionSeleccionada(graficoSoluciones, instancia[7], treeSoluciones, instancia[3])

    def seleccionarUltimaFilaTW(self, treeSoluciones, graficoSoluciones, instancia):
        root = treeSoluciones.invisibleRootItem()
        cantidadDeHijos = root.childCount()
        ultimaFila = root.child(cantidadDeHijos-1)
        treeSoluciones.setCurrentItem(ultimaFila)
        self.establecerSolucionSeleccionada(graficoSoluciones, instancia[7], treeSoluciones, instancia[3])

    def seleccionarFilaTW(self, treeSoluciones, graficoSoluciones, instancia, orden):
        root = treeSoluciones.invisibleRootItem()
        cantidadDeHijos = root.childCount()
        filaActual = treeSoluciones.currentIndex().row()
        if orden == "anterior":
            if filaActual > 0:
                filaActual -= 1
        elif orden == "siguiente":
            if filaActual < cantidadDeHijos - 1:
                filaActual += 1
        filaSeleccionada = root.child(filaActual)
        treeSoluciones.setCurrentItem(filaSeleccionada)
        self.establecerSolucionSeleccionada(graficoSoluciones, instancia[7], treeSoluciones, instancia[3])

    @QtCore.pyqtSlot(QtWidgets.QTreeWidgetItem)
    def establecerSolucionSeleccionada(self, grafico, coordenadas, arbol, nroVehiculos):
        filaSeleccionada = arbol.selectedItems()[0]
        if filaSeleccionada.parent() == None:
            rutas = []
            R = filaSeleccionada.child(0)
            for j in range(R.childCount()):
                vertices = R.child(j).text(0)
                rutas.append(json.loads(vertices))
            self.dibujarSolucion(grafico, rutas, coordenadas, nroVehiculos)

    def establecerResolucionSeleccionada(self, tabla, arbol, grafico, instancia):
        # print("Seleccionado tabla: ", tabla)
        self.resolucionSeleccionada = str(tabla.selectedItems()[10].text())
        arbol.clear()
        filasSoluciones = DB.select_solucionesXResolucion(
            self.conn, self.resolucionSeleccionada)
        items = []
        # print("resolución ", self.resolucionSeleccionada)
        # print("soluciones ", filasSoluciones)
        for s in filasSoluciones:
            rutas = json.loads(s[2])
            origen = json.loads(s[3])
            fila = QtGui.QTreeWidgetItem(arbol, [str(s[4]), str(s[1]), self.getOrigenSolucion(origen)])
            for r in range(len(rutas)):
                ruta = QtGui.QTreeWidgetItem(fila, [("Ruta %d")%(r+1)])
                for i in range(len(rutas)):
                    vertices = QtGui.QTreeWidgetItem(ruta, [str(rutas[i])])
                    ruta.addChild(vertices)
            fila.addChild(ruta)
        arbol.insertTopLevelItems(0, items)
        self.seleccionarPrimerFilaTW(arbol, grafico, instancia)

        # print(filasSoluciones)

    def getOrigenSolucion(self, kopt):
        tipoSwap = kopt[0]
        variante = kopt[1]
        salida = ""
        if tipoSwap == 0:
            salida += "Solución Inicial"
        elif tipoSwap == 2:
            salida += "2-opt"
        elif tipoSwap == 3:
            salida += "3-opt"
        elif tipoSwap == 4:
            salida += "4-opt"
        elif tipoSwap == 5:
            salida += "3-opt"
        if tipoSwap != 0:
            salida += " variante " + str(variante)
        return salida

    def getSolucionInicial(self, sol):
        try:
            sol = int(sol)
            if sol == 0:
                return "Clarke & Wright"
            elif sol == 1:
                return "Vecino Cercano"
            else:
                return sol
        except ValueError:
            return sol
            
    def graficoInstancia(self, layout, coordenadas, row, col):
        w1 = pg.PlotWidget()
        #w1 = view.addPlot()
       # QtGui.QColor(QtCore.qrand() % 256, QtCore.qrand() % 256, QtCore.qrand() % 256
        for coord in coordenadas:
            s = pg.ScatterPlotItem(
                [coord[1]], [coord[2]], size=10, pen=pg.mkPen(None))
            if coord[0] == 1:
                s.setBrush(QBrush(QtGui.QColor(255, 0, 0)))
            else:
                s.setBrush(QBrush(QtGui.QColor(255, 255, 255)))
            w1.addItem(s)
        layout.addWidget(w1)

        return w1
    # Obtengo los datos de mis archivos .vrp

    def cargarDesdeFile(self, pathArchivo):
        # +-+-+-+-+-Para cargar la distancias+-+-+-+-+-+-+-+-
        archivo = open(pathArchivo, "r")
        lineas = archivo.readlines()
        self.nombreArchivo = os.path.basename(archivo.name)
        self.nombreArchivo = self.nombreArchivo.split(".")[0]
        # Busco la posiciones de...
        try:
            indSeccionCoord = lineas.index("NODE_COORD_SECTION \n")
            lineaEOF = lineas.index("DEMAND_SECTION \n")
        except ValueError:
            try:
                indSeccionCoord = lineas.index("NODE_COORD_SECTION\n")
                lineaEOF = lineas.index("DEMAND_SECTION\n")
            except ValueError:
                indSeccionCoord = lineas.index("NODE_COORD_SECTION\t\n")
                lineaEOF = lineas.index("DEMAND_SECTION\t\n")

        # Linea optimo y nro de vehiculos
        lineaOptimo = [x for x in lineas[0:indSeccionCoord]
                       if re.search(r"COMMENT+", x)][0]
        parametros = re.findall(r"[0-9]+", lineaOptimo)

        self.__nroVehiculos = int(float(parametros[0]))
        self.__optimo = float(parametros[1])

        # Cargo la capacidad
        lineaCapacidad = [x for x in lineas[0:indSeccionCoord]
                          if re.search(r"CAPACITY+", x)][0]
        parametros = re.findall(r"[0-9]+", lineaCapacidad)

        self.__capacidad = float(parametros[0])
        print("Capacidad: "+str(self.__capacidad))

        # Lista donde irán las coordenadas (vertice, x, y)
        coord = []
        # Separa las coordenadas en una matriz, es una lista de listas (vertice, coordA, coordB)
        for i in range(indSeccionCoord+1, lineaEOF):
            textoLinea = lineas[i]
            # Elimina los saltos de línea
            textoLinea = re.sub("\n", "", textoLinea)
            splitLinea = textoLinea.split()  # Divide la línea por " "
            if(splitLinea[0] == ""):
                coord.append([float(splitLinea[1]), float(splitLinea[2]), float(
                    splitLinea[3])])  # [[v1,x1,y1], [v2,x2,y2], ...]
            else:
                coord.append([float(splitLinea[0]), float(splitLinea[1]), float(
                    splitLinea[2])])  # [[v1,x1,y1], [v2,x2,y2], ...]
        #print("coordenadas: "+str(coordenadas))
        # self.cargaMatrizDistancias(coordenadas)
        self.coordenadas = coord

        # +-+-+-+-+-+-+-Para cargar la demanda+-+-+-+-+-+-+-
        seccionDemanda = [x for x in lineas[indSeccionCoord:]
                          if re.findall(r"DEMAND_SECTION+", x)][0]
        indSeccionDemanda = lineas.index(seccionDemanda)

        seccionEOF = [x for x in lineas[indSeccionCoord:]
                      if re.findall(r"DEPOT_SECTION+", x)][0]
        indLineaEOF = lineas.index(seccionEOF)

        demanda = []
        for i in range(indSeccionDemanda+1, indLineaEOF):
            textoLinea = lineas[i]
            # Elimina los saltos de línea
            textoLinea = re.sub("\n", "", textoLinea)
            splitLinea = textoLinea.split()  # Divide la línea por " "
            try:
                demanda.append(float(splitLinea[1]))
            except:
                splitLinea = textoLinea.split()
                demanda.append(float(splitLinea[1]))
        # print(str(demanda))
        self.__demanda = demanda
        self.cantidadClientes = len(self.__demanda)

    def cargaMatrizDistancias(self, coordenadas):
        matriz = []
        # Arma la matriz de distancias. Calculo la distancia euclidea
        for coordRow in coordenadas:
            fila = []
            for coordCol in coordenadas:
                x1 = float(coordRow[1])
                y1 = float(coordRow[2])
                x2 = float(coordCol[1])
                y2 = float(coordCol[2])
                dist = self.distancia(x1, y1, x2, y2)

                # Para el primer caso. Calculando la distancia euclidea entre si mismo da 0
                if(dist == 0 and float(coordRow[0]) == float(coordCol[0])):
                    dist = float("inf")
                fila.append(dist)

            #print("Fila: "+str(fila))
            matriz.append(fila)
        return np.array(matriz)

    def distancia(self, x1, y1, x2, y2):
        return math.sqrt((x1-x2)**2+(y1-y2)**2)

    def dibujarRutaInicial(self, rutas):
        #print("Ingresar Rutas : ",rutas)
        print("recibió ruta")
        i = 0
        t = time()

        self.grafico.clear()
        self.grafico.showGrid(x=True, y=True)
        for r in rutas:
            x = [self.coordenadas[0][1]]
            y = [self.coordenadas[0][2]]
            for a in r.getA()[1:]:
                x.append(self.coordenadas[a.getOrigen().getValue()-1][1])
                y.append(self.coordenadas[a.getOrigen().getValue()-1][2])
            x += [self.coordenadas[0][1]]
            y += [self.coordenadas[0][2]]
            ruta = self.grafico.plot(x, y, pen=(
                i, self.k), symbol='o', symbolBrush=(i, self.k))
            self.rutasDict[i] = ruta
            i += 1
        x = [self.coordenadas[0][1]]
        y = [self.coordenadas[0][2]]
        deposito = self.grafico.plot(x, y, pen=(
            0, self.k), symbol='h', symbolSize=20, symbolBrush=(255, 255, 255))
        self.rutasDict[i+1] = deposito

    def dibujarRutasNuevas(self, R):
        """Dibuja rutas que vienen desde el CVRP"""
        indRutas = R["indRutas"]
        rutas = R["rutas"]
        print("recibió ruta")

        t = time()
        self.grafico.clear()
        self.grafico.showGrid(x=True, y=True)
        for d in self.rutasDict.keys():
            if d != indRutas[0] and d != indRutas[1]:
                self.grafico.addItem(self.rutasDict[d])

        i = 0
        for r in rutas:
            x = [self.coordenadas[0][1]]
            y = [self.coordenadas[0][2]]
            for a in r.getA()[1:]:
                x.append(self.coordenadas[a.getOrigen().getValue()-1][1])
                y.append(self.coordenadas[a.getOrigen().getValue()-1][2])
            x += [self.coordenadas[0][1]]
            y += [self.coordenadas[0][2]]
            ruta = self.grafico.plot(x, y, pen=(
                indRutas[i], self.k), symbol='o', symbolBrush=(indRutas[i], self.k))
            self.rutasDict[indRutas[i]] = ruta
            i += 1


    def dibujarSolucion(self, grafico, rutas, coordenadas, nroVehiculos):
        """Dibuja rutas, apartir de una lista de enteros, que representarían a los vértices"""

        coordenadas = json.loads(coordenadas)
        t = time()
        grafico.clear()
        indRutas = list(range(len(rutas)))
        grafico.showGrid(x=True, y=True)
        i = 0
        for r in rutas:
            x = [coordenadas[0][1]]
            y = [coordenadas[0][2]]
            for v in r:
                x.append(coordenadas[int(v) - 1][1])
                y.append(coordenadas[int(v) - 1][2])
            x += [coordenadas[0][1]]
            y += [coordenadas[0][2]]
            ruta = grafico.plot(x, y, pen=(
                indRutas[i], nroVehiculos), symbol='o', symbolBrush=(indRutas[i], nroVehiculos), name=str(i + 1))

            i += 1
        x = [coordenadas[0][1]]
        y = [coordenadas[0][2]]
        deposito = grafico.plot(x, y, pen=(
            0, nroVehiculos), symbol='h', symbolSize=20, symbolBrush=(255, 255, 255), name="Depósito")
        
        print(f"Se cargó el gráfico --> {time()-t} ")

    def graficoSwaps(self, swaps):
        """ Recibe una lista con 4 elementos con los distintos swap's. 
            el 3 y 5 corresponden a 3-opt
        """
        mpl.rcParams['toolbar'] = 'None'
        swaps = [swaps[0], swaps[1] + swaps[3], swaps[2]]
        x = [0, 1, 2]
        width = 0.8 # ancho de las barras
        fig, ax = plt.subplots()
        rects1 = ax.bar(x, swaps, width, color='r')

        ax.set_ylim(0, max(swaps) + max(swaps) * 0.1)
        ax.set_ylabel('')
        ax.set_title("Swap's")
        ax.set_xticks(x) 
        ax.set_xticklabels(('2-opt', '3-opt', '4-opt'))

        for rect in rects1:
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                    '%d' % int(height),
                    ha='center', va='bottom')
        plt.show()

    def abrirYCargarTxt(self, tablaResoluciones, instanciaId):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        archivosTxt, _ = QFileDialog.getOpenFileNames(
            self, "QFileDialog.getOpenFileNames()", "", "Archivos Txt (*.txt)", options=options)
        for a in archivosTxt:
            self.cargarTxt(a, instanciaId)
        self.llenarTablaResoluciones(tablaResoluciones, instanciaId)

    def cargarTxt(self, path, instanciaId):
        archivoTxt = open(path, "r",encoding="latin-1")
        lineas = [linea for linea in archivoTxt.readlines()]
        rutas = []
        swapsStr = []
        costosRuta = []
        costosRutas = []
        iteraciones = []
        for i in range(len(lineas)):
            aux = re.findall(r"Nro de vehiculos:", lineas[i])
            if len(aux) != 0:
                k = int(lineas[i].split(" ")[3])

            aux = re.findall(r"Nro de clientes:", lineas[i])
            if len(aux) != 0:
                n = int(lineas[i].split(" ")[3])

            aux = re.findall(r"Cantidad de iteraciones:", lineas[i])
            if len(aux) != 0:
                cantidadIteraciones = int(lineas[i].split(" ")[3])

            aux = re.findall(r"Ruta #", lineas[i])
            if len(aux) != 0:
                rutas.append(lineas[i])

            aux = re.findall("Costo asociado: ", lineas[i])
            if len(aux) != 0:
                costosRuta.append(float(lineas[i].split(" ")[2]))

            aux = re.findall("Costo total: ", lineas[i])
            if len(aux) != 0:
                costosRutas.append(float(lineas[i].split(" ")[3]))

            aux = re.findall("Iteracion ", lineas[i])
            if len(aux) != 0:
                iteraciones.append(int(lineas[i].split(" ")[2]))

            aux = re.findall("Se estancó|([1-5]-Opt)", lineas[i])
            if len(aux) != 0:
                swapsStr.append(lineas[i])

            aux = re.findall("Solucion peor", lineas[i])
            if len(aux) != 0:
                swapsStr.append(lineas[i])

            aux = re.findall("Solucion inicial", lineas[i])
            if len(aux) != 0:
                solucionInicial = lineas[i].split(": ")[1].replace("\n", "")

            aux = re.findall("Costo Total", lineas[i])
            if len(aux) != 0:
                costoTotal = lineas[i].split(" ")[2]

            aux = re.findall("Desviación", lineas[i])
            if len(aux) != 0:
                desvio = float(lineas[i].split(": ")[3].replace("%\n", ""))

            aux = re.findall("Tiempo total:", lineas[i])
            if len(aux) != 0:
                tiempoTotal1 = lineas[i].split(" ")[2].replace("min", "")
                tiempoTotal2 = lineas[i].split(" ")[3].replace("seg", "")

        tiempoTotal = [int(tiempoTotal1), int(tiempoTotal2)]
        tiempoTotal = int(tiempoTotal[0]/60) + tiempoTotal[1]
        #Se procesan las rutas
        i = 0
        ruta = []
        rutasNuevas = []
        for r in rutas:
            if i < k:
                strRuta = re.findall("Ruta #[0-9]*: ", r)[0]
                R = r.replace(strRuta, "")
                R = R.replace("\n", "")
                ruta.append(json.loads(R))
                i+=1
            if i == k:
                rutasNuevas.append(ruta)
                i = 0
                ruta = []
        #Se le suma la primer y última iteración 
        iteraciones = [1] + iteraciones
        iteraciones.append(cantidadIteraciones)
        #Se procesan los swaps y demás movimientos
        for i in range(len(swapsStr)):
            swapsStr[i] = swapsStr[i].replace("-Opt Opcion:", "")
            swapsStr[i] = swapsStr[i].replace("\n", "")
            aux = re.findall("path relinking", swapsStr[i])
            if len(aux) != 0:
                swapsStr[i] = "PathRelinking"

            aux = re.findall("penultimo", swapsStr[i])
            if len(aux) != 0:
                swapsStr[i] = "penúltimo"

            aux = re.findall("peor", swapsStr[i])
            if len(aux) != 0:
                swapsStr[i] = "peor"

            aux = re.findall(r"[0-9] [\-]*[0-9]", swapsStr[i])
            if len(aux) != 0:
                splitStr = swapsStr[i].split(" ")
                swapsStr[i] = [int(splitStr[0]),int(splitStr[1])]

        swaps = [0]*4
        for s in swapsStr:
            if isinstance(s, list):
                if s[0] == 2:
                    swaps[0]+= 1
                elif s[0] == 3:
                    swaps[1]+= 1
                elif s[0] == 4:
                    swaps[2] += 1
                elif s[0] == 5:
                    swaps[3] += 1

        cantidadClientes = 0
        for r in rutasNuevas:
            cantidadClientes += len(r)

        swapsStr = [solucionInicial] + swapsStr
        swapsStr.append("NS")
        solucionDB = []
        while len(rutasNuevas) != 0:
            C = []
            for j in range(k):
                C.append(costosRuta.pop(0))
            origen = swapsStr.pop(0)
            s = (
                costosRutas.pop(0),
                json.dumps(rutasNuevas.pop(0)),
                json.dumps(origen),
                iteraciones.pop(0),
                json.dumps(C)
            )
            if  origen == "peor" or origen == "penúltimo":
                continue
            else:
                solucionDB.append(s)

        tenureADD = int(cantidadClientes * 0.05)
        tenureDROP = int(cantidadClientes * 0.05) +1
        resolucion = (cantidadIteraciones,
                      solucionDB[-1][0],
                      tenureADD,
                      tenureDROP,
                      desvio,
                      tiempoTotal,
                      json.dumps(swaps),
                      solucionInicial,
                      1
                      )
        print("instancia ID: ", instanciaId)
        idRes = DB.insert_resolucion(self.conn, resolucion)
        DB.insert_resolucionXInstancia(self.conn, (idRes, instanciaId))
        for x in solucionDB:
            idSol = DB.insert_solucion(self.conn, x)
            DB.insert_solucionXResolucion(self.conn, (idRes, idSol))


class Worker(QRunnable):

    def __init__(self, funcion, *args, **kwargs):
        super(Worker, self).__init__()

        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.fn = funcion

    @pyqtSlot()
    def run(self):
        self.fn()


class WorkerSignals(QObject):

    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    ruta = pyqtSignal(dict)
    rutaLista = pyqtSignal(list)
    valorBarra = pyqtSignal(tuple)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = GUI()
    mainWin.show()
    sys.exit(app.exec_())
