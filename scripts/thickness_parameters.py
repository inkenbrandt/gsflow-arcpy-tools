#--------------------------------
# Name:         thickness_parameters.py
# Purpose:      GSFLOW thickness parameters
# Notes:        ArcGIS 10.2 Version
# Author:       Charles Morton
# Created       2015-04-27
# Python:       2.7
#--------------------------------

import argparse
from collections import defaultdict
import ConfigParser
import datetime as dt
import logging
import os
import re
import sys
##import tempfile

import arcpy
from arcpy import env
from arcpy.sa import *
##import numpy as np

from support_functions import *

################################################################################

def gsflow_thickness_parameters(config_path, overwrite_flag=False, debug_flag=False):
    """Calculate GSFLOW Thickness Parameters

    Args:
        config_file: Project config file path
        ovewrite_flag: boolean, overwrite existing files
        debug_flag: boolean, enable debug level logging
    Returns:
        None
    """

    try:
        ## Initialize hru_parameters class
        hru = hru_parameters(config_path)

        ## Open input parameter config file
        inputs_cfg = ConfigParser.ConfigParser()
        try:
            inputs_cfg.readfp(open(config_path))
        except:
            logging.error('\nERROR: Config file could not be read, '+
                          'is not an input file, or does not exist\n'+
                          'ERROR: config_file = {0}\n').format(config_path)
            raise SystemExit()

        ## Log DEBUG to file
        log_file_name = 'gsflow_thickness_log.txt'
        log_console = logging.FileHandler(
            filename=os.path.join(hru.log_ws, log_file_name), mode='w')
        log_console.setLevel(logging.DEBUG)
        log_console.setFormatter(logging.Formatter('%(message)s'))
        logging.getLogger('').addHandler(log_console)
        logging.info('\nGSFLOW Thickness Parameters')

        ## Input folders
        ##thickness_ws = os.path.join(parameter_ws, 'thickness_rasters')
        ##if not os.path.isdir(thickness_ws):
        ##    os.mkdir(thickness_ws)

        ## Check input paths
        if not arcpy.Exists(hru.polygon_path):
            logging.error(
                '\nERROR: Fishnet ({0}) does not exist'.format(
                    hru.polygon_path))
            raise SystemExit()

        ## Set ArcGIS environment variables
        arcpy.CheckOutExtension('Spatial')
        env.overwriteOutput = True
        env.pyramid = 'PYRAMIDS -1'
        ##env.pyramid = 'PYRAMIDS 0'
        env.workspace = parameter_ws
        ##env.workspace = thickness_ws
		env.scratchWorkspace = hru.scratch_ws

        ## Check field
        logging.info('\nAdding thickness fields if necessary')
        add_field_func(hru_polygon_path, hru.alluv_field, 'FLOAT')
        add_field_func(hru_polygon_path, hru.alluv_thick_field, 'FLOAT')
        add_field_func(hru_polygon_path, hru.lay1_thick_field, 'FLOAT')
        add_field_func(hru_polygon_path, hru.lay2_thick_field, 'FLOAT')
        add_field_func(hru_polygon_path, hru.lay3_thick_field, 'FLOAT')
        add_field_func(hru_polygon_path, hru.lay4_thick_field, 'FLOAT')
        add_field_func(hru_polygon_path, hru.lay1_bottom_field, 'FLOAT')
        add_field_func(hru_polygon_path, hru.lay2_bottom_field, 'FLOAT')
        add_field_func(hru_polygon_path, hru.lay3_bottom_field, 'FLOAT')
        add_field_func(hru_polygon_path, hru.lay4_bottom_field, 'FLOAT')


        ## Make a fishnet layer for calculating fields
        hru_polygon_layer = "hru_polygon_layer"
        arcpy.MakeFeatureLayer_management(
            hru.polygon_path, hru_polygon_layer)
        arcpy.SelectLayerByAttribute_management(
            hru_polygon_layer, "NEW_SELECTION",
            '"{0}" >= 0 '.format(hru.type_in_field))

        ## Calculate layer bottom values
        logging.info('Calculating {0}'.format(hru.lay1_bottom_field))
        arcpy.CalculateField_management(
            hru_polygon_layer, hru.lay1_bottom_field,
            '!{0}! - !{1}!'.format(hru.dem_adj_field, hru.lay1_thick_field),
            'PYTHON')      

        logging.info('Calculating {0}'.format(hru.lay2_bottom_field))
        arcpy.CalculateField_management(
            hru_polygon_layer, hru.lay2_bottom_field,
            '!{0}! - !{1}!'.format(hru.lay1_bottom_field, hru.lay2_thick_field),
            'PYTHON')      

        logging.info('Calculating {0}'.format(hru.lay3_bottom_field))
        arcpy.CalculateField_management(
            hru_polygon_layer, hru.lay3_bottom_field,
            '!{0}! - !{1}!'.format(hru.lay2_bottom_field, hru.lay3_thick_field),
            'PYTHON')      

        logging.info('Calculating {0}'.format(hru.lay4_bottom_field))
        arcpy.CalculateField_management(
            hru_polygon_layer, hru.lay4_bottom_field,
            '!{0}! - !{1}!'.format(hru.lay3_bottom_field, hru.lay4_thick_field),
            'PYTHON')      

        ## Cleanup
        arcpy.SelectLayerByAttribute_management(
            hru_polygon_layer, "CLEAR_SELECTION")
        arcpy.Delete_management(hru_polygon_layer)
        del hru_polygon_layer

    except:
        logging.exception('Unhandled Exception Error\n\n')
        raw_input('ENTER')

    finally:
        try: arcpy.CheckInExtension('Spatial')
        except: pass
        ##arcpy.ResetEnvironments()

################################################################################

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Alluvial Thickness Parameters',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-i', '--ini', required=True,
        help='Project input file', metavar='PATH')
    parser.add_argument(
        '-o', '--overwrite', default=False, action="store_true", 
        help='Force overwrite of existing files')
    parser.add_argument(
        '--debug', default=logging.INFO, const=logging.DEBUG,
        help='Debug level logging', action="store_const", dest="loglevel")
    args = parser.parse_args()

    ## Create Basic Logger
    logging.basicConfig(level=args.loglevel, format='%(message)s')
    
    #### Get GSFLOW config file
    ##ini_re = re.compile('\w*.ini$', re.I)
    ##try: 
    ##    ini_path = sys.argv[1]
    ##except IndexError:
    ##    ini_path = get_ini_file(workspace, ini_re, 'gsflow_thickness_parameters')
    ##del ini_re

    ## Run Information
    logging.info('\n{0}'.format('#'*80))
    log_f = '{0:<20s} {1}'
    logging.info(log_f.format(
        'Run Time Stamp:', dt.datetime.now().isoformat(' ')))
    logging.info(log_f.format('Current Directory:', os.getcwd()))
    logging.info(log_f.format('Script:', os.path.basename(sys.argv[0])))

    ## Calculate GSFLOW Thickness Parameters
    gsflow_thickness_parameters(
        config_path=args.ini, overwrite_flag=args.overwrite,
        debug_flag=args.loglevel==logging.DEBUG)