 # Building a Custom Selection Tool

from qgis.gui import *
from qgis.core import *
from PyQt4.QtGui import *
from PyQt4.QtCore import SIGNAL, Qt

# import sys, os
# Pad aangeven waar de python objecten van FME zich bevinden
# sys.path.append("C:\\Program Files\\FME\\fmeobjects\\python27") 
# import fmeobjects

class MyWnd(QMainWindow):
    # Self is een verwijzing naar de klasse instantie MyWnd. In Python  moet dat expliciet gebeuren
    # __init__ methode wordt als constructor aangeroepen bij het creeeren van een instantie
    def __init__(self):
        QMainWindow.__init__(self)
        QgsApplication.setPrefixPath("C:/Program Files/QGIS 2.16.1/apps/qgis", True)
        QgsApplication.initQgis()
        self.canvas = QgsMapCanvas()
        self.canvas.setCanvasColor(Qt.white)
        self.lyr = QgsVectorLayer("D:/OneDrive - Travelingo/GIS/Reg_SourcProj/Nederland/Chrystal.shp", "Chrystal", "ogr")
        QgsMapLayerRegistry.instance().addMapLayer(self.lyr)
        self.canvas.setExtent(self.lyr.extent())
        self.canvas.setLayerSet([QgsMapCanvasLayer(self.lyr)])
        
        # Definieert de centrale widget = window, minimaal 1 widget is verplicht
        self.setCentralWidget(self.canvas)
        # The QAction class provides an abstract user interface action that can be inserted into widgets
        actionZoomIn = QAction("Zoom in", self)
        actionZoomOut = QAction("Zoom out", self)
        actionPan = QAction("Pan", self)
        actionSelect = QAction("Select", self)
        actionSelectRectangle = QAction("Select rectangle", self)
        
        # setCheckable
        actionZoomIn.setCheckable(True)
        actionZoomOut.setCheckable(True)
        actionPan.setCheckable(True)
        actionSelect.setCheckable(True)
        actionSelectRectangle.setCheckable(True)
        
        # Now, we connect the signal created when the buttons are clicked to the Python methods that will provide each tool's functionality:
        actionZoomIn.triggered.connect(self.zoomIn)
        actionZoomOut.triggered.connect(self.zoomOut)
        actionPan.triggered.connect(self.pan)
        actionSelect.triggered.connect(self.select)
        actionSelectRectangle.triggered.connect(self.selectrectangle)
        
        # Next, we create our toolbar and add the buttons:        
        self.toolbar = self.addToolBar("Canvas actions")
        self.toolbar.addAction(actionZoomIn)
        self.toolbar.addAction(actionZoomOut)
        self.toolbar.addAction(actionPan)
        self.toolbar.addAction(actionSelect)
        self.toolbar.addAction(actionSelectRectangle)
        
        # Then, we connect the buttons to the applications states:
        self.toolPan = QgsMapToolPan(self.canvas)
        self.toolPan.setAction(actionPan)
        self.toolZoomIn = QgsMapToolZoom(self.canvas, False) # false = in
        self.toolZoomIn.setAction(actionZoomIn)
        self.toolZoomOut = QgsMapToolZoom(self.canvas, True) # true = out
        self.toolZoomOut.setAction(actionZoomOut)
        self.toolSelect = SelectMapTool(self.canvas, self.lyr) 
        self.toolSelect.setAction(actionSelect)
        self.toolRectangle = RectangleMapTool(self.canvas, self.lyr)  
        self.toolRectangle.setAction(actionSelectRectangle) 
        self.select()
        
        
    def zoomIn(self):
        self.canvas.setMapTool(self.toolZoomIn)
        
    def zoomOut(self):
        self.canvas.setMapTool(self.toolZoomOut)
        
    def pan(self):
        self.canvas.setMapTool(self.toolPan)

    def select(self):
        self.canvas.setMapTool(self.toolSelect)
    
    def selectrectangle(self):
        self.canvas.setMapTool(self.toolRectangle)

class SelectMapTool(QgsMapToolEmitPoint):
    def __init__(self, canvas, lyr):
        self.canvas = canvas
        self.lyr = lyr
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.rubberband = QgsRubberBand(self.canvas, QGis.Polygon)
        self.rubberband.setColor(QColor(255,255,0,50))
        self.rubberband.setWidth(1)
        self.point = None
        self.points = []
    
    def canvasPressEvent(self, e):
        self.point = self.toMapCoordinates(e.pos())
        m = QgsVertexMarker(self.canvas)
        m.setCenter(self.point)
        m.setColor(QColor(0,255,0))
        m.setIconSize(5)
        m.setIconType(QgsVertexMarker.ICON_BOX)
        m.setPenWidth(3) 
        self.points.append(self.point)
        self.isEmittingPoint = True
        self.selectPoly()

    def selectPoly(self):
        self.rubberband.reset(QGis.Polygon)
        for point in self.points[:-1]:
            self.rubberband.addPoint(point, False)
        self.rubberband.addPoint(self.points[-1], True)
        self.rubberband.show() 
        if len(self.points) > 2:
            g = self.rubberband.asGeometry()
            featsPnt = self.lyr.getFeatures(QgsFeatureRequest().setFilterRect(g.boundingBox()))
            for featPnt in featsPnt:
                if featPnt.geometry().within(g):
                    self.lyr.select(featPnt.id())                  

