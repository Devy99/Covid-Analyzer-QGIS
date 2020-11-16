# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CovidAnalyzer
                                 A QGIS plugin
 This plugin tracks Covid-19 cases
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-10-25
        git sha              : $Format:%H$
        copyright            : (C) 2020 by  
        email                :  
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# Qgis library
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import QIcon, QColor, QFont
from qgis.PyQt.QtWidgets import QAction, QProgressBar
from qgis.core import *

from qgis.gui import (
    QgsMapCanvas,
    QgsVertexMarker,
    QgsMapCanvasItem,
    QgsRubberBand,
    QgsMessageBar
)
# Initialize Qt resources from file resources.py
from .resources import *

# Data url retrieve library
import urllib.request
from urllib.error import URLError, HTTPError

# Import the code for the dialog
from .covid_analyzer_dialog import CovidAnalyzerDialog

# Join library
import processing

# CSV handling library
import pandas as pd

# Utility import
import os.path
import os
import io
import time
from datetime import timedelta 
from tempfile import TemporaryFile


# Absolute path of plugin folder
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

# Path of Region layer file and Province layer file 
PROV_PATH = os.path.join(THIS_FOLDER, 'layers/italy_boundaries/italy_prov/ProvCM01012020_WGS84.shp')
REG_PATH = os.path.join(THIS_FOLDER, 'layers/italy_boundaries/italy_reg/Reg01012020_WGS84.shp')

# Instantiate layers
reg_layer = QgsVectorLayer(REG_PATH, "Region layer", "ogr")
prov_layer = QgsVectorLayer(PROV_PATH, "Province layer", "ogr")

# Static declaration of layersMap
layersMap = {"Province layer": prov_layer, "Region layer": reg_layer}

# Layer type constants
REGION_LAYER = "Region layer"
PROVINCE_LAYER = "Province layer"

# Instantiate a global canvas
canvas = QgsMapCanvas()

# Csv costant prefixs and suffix
PROV_URL_PREFIX = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-province/dpc-covid19-ita-province-'
REG_URL_PREFIX = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni-'
URL_SUFFIX = '.csv'

class CovidAnalyzer:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'CovidAnalyzer_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Covid Analyzer')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('CovidAnalyzer', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/covid_analyzer/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Check pandemic data'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&Covid Analyzer'),
                action)
            self.iface.removeToolBarIcon(action)

    def showLabels(self):
        layerName = self.ui.layerComboBox.currentText()
        layer = layersMap[layerName]
        palLayer = QgsPalLayerSettings()
        palLayer.fieldName = 'DEN_PROV'
        palLayer.enabled = True
        palLayer.placement = QgsPalLayerSettings.OverPoint
        labels = QgsVectorLayerSimpleLabeling(palLayer)
        layer.setLabeling(labels)
        layer.setLabelsEnabled(True)
        layer.triggerRepaint()

    def resetUi(self): 
        self.first_start = True

    def showCanvas(self):
        selectedDate = getCurrentDateFromUI(self)
        selectedCsvFilename = downloadCsvByDate(self, selectedDate)
        previousDate = getPreviousDateFromUI(self)
        previousdCsvFilename = downloadCsvByDate(self, previousDate)

        canvas.setCanvasColor(Qt.white)
        canvas.enableAntiAliasing(True)
        canvas.move(50,50)
        canvas.show()
        layerName = self.ui.layerComboBox.currentText()
        layer = layersMap[layerName]
        if not layer.isValid():
            print("Layer failed to load!")

        performTableJoin(self, selectedCsvFilename, layerName)
        QgsProject.instance().addMapLayer(layersMap["Join result"])

        # set extent to the extent of our layer
        canvas.setExtent(layer.extent())

        # set the map canvas layer set
        canvas.setLayers([layer])

        self.showLabels()

    def showLayout(self):
 
        QgsProject.instance().addMapLayer(prov_layer)

        project = QgsProject.instance()
        manager = project.layoutManager()
        layoutName = 'LegendLayout'
        layouts_list = manager.printLayouts()
        # remove any duplicate layouts
        for layout in layouts_list:
            if layout.name() == layoutName:
                manager.removeLayout(layout)
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.setName(layoutName)
        manager.addLayout(layout)
        
        # create map item in the layout
        map = QgsLayoutItemMap(layout)
        map.setRect(20, 20, 20, 20)
        
        # set the map extent
        ms = QgsMapSettings()
        ms.setLayers([prov_layer]) # set layers to be mapped
        rect = QgsRectangle(ms.fullExtent())
        rect.scale(1.5)
        ms.setExtent(rect)
        map.setExtent(rect)
        map.setBackgroundColor(QColor(255, 255, 255, 0))
        layout.addLayoutItem(map)
        
        map.attemptMove(QgsLayoutPoint(5, 20, QgsUnitTypes.LayoutMillimeters))
        map.attemptResize(QgsLayoutSize(180, 180, QgsUnitTypes.LayoutMillimeters))
        
        legend = QgsLayoutItemLegend(layout)
        legend.setTitle("Legend")
        layout.addLayoutItem(legend)
        legend.attemptMove(QgsLayoutPoint(230, 15, QgsUnitTypes.LayoutMillimeters))
        
        title = QgsLayoutItemLabel(layout)
        title.setText("My Title")
        title.setFont(QFont('Arial', 24))
        title.adjustSizeToText()
        layout.addLayoutItem(title)
        title.attemptMove(QgsLayoutPoint(10, 5, QgsUnitTypes.LayoutMillimeters))
        
        layout = manager.layoutByName(layoutName)
        self.iface.showLayoutManager ()
        


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.ui = CovidAnalyzerDialog()

        # show the dialog
        self.ui.show()
        self.showLayout()

        initComponentsGUI(self)

        # Widget signals
        self.ui.layerComboBox.currentIndexChanged.connect(lambda: updateInformationComboBox(self))
        self.ui.previewButton.clicked.connect(self.showCanvas)
        self.ui.rejected.connect(self.resetUi)

        # Run the dialog event loop
        result = self.ui.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass


