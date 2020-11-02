# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 14:14:48 2020

@author: MoncadaMario63Y
"""
from opentrons import protocol_api
#from opentrons import simulate
import itertools
import json

#protocol = simulate.get_protocol_api('2.4')

metadata = {
    'protocolName': 'Magmax ThermoFisher/Viasure A',
    'author': 'Mercedes Perez Ruiz, Mario Moncada Soria, Andrés Montes Cabrero, Sergio Pérez Raya, Victoriano Giralt García',
    'source': 'Hospital Regional Universitario de Málaga',
    'apiLevel': '2.4',
    'description': 'Protocolo Magmax ThermoFisher A',
    'lastModification': '07/07/2020, 14:00:00'
}
''' EJEMPLO DE CONFIGURACIÓN
        configuracion = {
            'numero_muestras' : 96,
            'volumen_transferencia_muestras' : 200,
            '10_primera_punta_TipRack_1000' : 'A1',
            '11_primera_punta_TipRack_1000' : 'A1',
            'primera_punta_TipRack_20' : 'A1',
            'transferir_reactivos': True,
            'transferir_muestras': True,
            
            'reactivos': [{'nombre':'MB', 'volumen':1000,'velocidad_aspiracion' : 1.0, 'volumen_transferencia_reactivo':10, 'posicion':'A1', 'premezclado': True}, 
                         {'nombre':'PK', 'volumen':500,'velocidad_aspiracion' : 1.0, 'volumen_transferencia_reactivo':5, 'posicion':'A2', 'premezclado': False},
                         {'nombre':'CI', 'volumen':1000,'velocidad_aspiracion' : 1.0, 'volumen_transferencia_reactivo':10, 'posicion':'A3', 'premezclado': False}]
            }
    }'''
def run (protocol : protocol_api.ProtocolContext):

    #--------------CARGA DE LABWARE-----------------------------
    
    #Definición labware muestras de entrada.
    muestras_1 = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_screwcap', 4)
    muestras_2 = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_screwcap', 1)
    muestras_3 = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_screwcap', 6)
    muestras_4 = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_screwcap', 3)
    
    #Definición labware tubos de salida. cobas_96_deepwell_1600 'nest_96_wellplate_2ml_deep para simular'
    tubos_salida = protocol.load_labware('nest_96_deepwell_2ml',2)
    
    #Definicion labware de reactivos !!! Cambiado opentrons_24_aluminumblock_generic_2ml_screwcap
    tubos_reactivos = protocol.load_labware('opentrons_24_tuberack_nest_2ml_screwcap',7)
     
    #Definición TipRacks opentrons_96_tiprack_1000ul  biotix_96_tiprack_1000ul
    tipRack_1000_1 = protocol.load_labware('opentrons_96_tiprack_1000ul', 10)
    tipRack_1000_2 = protocol.load_labware('opentrons_96_tiprack_1000ul', 11)
    tipRack_20 = protocol.load_labware('opentrons_96_tiprack_20ul', 8)
    
    #CONFIGURACION
    configuracion = get_configuracion(protocol, [tipRack_1000_1,tipRack_1000_2,tipRack_20])
    #Definición pipetas
    p1000 = protocol.load_instrument('p1000_single_gen2', 'left', tip_racks=[tipRack_1000_1, tipRack_1000_2])
    p20 = protocol.load_instrument('p20_single_gen2', 'right', tip_racks=[tipRack_20])
    p20.flow_rate.blow_out = 40 # !!! Configuracion velocidad blow out
    #Obtener destinos, tubos de salida. 
    lista_destinos = get_lista_destinos(configuracion, tubos_salida)
    #Obtener origenes, tubos de muestras.
    lista_muestras = get_lista_muestras(configuracion, [muestras_1,muestras_2,muestras_3, muestras_4])
    
    #----- PROCESO ----------------------------------------------------------------------------------------------------
    if configuracion['transferir_reactivos']:
        for configuracion_reactivo in configuracion['reactivos']:
            if configuracion_reactivo['premezclado']:
                dispensar_reactivo_premezclado(p20, p1000, configuracion_reactivo, tubos_reactivos, lista_destinos)
            else:
                dispensar_reactivo(p20,configuracion_reactivo, tubos_reactivos, lista_destinos)
    if configuracion['transferir_muestras']:       
        transferir_muestras(p1000, configuracion, lista_muestras, lista_destinos)
    
   
def get_configuracion(protocol, lista_tipRacks):
    
    if not protocol.is_simulating():
        configuracion = {
            'numero_muestras' : 96,
            'volumen_transferencia_muestras' : 200,
            '10_primera_punta_TipRack_1000' : 'A1',
            '11_primera_punta_TipRack_1000' : 'A1',
            'primera_punta_TipRack_20' : 'A1',
            'transferir_reactivos': True,
            'transferir_muestras': True,
            
            'reactivos': [{'nombre':'MB', 'volumen':1000,'velocidad_aspiracion' : 1.0, 'volumen_transferencia_reactivo':10, 'posicion':'A1', 'premezclado': True}, 
                         {'nombre':'PK', 'volumen':500,'velocidad_aspiracion' : 1.0, 'volumen_transferencia_reactivo':5, 'posicion':'A2', 'premezclado': False},
                         {'nombre':'CI', 'volumen':1000,'velocidad_aspiracion' : 1.0, 'volumen_transferencia_reactivo':10, 'posicion':'A3', 'premezclado': False}]
            }
    else:
        configuracion = {
            'numero_muestras' : 96,
            'volumen_transferencia_muestras' : 200,
            '10_primera_punta_TipRack_1000' : 'A1',
            '11_primera_punta_TipRack_1000' : 'A1',
            'primera_punta_TipRack_20' : 'A1',
            'transferir_reactivos': True,
            'transferir_muestras': True,
            
            'reactivos': [{'nombre':'MB', 'volumen':1000,'velocidad_aspiracion' : 1.0, 'volumen_transferencia_reactivo':10, 'posicion':'A1', 'premezclado': True}, 
                         {'nombre':'PK', 'volumen':500,'velocidad_aspiracion' : 1.0, 'volumen_transferencia_reactivo':5, 'posicion':'A2', 'premezclado': False},
                         {'nombre':'CI', 'volumen':1000,'velocidad_aspiracion' : 1.0, 'volumen_transferencia_reactivo':10, 'posicion':'A3', 'premezclado': False}]
            }
    
    # Cálculo y configuracion del número de puntas en los tipRacks
    num_tips_1000 = 0
    num_tips_20 = 0       
    
    for tipRack in lista_tipRacks:
        
        if tipRack._well_definition['A1']['totalLiquidVolume'] == 1000 :
            pos_primera_punta = tipRack.parent+'_primera_punta_TipRack_1000' # !!! un poco cerdete . Operamos sobre la cadena para sacar la clave de configuracion del tipRack en concreto
            num_tips_1000 += configurar_tipRack(tipRack, configuracion[pos_primera_punta])
        elif tipRack._well_definition['A1']['totalLiquidVolume'] == 20 :
            num_tips_20 += configurar_tipRack(tipRack, configuracion['primera_punta_TipRack_20'])
        else:
            raise ValueError('Error en la configuración de los tipRacks')
            
    #Cálculo de las tips necesarias de 1000
    tips_1000_necesarias = 0
    tips_1000_necesarias += configuracion['numero_muestras'] # Es necesaria una punta de 1000 por cada muestra
    
    for reactivo in configuracion['reactivos']: #Es necesaria una punta de 1000 por cada reactivo con premezclado
        tips_1000_necesarias += reactivo['premezclado']
        
    #Cálculo de las tips necesarias de 20
    tips_20_necesarias = 0
    tips_20_necesarias = len(configuracion['reactivos'])* int(configuracion['numero_muestras']/16) # Es necesaria 1 por cada reactivo.
    
    #Comprobación volumen reactivos.
    for reactivo in configuracion['reactivos']:
        volumen_necesario = configuracion['numero_muestras'] * reactivo['volumen_transferencia_reactivo']
        if reactivo['volumen']< volumen_necesario:
            cadena_error = 'Volumen insuficiente reactivo: '+reactivo['nombre']+' Volumen mínimo necesario: '+str(volumen_necesario)+' Volumen configurado: '+str(reactivo['volumen'])+'.'
            raise ValueError(cadena_error)
            
    if tips_1000_necesarias > num_tips_1000:
        raise ValueError('Puntas de 1000uL insuficientes')
    if tips_20_necesarias > num_tips_20:
        raise ValueError('Puntas de 20uL insuficientes')
        
    if (configuracion['numero_muestras'] < 0) or (configuracion['numero_muestras'] > 96) :
        raise ValueError('Número de muestras fuera de parámetros')
        
    if (configuracion['volumen_transferencia_muestras'] < 50) or (configuracion['volumen_transferencia_muestras'] > 900) :
        raise ValueError('Volumen de transferencia de muestras incorrecto')
        
    
    return configuracion    
    
def configurar_tipRack(tipRack, posicion_primera_punta):  # Quitamos puntas de del tipRack, objeto Labware. Para que la api se apañe con las puntas que tiene el tipRack.
    
    # !!! Esto es una guarrada, hay que cambiarlo. 
    tipRack.wells_by_name()
    
    if len(posicion_primera_punta) < 3:
        posicion_primera_punta += ' '
        
    for well in tipRack.wells():
        
        if well.display_name[0:3] == posicion_primera_punta:
            break
        else:
            well.has_tip = False
    num_tips = get_remainingTips(tipRack)
    
    
    return num_tips

def get_remainingTips(labware): # Como sacar el numero de pipetas que quedan en un objeto de tipo Labware de tipracks usando la API
    
    if type(labware) is list: 
        remainingTips=0
        for tipRack in labware: 
            remainingTips+=sum([well.has_tip for well in tipRack.wells()])
        
    elif type(labware) is protocol_api.labware.Labware:
        remainingTips = sum([well.has_tip for well in labware.wells()]) # Como sacar el numero de pipetas que quedan en un tiprack
   
    else:
        remainingTips = 0
        
    return remainingTips
    
def getList_wellsByRow(labware): #Returns a list of wells ordered by row 
    
    labware_by_rows = labware.rows()
    
    return_list = list(itertools.chain.from_iterable(labware_by_rows))
    
    return return_list    
    
def get_lista_destinos(configuracion, labware_salida):
    
    lista_destinos = [labware_salida.wells()[i] for i in range(configuracion['numero_muestras'])]
    
    return lista_destinos
    
def get_lista_muestras(configuracion, lista_labware_muestras):
    
    lista = []
    
    for labware_muestras in lista_labware_muestras:
        lista += getList_wellsByRow(labware_muestras)
        
    lista_muestras = lista[:configuracion['numero_muestras']]
        
    return lista_muestras  

def calculo_altura(labware, volumen):
    
    if labware._well_definition['A1']['shape'] == 'circular':
        
        Area = 3.14159265359 * (labware._well_definition['A1']['diameter']/2)**2 
        Altura = volumen/Area
        
    elif labware._well_definition['A1']['shape'] == 'rectangular':
        Area = labware._well_definition['A1']['xDimension'] * labware._well_definition['A1']['yDimension']
        Altura = volumen/Area
        
    else:
        Altura = 1
        
    return Altura
       
def configuracion_altura_aspiracion(labware, volumen_actual, volumen_aspiracion, margen): #Devuelve altura sobre el fondo del pozo (bottom)
    
    altura_actual = calculo_altura(labware, volumen_actual)
    diferenciaAltura_trasAspiracion = calculo_altura(labware, volumen_aspiracion)
    
    altura_aspiracion = altura_actual - diferenciaAltura_trasAspiracion - margen
    
    altura_aspiracion = int(altura_aspiracion) # REDONDEO A LA BAJA
    
    if altura_aspiracion < margen:
        altura_aspiracion = 1
    
    if altura_aspiracion < 1:
        altura_aspiracion = 1
    
    return altura_aspiracion

def mezclado(pipeta,volumen, posicion, iteraciones = 3, velocidad_aspiracion = 1, velocidad_dispensacion = 5, altura_aspiracion = 5, altura_dispensacion = None): 

    
    if type(altura_dispensacion) is type(None):
        altura_dispensacion = altura_aspiracion
        

    for i in range(iteraciones):
        
        pipeta.aspirate(volumen, posicion.bottom(z = altura_aspiracion), rate=velocidad_aspiracion)
        pipeta.dispense(volumen, posicion.bottom(z = altura_dispensacion), rate=velocidad_dispensacion)
         
def transferir_muestras(pipeta, configuracion, lista_muestras, lista_destinos):
    
    #Variables 
    aire_gap = 10
    altura_aspiracion = 5
    
    numero_muestras = configuracion['numero_muestras']
    volumen_transferencia = configuracion['volumen_transferencia_muestras']
    
    altura_dispensacion = altura_aspiracion
    volumen_meclado_muestra = 200
    volumen_mezclado_salida = int(volumen_transferencia*0.75)
    
    
    for i in range(numero_muestras):
        
        pipeta.pick_up_tip()
        
        
        mezclado(pipeta, volumen_meclado_muestra,lista_muestras[i], iteraciones = 2, velocidad_aspiracion = 2, velocidad_dispensacion = 5, altura_aspiracion = 5)
        
        
        pipeta.aspirate(volumen_transferencia, lista_muestras[i].bottom(z = altura_aspiracion), rate = 0.75)
        
        pipeta.aspirate(aire_gap, lista_muestras[i].top(z = -10), rate = 2)
        
        pipeta.dispense(volumen_transferencia + aire_gap, lista_destinos[i].bottom(z = altura_dispensacion), rate = 5)
        
        
        mezclado(pipeta, volumen_mezclado_salida, lista_destinos[i], iteraciones = 2, velocidad_aspiracion = 2, velocidad_dispensacion = 5, altura_aspiracion = 1)
        
        pipeta.blow_out(lista_destinos[i].top(z = -10))
        
        pipeta.drop_tip(home_after = False)
 
def dispensar_reactivo(pipeta,configuracion_reactivo, labware_reactivos, lista_destinos):
    
    
    # Variables configuración.
    profundidad_aspiracion_sobre_superficie = 2
    altura_dispensacion = 10
    
    # Copiar valores del diccionario de configuración.
    origen = labware_reactivos.wells_by_name()[configuracion_reactivo['posicion']]
    volumen_aspiracion = configuracion_reactivo['volumen_transferencia_reactivo']
    volumen_dispensacion = volumen_aspiracion
    velocidad_aspiracion = configuracion_reactivo['velocidad_aspiracion']
    
    vol_sobredispensacion = 15 - volumen_aspiracion 
    
    if vol_sobredispensacion < 0:
        vol_sobredispensacion = 0
        
    #Dispensar reactivo.
    pipeta.pick_up_tip()
    
    i=0
    for destino in lista_destinos:
        
        if (i%16 == 0) and (i > 0): # Una punta nueva de 20 por cada 2 columnas.
            pipeta.drop_tip()
            pipeta.pick_up_tip()
            
        altura = configuracion_altura_aspiracion(labware_reactivos, configuracion_reactivo['volumen'],volumen_aspiracion,profundidad_aspiracion_sobre_superficie)
        
        pipeta.aspirate(vol_sobredispensacion,origen.top(), rate = 10)
        
        pipeta.aspirate(volumen_aspiracion,origen.bottom(z = altura), rate = velocidad_aspiracion)
        
        # Quitado para que dispense a 1mm pipeta.dispense(volumen_dispensacion + vol_sobredispensacion, destino.bottom(z = altura_dispensacion), rate=10)
        pipeta.dispense(volumen_dispensacion + vol_sobredispensacion, destino, rate=10)
        
        pipeta.blow_out(destino.top(z=-5))
        
        configuracion_reactivo['volumen'] -= volumen_aspiracion
        
        i+=1
    
    pipeta.drop_tip()
    
def dispensar_reactivo_premezclado(pipeta, pipeta_2, configuracion_reactivo, labware_reactivos, lista_destinos):
    
    # Variables configuración.
    profundidad_aspiracion_sobre_superficie = 2
    altura_dispensacion = 10
    
    # Copiar valores del diccionario de configuración.
    origen = labware_reactivos.wells_by_name()[configuracion_reactivo['posicion']]
    volumen_aspiracion = configuracion_reactivo['volumen_transferencia_reactivo']
    volumen_dispensacion = volumen_aspiracion
    
    velocidad_aspiracion = configuracion_reactivo['velocidad_aspiracion']
    
    vol_sobredispensacion = 15 - volumen_aspiracion 
    
    if vol_sobredispensacion < 0:
        vol_sobredispensacion = 0
        
    #--- Proceso de dispensacion ---    
    pipeta.pick_up_tip()
    pipeta_2.pick_up_tip()
    
    i = 0
    for destino in lista_destinos:
        
        if (i%16 == 0) and (i > 0): # Una punta nueva de 20 por cada 2 columnas.
            pipeta.drop_tip()
            pipeta.pick_up_tip()
        
        #--- Mezclado cada columna---
        if (i%8 == 0): 
            
            if i == 0: # Mezclar 8 veces al comienzo
                num_iteraciones = 10
            else:
                num_iteraciones = 3
                
            volumen_mezclado = int(configuracion_reactivo['volumen']/2) 
            if volumen_mezclado > 800:
                volumen_mezclado = 800
                
            altura_mezclado = configuracion_altura_aspiracion(labware_reactivos, configuracion_reactivo['volumen'],volumen_mezclado,profundidad_aspiracion_sobre_superficie)
            
            mezclado(pipeta_2 , volumen_mezclado, origen, iteraciones = num_iteraciones, velocidad_aspiracion = 3, velocidad_dispensacion = 8, altura_aspiracion = altura_mezclado, altura_dispensacion = 1)
            
            pipeta_2.blow_out(origen.top(z=-10))
        #-----------------------------
            
            
        altura = configuracion_altura_aspiracion(labware_reactivos, configuracion_reactivo['volumen'],volumen_aspiracion,profundidad_aspiracion_sobre_superficie)
        
        pipeta.aspirate(vol_sobredispensacion,origen.top(), rate = 10)
        
        pipeta.aspirate(volumen_aspiracion,origen.bottom(z = altura), rate = velocidad_aspiracion)
        
        #Quitado para que dispense a un mililmetro pipeta.dispense(volumen_dispensacion + vol_sobredispensacion, destino.bottom(z = altura_dispensacion), rate=10)
        pipeta.dispense(volumen_dispensacion + vol_sobredispensacion, destino, rate=10)
        
        
        pipeta.blow_out(destino.top(z=-5))
        
        configuracion_reactivo['volumen'] -= volumen_aspiracion
        
        i += 1
    
    pipeta.drop_tip()
    pipeta_2.drop_tip()





#run(protocol)

'''
 CAMBIOS C

07/07/2020:
    - Se cambia definicion del labware de salida de deep well de nest a cobas


'''