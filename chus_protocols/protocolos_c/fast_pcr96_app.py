#!/home/laboratorio/anaconda2/bin/python


from gooey import Gooey, GooeyParser
import subprocess
import datetime



robodict = {'SCR1':'69.101.94.152', 
	    'SCR2':'69.101.94.151'}
splitmethods = ['genomica', 
		'vircell']
LIBRARY_PATH = '../../library/'


### Gooey decorator

@Gooey(program_name='Opentrons',
       program_description="Fast PCR Setup 96",
       default_size=(500, 700),
       show_stop_warning = True,
       force_stop_is_error = True,
       show_success_modal = False,
       show_failure_modal = False,
       show_restart_button = False,
       language = 'spanish',
       image_dir = '../../library/',
       text_color = '#ffffff',
       body_bg_color = '#0589f8',
       menu=[{
        'name': 'Axuda',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'Sobre o programa',
                'name': 'Opentrons App Galicia',
                'description': 'App para manexo sinxelo de protocolos',
                'version': '1.1',
                'copyright': '2020',
                'website': 'https://github.com/IPardelo/ot2-covid19',
                'developer': 'Victoria Suárez Ulloa, Ismael Castiñeira Paz'
            }]
       }]
)
#       navigation='TABBED')


def parse_args():

    parser = GooeyParser()

    robots = parser.add_argument("Robots",
            metavar='ROBOT',
            action='store',
            choices=['SCR1', 'SCR2'],
            default='SCR1')

# text field to input number of samples
    samples = parser.add_argument("samples", 
            metavar='NÚMERO DE MUESTRAS',
            type=int,
            help="Inserte el numero de muestras", 
            action="store")

# menus for type of library kit and type of tube
    prot_group = parser.add_argument_group('Parámetros protocolo')    
    prot_group.add_argument("modes",
            metavar='KIT DE REACTIVOS',
            action = 'store',
            choices=['seegene-2019-ncov', 'seegene-sars-cov2', 'thermofisher', 'roche', 'vircell', 'vircell_multiplex', 'genomica'],
            default='genomica')
    prot_group.add_argument("tubes",
            metavar='TIPO DE TUBO',
            action = 'store',
            choices=['falcon', 'eppendorf', 'labturbo','criotubo', 'criotubo_conico', 'serologia', 'f_redondo', 'f_redondo2'],
            default='eppendorf')

    args=parser.parse_args()
    return args


def print_output():

    numero_muestras_text = str(numero_muestras)

    now = datetime.datetime.now()

    print(now.strftime('%d-%m-%Y %H-%M\n\n'))
    print('\tSE HAN SELECCIONADO '+ numero_muestras_text +' MUESTRAS\n')

    if brand_name in splitmethods and numero_muestras > 47:
        raise ValueError("### PARA ESTE METODO EL NUMERO MAXIMO DE MUESTRAS ES 47 ###\n\n")
    elif 94 < numero_muestras:
        raise ValueError("#### EL NUMERO MAXIMO DE MUESTRAS ES 94 ###\n\n")

    print('\tEL KIT '+brand_name+'\n')
    print('\tY EL TUBO '+tipo_de_tubo+'\n\n\n')


def print_json():


    with open(filepath, 'w') as f:
        f.write('{\n\t\"muestras\": '+numero_muestras_text+',\n\t\"kit\": \"'+brand_name+'\",\n\t\"tubo\": \"'+tipo_de_tubo+'\"\n}')


def send():

    subprocess.call(["scp", "-i", "/home/laboratorio/ot2_ssh_key_sinclave", filepath, "root@"+ip+":/root/ot2-covid19/library/protocols/"])




if __name__ == '__main__':

# variables
    args = parse_args()

    robot = args.robots
    ip = robodict[robot]

    numero_muestras = args.samples
    numero_muestras_text = str(numero_muestras)

    brand_name = args.modes

    tipo_de_tubo = args.tubes



    filepath = "{}protocols/run_config.json".format(LIBRARY_PATH)

#ejecucion
    print_output()

    print_json()

    send()