def initComponentsGUI(self):
    # Clearing existing data
    self.ui.typeComboBox.clear()
    self.ui.layerComboBox.clear()

    # Init layers comboBox
    layersNameList = ["Region layer", "Province layer"]
    self.ui.layerComboBox.addItems(layersNameList)
    
    # Init informations comboBox
    informationsList = ["Casi totali","Casi quotidiani","Tamponi","Dimessi guariti","Deceduti"]
    self.ui.typeComboBox.addItems(informationsList)

def updateInformationComboBox(self):
    # Clearing existing data
    self.ui.typeComboBox.clear()

    informationsList = []

    # Update informations comboBox
    selectedLayerName = self.ui.layerComboBox.currentText()
    if selectedLayerName == "Region layer":
        informationsList = ["Casi totali","Casi quotidiani","Tamponi","Dimessi guariti","Deceduti"]
    elif  selectedLayerName == "Province layer":
        informationsList = ["Casi totali","Variazione casi"]
    self.ui.typeComboBox.addItems(informationsList)

def getCurrentDateFromUI(self):
    # Get data from UI
    pyQgisDate = self.ui.dateEdit.date() 
    currentDate = pyQgisDate.toPyDate()
    return currentDate

def getPreviousDateFromUI(self):
    # Get data from UI
    pyQgisDate = self.ui.dateEdit.date() 
    currentDate = pyQgisDate.toPyDate()

    previousDate = currentDate - timedelta(days = 1)
    return previousDate


# This method takes as parameter the Date of csv to download and return the filename in output
def downloadCsvByDate(self, date):
    dateString = str(date).replace('-', '')

    # Concatenate final CSV url
    url = dateString

    # Check selected layer
    selectedLayerName = self.ui.layerComboBox.currentText()
    filePrefix = ''

    if selectedLayerName == 'Province layer':
        url = PROV_URL_PREFIX + dateString + URL_SUFFIX
        filePrefix = 'Prov'
    elif selectedLayerName == 'Region layer':
        url = REG_URL_PREFIX + dateString + URL_SUFFIX
        filePrefix = 'Reg'
    
    # Generating filename
    fileName = filePrefix + dateString + '.csv'
    relativeFilepath = 'csv_cache/' + fileName

    csvFile = os.path.join(THIS_FOLDER, relativeFilepath)

    # Check if file exists in cache
    if not os.path.isfile(csvFile):
        try:
            response =  urllib.request.urlretrieve(url, csvFile)
        except HTTPError as e:
            self.iface.messageBar().pushMessage("Error", "Cannot retrieve any csv data at selected date", level=Qgis.Critical)
        except URLError as e:
            self.iface.messageBar().pushMessage("Error", "Request rejected. Check your internet connection", level=Qgis.Critical)
    
    return fileName