class RectangleMapTool(QgsMapToolEmitPoint):
    def __init__(self, canvas,lyr):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.rubberBand = QgsRubberBand(self.canvas, QGis.Polygon)
        self.rubberBand.setFillColor(QColor(255,255,0,50))         
        self.rubberBand.setWidth(1)
        self.reset()

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rubberBand.reset(QGis.Polygon)

    def canvasPressEvent(self, e):
        self.startPoint = self.toMapCoordinates(e.pos())
        self.endPoint = self.startPoint
        self.isEmittingPoint = True
        self.showRect(self.startPoint, self.endPoint)

    def canvasReleaseEvent(self, e):
        self.isEmittingPoint = False
        r = self.rectangle()
        if r is not None:
        # Hier verwijzing naar een pop up maken met een vraag of van deze boundingbox alle items kunnen worden opgehaald.
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Do you really want the items in the rectangle area exported for editing?")
            msg.setWindowTitle("Export BoundingBox")
            msg.setDetailedText("BoundingBox: " + str(r.xMinimum()) + ", " + str(r.yMinimum()) + ", " + str(r.xMaximum()) + ", " + str(r.yMaximum()))
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            #msg.buttonClicked.connect(self.msgbtn())
            msg.show()
            retval = msg.exec_()
            print "value of pressed message box button:", retval
            
            #if retval == 1024:
                #implementatie REST FME server?
                
                # initiate FMEWorkspaceRunner Class 
                # runner = fmeobjects.FMEWorkspaceRunner() 
                # Full path to Workspace, example comes from the FME 2014 Training Full Dataset
                # workspace = 'D:\OneDrive - Travelingo\Opdrachtgevers\RedGeographics\FME_Postgis\1474_Datamanagement\workspaces\Export_BBoxV002.fmw'
                # Set workspace parameters by creating a dictionary of name value pairs
                # parameters = {}
                # parameters['Minimum_x'] = r.xMinimum()
                # parameters['Minimum_Y'] = r.yMinimum()
                # parameters['Maximum_x'] = r.xMaximum()
                # parameters['Maximum_Y'] = r.yMaximum()
                # Use Try so we can get FME Exception
                # try:
                    # Run Workspace with parameters set in above directory
                    # runner.runWithParameters(workspace, parameters)
                    # or use promptRun to prompt for published parameters
                    #runner.promptRun(workspace)
                # except fmeobjects.FMEException as ex:
                    # Print out FME Exception if workspace failed
                    # print ex.message
                # else:
                    #Tell user the workspace ran
                    # msg = QMessageBox()
                    # msg.setIcon(QMessageBox.Information)
                    # msg.setText("The Workspace" + workspace + "ran successfully")
                # get rid of FMEWorkspace runner so we don't leave an FME process running
                # running = None
 
    def canvasMoveEvent(self, e):
        if not self.isEmittingPoint:
            return
        self.endPoint = self.toMapCoordinates(e.pos())
        self.showRect(self.startPoint, self.endPoint)

    def showRect(self, startPoint, endPoint):
        self.rubberBand.reset(QGis.Polygon)
        if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
            return

        point1 = QgsPoint(startPoint.x(), startPoint.y())
        point2 = QgsPoint(startPoint.x(), endPoint.y())
        point3 = QgsPoint(endPoint.x(), endPoint.y())
        point4 = QgsPoint(endPoint.x(), startPoint.y())

        self.rubberBand.addPoint(point1, False)
        self.rubberBand.addPoint(point2, False)
        self.rubberBand.addPoint(point3, False)
        self.rubberBand.addPoint(point4, True)    # true to update canvas
        self.rubberBand.setFillColor(QColor(255,255,0,50))
        self.rubberBand.show()

    def rectangle(self):
        if self.startPoint is None or self.endPoint is None:
            return None
        elif self.startPoint.x() == self.endPoint.x() or self.startPoint.y() == self.endPoint.y():
            return None

        return QgsRectangle(self.startPoint, self.endPoint)

    def deactivate(self):
        super(RectangleMapTool, self).deactivate()
        self.emit(SIGNAL("deactivated()"))
      
      
        
class MainApp(QApplication):
    def __init__(self):
        QApplication.__init__(self,[],True)
        wdg = MyWnd()
        wdg.show()
        self.exec_()

if __name__ == "__main__":
    import sys
    app = MainApp()

