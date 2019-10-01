# Import PySide classes
import sys
from PySide.QtCore import *
from PySide.QtGui import *

from MorphingGUI import *
from Morphing import *

class BlenderGUI(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(BlenderGUI, self).__init__(parent)
        self.setupUi(self)

        #variables i used initialized here
        self.startImg = None
        self.endImg = None
        self.startImgArray = None
        self.endImgArray = None
        self.startPoints = None
        self.startPointsFile = None
        self.startPointsFileMode = None
        self.endPoints = None
        self.endPointsFile = None
        self.endPointsFileMode = None
        self.startScene = None
        self.prevStartScene = None
        self.endScene = None
        self.prevEndScene = None
        self.alpha = None
        self.state = 0
        self.startPos = None
        self.endPos = None
        self.startEllipse = None
        self.endEllipse = None

        self.loadStartPB.clicked.connect(self.loadStart)
        self.loadEndPB.clicked.connect(self.loadEnd)
        self.alphaSlide.valueChanged.connect(self.readAlpha)
        self.blendPB.clicked.connect(self.doitson)
        self.trianglesBox.stateChanged.connect(self.triFunc)


    def persist(self):
        painter = QPainter()
        painter.begin(self.startImg)
        painter.setPen(QPen(Qt.blue))
        painter.setBrush(Qt.blue)
        painter.drawEllipse(QPointF(self.startPos[0],self.startPos[1]),7,7)
        painter.end()
        self.startScene.addPixmap(self.startImg.scaled(400,300,Qt.KeepAspectRatio, Qt.SmoothTransformation))
        if self.startPointsFileMode == "w":
            self.startPoints = np.array([self.startPos])
            self.startPointsFileMode = "a"
            with open(self.startPointsFile, "w") as myFile:
                myFile.write("{0:6d}{1:6d}\n".format(int(self.startPos[0]), int(self.startPos[1])))
        else:
            self.startPoints = np.append(self.startPoints, [self.startPos], axis=0)
            with open(self.startPointsFile, "a") as myFile:
                myFile.write("{0:6d}{1:6d}\n".format(int(self.startPos[0]), int(self.startPos[1])))

        painter.begin(self.endImg)
        painter.setPen(QPen(Qt.blue))
        painter.setBrush(Qt.blue)
        painter.drawEllipse(QPointF(self.endPos[0],self.endPos[1]),7,7)
        painter.end()
        self.endScene.addPixmap(self.endImg.scaled(400,300,Qt.KeepAspectRatio, Qt.SmoothTransformation))
        if self.endPointsFileMode == "w":
            self.endPoints = np.array([self.endPos])
            self.endPointsFileMode = "a"
            with open(self.endPointsFile, "w") as myFile:
                myFile.write("{0:6d}{1:6d}\n".format(int(self.endPos[0]), int(self.endPos[1])))
        else:
            self.endPoints = np.append(self.endPoints, [self.endPos], axis=0)
            with open(self.endPointsFile, "a") as myFile:
                myFile.write("{0:6d}{1:6d}\n".format(int(self.endPos[0]), int(self.endPos[1])))

        if self.trianglesBox.isChecked() == True:
            self.showTriangles()


    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonPress and source == self.image1View.viewport():
            if self.state == 1:
                self.state = 2
                self.startEllipse = self.startScene.addEllipse(event.pos().x(), event.pos().y(), 6, 6, QPen(Qt.green), QBrush(Qt.green))
                self.startPos = [event.pos().x()*self.ratio[0], event.pos().y()*self.ratio[1]]
            elif self.state == 3:
                self.state = 2
                self.persist()

                self.startEllipse = self.startScene.addEllipse(event.pos().x(), event.pos().y(), 6, 6, QPen(Qt.green), QBrush(Qt.green))
                self.startPos = [event.pos().x()*self.ratio[0], event.pos().y()*self.ratio[1]]
            return True


        elif event.type() == QEvent.MouseButtonPress and source == self.image2View.viewport():
            if self.state == 2:
                self.state = 3
                self.endEllipse = self.endScene.addEllipse(event.pos().x(), event.pos().y(), 6, 6, QPen(Qt.green), QBrush(Qt.green))
                self.endPos = [event.pos().x()*self.ratio[0], event.pos().y()*self.ratio[1]]

            return True

        elif event.type() == QEvent.MouseButtonPress and source != self.image2View.viewport():
            if self.state == 3:
                self.state = 1
                self.persist()
                #self.startScene.addEllipse(self.startPos[0], self.startPos[1], 4, 4, QPen(Qt.blue), QBrush(Qt.blue))
                #self.endScene.addEllipse(self.endPos[0], self.endPos[1], 4, 4, QPen(Qt.blue), QBrush(Qt.blue))
                return True
            else:
                return False

        elif event.type() == QEvent.KeyPress:
            if self.state == 2 and event.key() == Qt.Key_Backspace:
                self.state = 1
                self.startScene.removeItem(self.startEllipse)
                return True
            elif self.state == 3 and event.key() == Qt.Key_Backspace:
                self.state = 2
                self.endScene.removeItem(self.endEllipse)
                return True
            else:
                return False
        else:
            return False



    def triFunc(self):
        if self.trianglesBox.isChecked() == True:
            try:
                self.showTriangles()
            except:
                pass
        else:
            self.clearTriangles()

    def clearTriangles(self):
        self.startScene.addPixmap(self.startImg.scaled(400,300,Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.endScene.addPixmap(self.endImg.scaled(400,300,Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def showTriangles(self):
        startTriangles = Delaunay(self.startPoints)

        painter = QPainter()
        image = self.startImg.copy()
        painter.begin(image)
        pen = QPen(Qt.blue)
        pen.setWidth(3)
        painter.setPen(pen)
        for item in startTriangles.simplices:
            startPts = np.array([[self.startPoints[item[0],0], self.startPoints[item[0], 1]],
                        [self.startPoints[item[1],0], self.startPoints[item[1], 1]],
                        [self.startPoints[item[2],0], self.startPoints[item[2], 1]]], dtype=np.float64)

            painter.drawLine(QPointF(startPts[0,0],startPts[0,1]), QPointF(startPts[1,0],startPts[1,1]))
            painter.drawLine(QPointF(startPts[1,0],startPts[1,1]), QPointF(startPts[2,0],startPts[2,1]))
            painter.drawLine(QPointF(startPts[2,0],startPts[2,1]), QPointF(startPts[0,0],startPts[0,1]))
        painter.end()
        self.startScene.addPixmap(image.scaled(400,300,Qt.KeepAspectRatio, Qt.SmoothTransformation))

        image = self.endImg.copy()
        painter.begin(image)
        painter.setPen(pen)
        for item in startTriangles.simplices:
            endPts = np.array([[self.endPoints[item[0],0], self.endPoints[item[0], 1]],
                      [self.endPoints[item[1],0], self.endPoints[item[1], 1]],
                      [self.endPoints[item[2],0], self.endPoints[item[2], 1]]], dtype = np.float64)

            painter.drawLine(QPointF(endPts[0,0],endPts[0,1]), QPointF(endPts[1,0],endPts[1,1]))
            painter.drawLine(QPointF(endPts[1,0],endPts[1,1]), QPointF(endPts[2,0],endPts[2,1]))
            painter.drawLine(QPointF(endPts[2,0],endPts[2,1]), QPointF(endPts[0,0],endPts[0,1]))
        painter.end()
        self.endScene.addPixmap(image.scaled(400,300,Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def doitson(self):
        if self.startImgArray.ndim == 2:
            tmp = Blender(self.startImgArray, self.startPoints, self.endImgArray, self.endPoints)
        elif self.startImgArray.ndim == 3:
            tmp = ColorBlender(self.startImgArray, self.startPoints, self.endImgArray, self.endPoints)
        tmp2 = tmp.getBlendedImage(self.alpha)
        imageio.imsave('blended.jpg', tmp2)
        blendedImg = QPixmap('blended.jpg')
        scene = QGraphicsScene()
        scene.addPixmap(blendedImg.scaled(self.blendedView.size()))
        self.blendedView.setScene(scene)
        self.blendedView.setSceneRect(QRectF(self.blendedView.viewport().rect()))
        self.blendedView.show()

    def readAlpha(self):
        self.alpha = np.round(self.alphaSlide.value()*0.05,2)
        self.alphaValue.setText(str(self.alpha))

    def loadStart(self):
        """
        Obtain a file name from a file dialog, and pass it on to the loading method. This is to facilitate automated
        testing. Invoke this method when clicking on the 'load' button.

        *** DO NOT MODIFY THIS METHOD! ***
        """
        filePath, _ = QFileDialog.getOpenFileName(self, caption='Open PNG or JPG file ...', filter="PNG and JPG files (*.jpg *.png)")

        if not filePath:
            return

        self.loadStartFromFile(filePath)
        if self.startImg and self.endImg:
            self.state = 1
            self.blendPB.setDisabled(False)
            self.trianglesBox.setDisabled(False)
            self.alphaSlide.setEnabled(True)
            self.alphaValue.setEnabled(True)
            self.image1View.viewport().installEventFilter(self)
            self.image2View.viewport().installEventFilter(self)
            self.installEventFilter(self)

    def loadStartFromFile(self, filePath):
        self.startImg = QPixmap(filePath)
        self.startImgArray = np.array(imageio.imread(filePath))
        self.startScene = QGraphicsScene()
        self.startScene.addPixmap(self.startImg.scaled(400,300,Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.ratio = [self.startImgArray.shape[1]/400, self.startImgArray.shape[0]/300]

        self.image1View.setScene(self.startScene)
        self.image1View.setSceneRect(QRectF(self.image1View.viewport().rect()))
        #self.image1View.show()

        try:
            self.startPointsFile = filePath + '.txt'
            self.startPoints = np.loadtxt(self.startPointsFile)
        except:
            self.startPointsFileMode = "w"
        else:
            self.startPointsFileMode = "a"
            painter = QPainter()
            painter.begin(self.startImg)
            painter.setPen(QPen(Qt.red))
            painter.setBrush(Qt.red)
            for x,y in self.startPoints:
                painter.drawEllipse(QPointF(x,y),6,6)
            painter.end()
            self.startScene.addPixmap(self.startImg.scaled(400,300,Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def loadEnd(self):
        """
        Obtain a file name from a file dialog, and pass it on to the loading method. This is to facilitate automated
        testing. Invoke this method when clicking on the 'load' button.

        *** DO NOT MODIFY THIS METHOD! ***
        """
        filePath, _ = QFileDialog.getOpenFileName(self, caption='Open PNG or JPG file ...', filter="PNG and JPG files (*.jpg *.png)")

        if not filePath:
            return

        self.loadEndFromFile(filePath)
        if self.startImg and self.endImg:
            self.state = 1
            self.blendPB.setDisabled(False)
            self.trianglesBox.setDisabled(False)
            self.alphaSlide.setEnabled(True)
            self.alphaValue.setEnabled(True)
            self.image1View.viewport().installEventFilter(self)
            self.image2View.viewport().installEventFilter(self)
            self.installEventFilter(self)

    def loadEndFromFile(self, filePath):
        self.endImg = QPixmap(filePath)
        self.endImgArray = np.array(imageio.imread(filePath))
        self.endScene = QGraphicsScene()
        self.endScene.addPixmap(self.endImg.scaled(400,300,Qt.KeepAspectRatio, Qt.SmoothTransformation))

        self.image2View.setScene(self.endScene)
        self.image2View.setSceneRect(QRectF(self.image1View.viewport().rect()))
        #self.image2View.show()

        try:
            self.endPointsFile = filePath + '.txt'
            self.endPoints = np.loadtxt(self.endPointsFile)
        except:
            self.endPointsFileMode = "w"
        else:
            self.endPointsFileMode = "a"
            painter = QPainter()
            painter.begin(self.endImg)
            painter.setPen(QPen(Qt.red))
            painter.setBrush(Qt.red)
            for x,y in self.endPoints:
                painter.drawEllipse(QPointF(x,y),6,6)
            painter.end()
            self.endScene.addPixmap(self.endImg.scaled(400,300,Qt.KeepAspectRatio, Qt.SmoothTransformation))


if __name__=="__main__":
    currentApp = QApplication(sys.argv)
    currentForm = BlenderGUI()

    currentForm.show()
    currentApp.exec_()


'''
class GraphicsScene(QGraphicsScene):
    def __init__(self, parent=None):
        QGraphicsScene.__init__(self, parent)
        #self.setSceneRect(-100, -100, 200, 200)

    def mousePressEvent(self, event):
        pen = QPen(QtCore.Qt.green)
        brush = QBrush(QtCore.Qt.green)
        x = event.scenePos().x()
        y = event.scenePos().y()
        self.addEllipse(x, y, 4, 4, pen, brush)
'''