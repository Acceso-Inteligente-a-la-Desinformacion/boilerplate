from src.lib.gui import *
from src.lib.scrapper import *
from src.lib.db import *

import re

class App:
    def __init__(self, title='Título del programa'):
    
        self.db = DB('example', [
            DbTable(
                name="Partidos",
                fields = [
                    DbField(
                        'Jornada',
                        'int',
                        min = 1,
                        max = 2
                    ),
                    DbField(
                        'Local',
                        'text'
                    ),
                    DbField(
                        'Resultado Local',
                        'int'
                    ),
                    DbField(
                        'Visitante',
                        'text'
                    ),
                    DbField(
                        'Resultado Visitante',
                        'int'
                    ),
                    DbField(
                        'Link',
                        'text'
                    ),
                    DbField(
                        'Datos',
                        'text'
                    )
                ]
            ),
            DbTable(
                name="example_birds_table",
                fields = [
                    DbField(
                        'Name',
                        'text'
                    ),
                    DbField(
                        'Size',
                        'int'
                    ),
                    DbField(
                        'Quantity',
                        'int'
                    )
                ]
            ),
            DbTable(
                name="Example Dogs Table",
                fields = [
                    DbField(
                        'Name',
                        'text'
                    ),
                    DbField(
                        'Size',
                        'int'
                    ),
                    DbField(
                        'Quantity',
                        'int'
                    )
                ]
            )
        ], 'dev') # Inicializa la conexión a la base de datos

        self.gui = GUI() # Inicializa la interfaz gráfica
        self.gui.setTitle(title) # Asigna un título a la interfaz gráfica
        
        # Por cada elemento del menú en el método getMenu lo añade a la MenuBar de la interfaz gráfica
        for menutab in self.getMenu():
            self.gui.addMenuTab(menutab)

        # Por cada elemento definido en getMainComponents se añade un componente dentro de la ventana principal
        for component in self.getMainComponents():
            self.gui.addRootComponent(component)

        self.gui.launch() # Lanza la interfaz gráfica

    def getMenu(self):
        return [
            MenuTab(
                title = 'Primera pestaña',
                items = [
                    MenuTabItem(
                        label = 'Primer elemento',
                        callback = self.showConsoleMessage
                    )
                ]
            ),
            MenuTab(
                title = 'Segunda pestaña',
                items = [
                    MenuTabItem(
                        label = 'Primer elemento',
                        callback = self.showConsoleMessage
                    )
                ]
            ),
            MenuTab(
                title = 'Tercerao pestaña',
                items = [
                    MenuTabItem(
                        label = 'Primer elemento',
                        callback = self.showConsoleMessage
                    )
                ]
            )
        ]
    
    def getMainComponents(self):
        return [
            Component(
                type='button',
                text='Almacenar resultados',
                callback=self.store
            ),
            Component(
                type='button',
                text='Listar Jornadas',
                callback=self.list
            ),
            Component(
                type='button',
                text='Buscar Jornada',
                callback=self.searchJornada
            ),
            Component(
                type='button',
                text='Estadísticas Jornada',
                callback=self.searchJornadaEstadisticas
            ),
            Component(
                type='button',
                text='Buscar Goles',
                callback=self.searchGoles
            )
        ]
    
    def showConsoleMessage(self):
        print('Esto es un mensaje en consola')

    
    def close(self):
        self.db.closeConnection() # Cierra la conexión con la base de datos
        self.gui.close() # Cierra la interfaz gráfica

    def store(self):

        partidos = [] # Elemento que va a almacenar cada vino

        scrappy = Scrapper('https://resultados.as.com/resultados/futbol/primera/2021_2022/calendario/') # Inicializa la clase de Scrapper
        scrappy.get() # Hace que el scrapper funcione en modo GET

        jornadasHtml = scrappy.select('.content > div:last-child > div > div:nth-child(3) > div')

        cantidadJornadas = 2

        for jornada in jornadasHtml: # Recorre cada elemento de VINO. Aquí son objetos de tipo BEAUTIFULSOUP

            if cantidadJornadas > 0:

                numJornada = int(jornada.select_one('.tit-modulo > a').text.replace('Jornada ', ''))

                partidosHtml = jornada.select('.tabla-datos > tbody > tr')

                for partido in partidosHtml:
                    resultadosText = partido.select_one('td:nth-child(2) > a').text
                    link = partido.select_one('td:nth-child(2) > a')['href']

                    resultados = []
                    for r in resultadosText.split(' - '):
                        resultados.append(int(r))


                    scrappy2 = Scrapper(link)
                    scrappy2.get()

                    datosHtml = scrappy2.select('.ev-mw-wr-col.no-gap.no-gap-fw')

                    listGoalPlayers = []
                    for playersList in datosHtml:
                        teamName = playersList.select_one('.team-name').text.strip()
                        goalPlayers = playersList.select('.in-pla:has(.ev-i-goal)')

                        for player in goalPlayers:
                            if not isinstance(player, str):
                                playerName = player.select_one('.in-pla-name').text.strip()

                                goalQuantityHtml = player.select_one('.in-pla-goals')

                                if(goalQuantityHtml != None):
                                    goalQuantity = player.select_one('.in-pla-goals').text
                                else:
                                    goalQuantity = '1'
                                
                                listGoalPlayers.append(f'{teamName}: {playerName} ({goalQuantity})')

                    partidos.append((
                        numJornada,
                        partido.select_one('td:first-child .nombre-equipo').text,
                        resultados[0],
                        partido.select_one('td:last-child .nombre-equipo').text,
                        resultados[1],
                        link,
                        "\n".join(listGoalPlayers)
                    ))
            cantidadJornadas -= 1

        # Reinicializa la tabla de la base de datos de VINOS
        self.db.rebuildSchema('prod')

        # Por cada tupla de vinos la añade a la tabla
        for partido in partidos:
            self.db.exec('INSERT INTO PARTIDOS VALUES (?,?,?,?,?,?,?)', partido)

        partidoQuantity = self.db.countTable('PARTIDOS') # Cuenta la cantidad de vinos
        self.gui.message("Base de Datos", "Cantidad de partidos: "+str(partidoQuantity)) # Muestra un mensaje con la cantidad de elementos añadidos


    def list(self):
        cursor = self.db.exec('SELECT * FROM PARTIDOS') # Recoge todos los vinos de la tabla

        content = []
        matches = []
        nJornada = 0
        for row in cursor:

            if nJornada != row[0]:
                content.append(matches)
                matches = []

                content.append([
                    "Jornada: "+ str(row[0]),
                    "----------------------------"
                ])
                nJornada += 1

            matches.append('      ' + row[1] + ' ' + str(row[2]) + '-' + str(row[4]) + ' ' + row[3])

        content.append(matches)
        self.gui.listScrollWindow(title='Partidos', content=content)
    
    def searchJornada(self):
        def search(param, window):
            cursor = self.db.exec("SELECT * FROM PARTIDOS WHERE JORNADA == ?", (param,))

            content = [['JORNADA '+str(param)]]
            matches = []
            for row in cursor:
                matches.append(row[1] + ' ' + str(row[2]) + '-' + str(row[4]) + ' ' + row[3])

            content.append(matches)

            self.gui.listScrollWindow(title='Buscar jornada', content=content)


        cursor = self.db.exec('SELECT DISTINCT JORNADA FROM PARTIDOS') # Recoge cada denominación sin repetirla

        jornadas = [d[0] for d in cursor]

        newWindow = self.gui.formWindow(title="Buscar partido", components = [{
            'type': 'label',
            'text': 'Seleccione una jornada: ',
            'side': 'left'
        }, {
            'type': 'spinbox',
            'values': jornadas,
            'onChangeEvent': False,
            'func': search,
            'side': 'left',
            'width': 30
        }])

        newWindow.create()

    def searchJornadaEstadisticas(self):
        def calcular_estadisticas(partidos):
            total_goles = 0
            empates = 0
            victorias_locales = 0
            victorias_visitantes = 0
            ls=[]
            
            for partido in partidos:
                total_goles += partido[2] + partido[4]  # Sumar goles del equipo local y visitante
                if partido[2] == partido[4]:  # Si los goles son iguales, es un empate
                    empates += 1
                elif partido[2] > partido[4]:  # Si el equipo local tiene más goles, es una victoria local
                    victorias_locales += 1
                else:  # Si el equipo visitante tiene más goles, es una victoria visitante
                    victorias_visitantes += 1
            ls.append(total_goles)
            ls.append(empates)
            ls.append(victorias_locales)
            ls.append(victorias_visitantes)
            return ls
        
        newWindow = None

        def search(param, window):
            cursor = self.db.exec("SELECT * FROM PARTIDOS WHERE JORNADA == ?", (param,))
            content = [['JORNADA '+str(param)]]
            estadisticas= calcular_estadisticas(cursor.fetchall())
            mensaje = [f"{estadisticas[0]} goles totales, {estadisticas[1]} empates, {estadisticas[2]} victorias locales, {estadisticas[3]} victorias de visitantes"]
            content.append(mensaje)
            self.gui.listScrollWindow(title='Buscar estadisticas de la jornada', content=content)


        cursor = self.db.exec('SELECT DISTINCT JORNADA FROM PARTIDOS') # Recoge cada denominación sin repetirla

        jornadas = [d[0] for d in cursor]

        newWindow = self.gui.formWindow(title="Buscar partido", components = [{
            'type': 'label',
            'text': 'Seleccione una jornada: ',
            'side': 'left'
        }, {
            'type': 'spinbox',
            'values': jornadas,
            'func': search,
            'side': 'left',
            'width': 30
        }])

        newWindow.create()

    def searchGoles(self):
        def searchJornada(param, window):
            cursor = self.db.exec("SELECT LOCAL FROM PARTIDOS WHERE JORNADA == ?", (param,))

            equipos_locales = [d[0] for d in cursor]

            window.entryComponents[3].config(values=equipos_locales)

            searchLocal(equipos_locales[0], window)

        def searchLocal(param, window):
            cursor = self.db.exec("SELECT VISITANTE FROM PARTIDOS WHERE JORNADA == ? AND LOCAL == ?", (window.entryComponents[1].get(), param))

            equipos_visitantes = [d[0] for d in cursor]

            window.entryComponents[5].config(values=equipos_visitantes)

        def searchVisitante(param, window):
            cursor = self.db.exec("SELECT DATOS FROM PARTIDOS WHERE JORNADA == ? AND LOCAL == ? AND VISITANTE == ?", (window.entryComponents[1].get(), window.entryComponents[3].get(), param))

            resultados = [d[0] for d in cursor]

            contentView = self.gui.formWindow(title="Resultados del partido", components=[{
                'type': 'label',
                'text': resultados[0]
            }])

            contentView.create()


        cursor = self.db.exec('SELECT DISTINCT JORNADA FROM PARTIDOS') # Recoge cada denominación sin repetirla

        jornadas = [d[0] for d in cursor]

        newWindow = self.gui.formWindow(title="Buscar partido", components = [{
            'type': 'label',
            'text': 'Seleccione una jornada: ',
            'side': 'left'
            }, {
            'type': 'spinbox',
            'values': jornadas,
            'func': searchJornada,
            'side': 'left',
            'width': 30
            },
            {
            'type': 'label',
            'text': 'Seleccione un equipo local: ',
            'side': 'left'
            }, {
            'type': 'spinbox',
            'values': [],
            'func': searchLocal,
            'side': 'left',
            'width': 30
            },
            {
            'type': 'label',
            'text': 'Seleccione un equipo visitante: ',
            'side': 'left'
            }, {
            'type': 'spinbox',
            'values': [],
            'func': searchVisitante,
            'side': 'left',
            'width': 30
        }])

        newWindow.create()

        searchJornada(jornadas[0], newWindow)

# Lanza App
App()