# Instalación y errores
> por Luis Lorenzo Mosquera, Victor Soroña Pombo & Ismael Castiñeira Paz 
<pre>
      @@@@@    @@@@@                                                                               
    @@@@          @@@@                                                         
   @@@      @@      @@@    @@@@@@   @@@@@
  @@@      @@@@      @@@   @@@@@@  &amp;@&apos; &apos;@@
  @@     @@@@@@@@    &amp;@@     @@         @@
  @@    .@@@    @    #@@     @@        @@
  @@@    @      @    @@@     @@       @@
   @@@    @@..@@    @@@      @@      @@
    @@@@          @@@@       @@     @@@@@&amp;
      @@@@@@@@@@@@@@         ##    &amp;@@@@@#
         (@@@@@@.
</pre>

# Instalación

<a id="ssh"></a>

## Preparar la conexión por ssh

1. `sudo apt-get install curl`
2. `ssh-keygen -f ot2_ssh_key`
3. `curl \
-H 'Content-Type: application/json' \
-d "{\"key\":\"$(cat ot2_ssh_key.pub)\"}" \`
**IP_ROBOT**`:31950/server/ssh_keys`
4. `ssh -i ot2_ssh_key root@`**IP_ROBOT**


<a id="transf_biblio"></a>

## Transferir biblioteca de codigo a OT2

1. `ssh -i ot2_ssh_key root@`**IP_ROBOT**
2. `mkdir -p /root/ot2-covid19/library/protocols`
3. `scp -i ot2_ssh_key home/laboratorio/Repositorios/ot2-covid19/library/protocols/common_functions.py root@`**IP_ROBOT**`:/root/ot2-covid19/library/protocols`


# Otros

<a id="apagar"></a>

## Apagar robot de forma segura
1. `ssh -i ot2_ssh_key root@`**IP_ROBOT**
2. `halt`


<a id="ruta_historial"></a>

## Ruta historial de robots conectados al programa
~~~
~/.config/Opentrons/discovery.json
~~~


# Troubleshooting

## Problemas instalar clave en OT2

* Si salta error `The endpoint http://127.0.0.1:34000/server/ssh_keys can only be used from local connections`:
1. Asignar al OT2 una ip del mismo rango que tiene el PC al activar [*"solo enlace local"*](https://es.wikipedia.org/wiki/Direcci%C3%B3n_de_Enlace-Local) en la configuración de red.
2. Activar "solo enlace local" en el PC.
3. Enviamos clave al OT2 como en el [**apartado 3.** de Conectar por ssh](#ssh)
4. Volver a poner la IP correspondiente al OT2 y al PC
5. Nos conectamos por ssh al OT2 como en el [**apartado 4.** de Conectar por ssh](#ssh)

## Links de referencia

* Página web [diseñador de protocolos](https://opentrons.com/protocols/designer/)
* Página web [manual](https://covidrobots.org/instalacion/1/introduccion/index.html)
* Página web [proyecto github](https://github.com/COVIDWarriors)