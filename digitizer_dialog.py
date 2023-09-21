# -*- coding: utf-8 -*-
"""
/***************************************************************************
 digitizerDialog
                                 A QGIS plugin
 digitizer
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-09-14
        git sha              : $Format:%H$
        copyright            : (C) 2023 by mafaz
        email                : wearemafaz@gmail.com
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

import os
import pathlib
from zipfile import ZipFile, ZIP_DEFLATED
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from PyQt5.QtCore import QVariant
from qgis.core import QgsField, QgsExpression, QgsFeature
from qgis.core import QgsExpressionContextUtils
from qgis.core import QgsExpressionContext
from qgis.core import QgsProject, QgsVectorLayer, QgsFeature
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from qgis.core import QgsVectorFileWriter, QgsProject
import processing



# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'digitizer_dialog_base.ui'))


class digitizerDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(digitizerDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        layers = QgsProject.instance().layerTreeRoot().children()
        self.dig_line.addItems([layer.name() for layer in layers])
        selected_line = self.dig_line.currentIndex()
        self.digitized_line = layers[selected_line].layer() # ?????????
        self.dl_ok.clicked.connect(self.convertLineToPolygon)
        self.tl_link_ok.clicked.connect(self.linkTl)
        self.cancel.clicked.connect(self.onClosePlugin)
        self.cancel_2.clicked.connect(self.onClosePlugin)
        self.cancel_3.clicked.connect(self.onClosePlugin)

        self.polygon.addItems([layer.name() for layer in layers])

        # tl_layer
        self.ten_lis.addItems([layer.name() for layer in layers])

        # meta_layer
        self.metadata.addItems([layer.name() for layer in layers])

        # save output

        self.report_browse.clicked.connect(self.report_folder)
        self.req_submit.clicked.connect(self.requisition)
        self.output_ok.clicked.connect(self.output_vector)

        #layers = QgsProject.instance().layerTreeRoot().children() #add layers loaded to qgis

    def onClosePlugin(self): # Close the plugin's dialog when cancel is pressed
      self.close()

    def convertLineToPolygon(self): # polygonize
        selected_line_layer_name = self.dig_line.currentText()
        selected_line_layer = QgsProject.instance().mapLayersByName(selected_line_layer_name)[0]

        polygonized_layer_name = f"{selected_line_layer_name}_polygonized"
        polygonized_layer = processing.run("native:polygonize", {
            'INPUT': selected_line_layer,
            'KEEP_FIELDS': False,
            'OUTPUT': 'memory:' + 'polygonized_layer' # Save the output as a temporary memory layer
        })['OUTPUT']

        layer_provider = polygonized_layer.dataProvider()
        layer_provider.addAttributes([QgsField("Lot_No", QVariant.String)])
        pv = polygonized_layer.dataProvider()
        pv.addAttributes([QgsField("area", QVariant.Double)])
        polygonized_layer.updateFields()

        polygonized_layer.startEditing()
        features = polygonized_layer.getFeatures()
        for feature in features:
            feature['area'] = feature.geometry().area()
            polygonized_layer.updateFeature(feature)
        polygonized_layer.commitChanges()
        QgsProject.instance().addMapLayer(polygonized_layer)
        print(f"Polygonized layer '{polygonized_layer_name}' added to the project.")

    def linkTl(self):
        selected_polygon_layer_name = self.polygon.currentText() # select polygon layer
        selected_polygon_layer = QgsProject.instance().mapLayersByName(selected_polygon_layer_name)[0]

        selected_ten_list_layer_name = self.ten_lis.currentText() #select tl
        selected_ten_list_layer = QgsProject.instance().mapLayersByName(selected_ten_list_layer_name)[0]

        selected_meta_data_layer_name = self.metadata.currentText() # select metadata file
        selected_meta_data_layer = QgsProject.instance().mapLayersByName(selected_meta_data_layer_name)[0]

        # Joining parameters for tl and polygon
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'Lot_No',  # Adjust to the actual field name
            'FIELDS_TO_COPY': [''],  # List of fields to copy from the join layer
            'FIELD_2': 'lot_no',  # Adjust to the actual field name
            'INPUT': selected_polygon_layer,
            'INPUT_2': selected_ten_list_layer,
            'METHOD': 0,  # Create separate feature for each matching feature (one-to-many)
            'PREFIX': '',
            'OUTPUT': 'memory:'  # Save the output as a temporary memory layer
        }

        # Perform the join using the processing algorithm
        joined_layer = processing.run('native:joinattributestable', alg_params)['OUTPUT']

        # Add the joined layer to the project
        QgsProject.instance().addMapLayer(joined_layer)
        print(f"Joined layer added to the project.")

        # scale
        for source_feature in selected_meta_data_layer.getFeatures():
            attributes = source_feature.attributes()
            scale_value = attributes[8]
            self.sc = float(scale_value)
            if self.sc == 1:
                self.sf = 1
            elif self.sc == 2:
                self.sf = 2
            elif self.sc == 3:
                self.sf = 4
            elif self.sc == 4:
                self.sf = 8
            elif self.sc == 5:
                self.sf = 16
            elif self.sc == 6:
                self.sf = 32
            elif self.sc == 7:
                self.sf = 40
            elif self.sc == 8:
                self.sf = 60
            elif self.sc == 9:
                self.sf = 0.5
            elif self.sc == 10:
                self.sf = 1
            elif self.sc == 11:
                self.sf = 2
            elif self.sc == 12:
                self.sf = 4
            elif self.sc == 13:
                self.sf = 10
            elif self.sc == 14:
                self.sf = 50
            elif self.sc == 15:
                self.sf = 63.5
            elif self.sc == 16:
                self.sf = 63.5
            else:
                self.sf=0.001
        # this formula with the factors taken from dsr 2008 & 1970

        # Original Scale of the Plan
            #  1 - 1 inch into 1Ch
            #  2 - 1 inch into 2Ch
            #  3 - 1 inch into 4Ch
            #  4 - 1 inch into 8Ch
            #  5 - 1 inch into 16Ch
            #  6 - 1 inch into 32Ch
            #  7 - 1 inch into 40Ch
            #  8 - 1 inch into 60Ch
            #  9 - 1:500                SF-0.5
            #  10 - 1:1000              SF-1
            #  11 - 1:2000              SF-2
            #  12 - 1:4000
            #  13 - 1:10,000
            #  14 - 1:50,000
            #  15 - 1:63,500 (1 inch into 1Mile)
            #  16 - 1:250,000

        print(f"Scale factor for plan scale is '{self.sf}'.")
        pv = joined_layer.dataProvider()
        pv.addAttributes([QgsField('error', QVariant.Double), QgsField('calc', QVariant.Double),QgsField('tollerance', QVariant.Double),QgsField('checking', QVariant.String)])
        joined_layer.updateFields()
        expression1 = QgsExpression('abs("area" / 10000)-coalesce("pcl_if_elh", 0)+(coalesce("pcl_if_elha", 0) + coalesce("pcl_if_elr", 0) / 4 + coalesce("pcl_if_elp", 0) / 160)* 0.4047')
        expression2 = QgsExpression('0.4*sqrt(coalesce("pcl_if_elh", 0)*2.4711*160+(coalesce("pcl_if_ela", 0)*160 + coalesce("pcl_if_elr", 0) *40 + coalesce("pcl_if_elp", 0) ))*25.2924')

        context = QgsExpressionContext()
        context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(joined_layer))
        joined_layer.startEditing()
        features = joined_layer.getFeatures()
        for feature in features:
            context.setFeature(feature)
            feature['error'] = expression1.evaluate(context)
            feature['calc'] = expression2.evaluate(context)

            # feature['calc'] = float(feature['calc'])  # Convert QVariant to float
            # self.sf = float(self.sf)  # Convert QVariant to float

            feature['tollerance'] = feature['calc'] * self.sf / 4



            joined_layer.updateFeature(feature)
        joined_layer.commitChanges()
        QgsProject.instance().addMapLayer(joined_layer)


        # Filter the features based on tolerance and error values
        filtered_features = []

        for feature in joined_layer.getFeatures():
            error_value = feature['error']
            tolerance_value = feature['tollerance']

            # Check if tolerance is lower than error
            if tolerance_value < error_value:
                filtered_features.append(feature)

        # Create a new memory layer for the filtered features
        Extent_error = QgsVectorLayer(
            'Polygon?crs=' + joined_layer.crs().authid(),
            'Error_Polygons',
            'memory'
        )

        # Add attributes to the filtered layer (you can customize this based on your needs)
        Extent_error.dataProvider().addAttributes(joined_layer.fields())
        Extent_error.updateFields()

        # Add filtered features to the filtered layer
        Extent_error.dataProvider().addFeatures(filtered_features)

        # Add the filtered layer to the project
        QgsProject.instance().addMapLayer(Extent_error)

        print("Polygons that extent mismatch added to the project")


    def report_folder(self):

        directory = QFileDialog.getExistingDirectory(self, 'Select directory',
                                                     'D:\\codefirst.io\\PyQt5 tutorials\\Browse Files')

        self.report_filename.setText(directory) # browse the directory where report folder presents
        self.report_dir = directory



    def requisition(self):
        self.requition_no = self.req_no.text()
        print(self.requition_no)

    def output_vector(self):


        #full_path = self.report_dir + 'report.txt'
        full_path = os.path.join(self.report_dir, 'reports', 'report.txt')

        layer_name_1 = "output"
        layer_name_2 ="Error_Polygons"
        layer_1 = QgsProject.instance().mapLayersByName(layer_name_1)[0]
        layer_2 = QgsProject.instance().mapLayersByName(layer_name_2)[0]


        feature_count_pcl = layer_1.featureCount()
        feature_count_error = layer_2.featureCount()
       
        content = f"Total no. of Lots: {feature_count_pcl}\nTotal no. of Lot extent Errors: {feature_count_error}"
        with open(full_path, 'w') as file:
            file.write(content)
            print(f"Error report 'report.txt' created successfully in {full_path}.")

        # Define the output file path using self.report_dir
        #error_path = self.report_dir + "/reports"+"/Error_polygons.shp"  # Change the file extension and format as needed

        # Define the output file path using self.report_dir
        error_path = os.path.join(self.report_dir, "reports",
                                  "Error_polygons.shp")  # Change the file extension and format as needed

        # Create a QgsVectorFileWriter instance to write the layer to a file
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "ESRI Shapefile"  # Change the format as needed
        options.fileEncoding = "UTF-8"  # Change the encoding as needed

        # Use the QgsVectorFileWriter.writeAsVectorFormat method to save the layer
        result, error_message = QgsVectorFileWriter.writeAsVectorFormat(layer_2, error_path, options)

        if result == QgsVectorFileWriter.NoError:
            print(f" '{layer_name_2}' was saved to {error_path}")
        else:
            print(f"Error saving layer '{layer_name_2}': {error_message}")

#----------------------------------------------------------------------------


        # Define the path for the zip file within self.report_dir
        parts = self.report_dir.split("/")

        dir_to_zip = self.requition_no # Get the last part (directory name)Z
        # Specify the full path for the ZIP file
        zip_file_path = os.path.join(os.path.dirname(self.report_dir), dir_to_zip + ".zip")

        print("zipfile name: " + dir_to_zip)
        print("zipfile path: " + zip_file_path)

        # Create a Path object for the directory to zip
        folder = pathlib.Path(self.report_dir)
        with ZipFile(zip_file_path, 'w', ZIP_DEFLATED) as zip:
            # Walk through the self.report_dir directory and add all files and subdirectories
            for root, dirs, files in os.walk(self.report_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.report_dir)
                    zip.write(file_path, arcname=arcname)

        print("zip folder has been created")