# This method perform table joins between a .shp file and a .csv file in their reg/prov code
def performTableJoin(self, csvFilename, layerType):
    csvFilepath = THIS_FOLDER + "/csv_cache/" + csvFilename
    csvUri = "file:///" + csvFilepath

    csv = QgsVectorLayer(csvUri, "csv", "delimitedtext")

    if layerType == REGION_LAYER:
        fixRegionCsv(csvFilepath)

        shp = layersMap['Region layer']
        csvField = 'denominazione_regione'
        shpField='DEN_REG'
    elif layerType == PROVINCE_LAYER:
        calculateCasesVariation(self, csvFilepath)

        shp = layersMap['Province layer']
        csvField = 'sigla_provincia'
        shpField='SIGLA' 

    joinObject = QgsVectorLayerJoinInfo()
    joinObject.setJoinFieldName(csvField)
    joinObject.setTargetFieldName(shpField)
    joinObject.setJoinLayerId(csv.id())
    #QgsProject.instance().addMapLayer(shp)
    #QgsProject.instance().addMapLayer(csv)
    
    joinObject.setUsingMemoryCache(True)
    joinObject.setJoinLayer(csv)
    QgsMessageLog.logMessage( csvUri, 'MyPlugin', level=Qgis.Info)
    
    shp.addJoin(joinObject)

    shp.selectAll()
    # Clear dictionary
    if "Join result" in layersMap:
       del layersMap["Join result"] # In order to avoid duplicated entries

    layersMap["Join result"] = processing.run("native:saveselectedfeatures", {'INPUT': shp, 'OUTPUT': 'memory:'})['OUTPUT']
    shp.removeSelection()

# This method adapt retrieved region CSV in order to be abled to perform join
def fixRegionCsv(csvFilepath):
    csv = pd.read_csv(csvFilepath)

    if csv.shape[0] > 20: # Check if Csv was fixed previously
        csv.iloc[11,2]  = 4  # Change region code to 4
        csv.iloc[11,3]  = 'Trentino-Alto Adige'  # Change region name

        for x in range(6, 21):  # Merging Bolzano and Trento rows
            csv.iloc[11,x]  += csv.iloc[12,x]

        csv.drop(12,axis=0,inplace=True) # Drop Bolzano row
        csv.to_csv(csvFilepath) # Saving updated CSV 

# This method adapt retrieved province CSV in order to get cases variation data
def calculateCasesVariation(self, csvFilepath):
    previousDate = getPreviousDateFromUI(self)
    previousCsvFilename = downloadCsvByDate(self, previousDate)
    previousCsvFilepath = THIS_FOLDER + "/csv_cache/" + previousCsvFilename

    currentCsv = pd.read_csv(csvFilepath)
    previousCsv = pd.read_csv(previousCsvFilepath)

    # Check if the csv was modified previously
    if not 'variazione' in currentCsv: 
        countRowCurrentCsv = currentCsv.shape[0]
        countRowPreviousCsv = previousCsv.shape[0]

        totalCasesVar = []
        # Take total cases of selected day from defined provinces
        for i in range(countRowCurrentCsv):
            if not (currentCsv.loc[i,"denominazione_provincia"] == "In fase di definizione/aggiornamento") and not(currentCsv.loc[i,"denominazione_provincia"] == "Fuori Regione / Provincia Autonoma"):
                totalCasesVar.append(currentCsv.loc[i, "totale_casi"])

        # Take total cases of previous day from defined provinces and subtract from the ones of next day
        count = 0
        for i in range(countRowPreviousCsv):
            if not (previousCsv.loc[i,"denominazione_provincia"] == "In fase di definizione/aggiornamento") and not(previousCsv.loc[i,"denominazione_provincia"] == "Fuori Regione / Provincia Autonoma"):
                totalCasesVar[count] -= previousCsv.loc[i, "totale_casi"]
                count += 1

        # Create the column variation 
        currentCsv.insert(10, "variazione", 0, True) 

        # Put variation value in the new column 'variazione'
        count = 0
        for i in range(countRowCurrentCsv):
            if not (currentCsv.loc[i,"denominazione_provincia"] == "In fase di definizione/aggiornamento") and not(currentCsv.loc[i,"denominazione_provincia"] == "Fuori Regione / Provincia Autonoma"):
                currentCsv.loc[i,"variazione"] += totalCasesVar[count]
                count += 1

        currentCsv.to_csv(csvFilepath) # Saving updated CSV 