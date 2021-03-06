from django.db import models
import requests
from abc import ABCMeta, abstractmethod
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots
from bs4 import BeautifulSoup

# Create your models here.
class TransportData(metaclass = ABCMeta):
    """
    This class aims to facilitate storing and retrieving transport data.

    :ivar X: X-Coordinate of Property.
    :ivar Y: Y-Coordinate of Property.
    :ivar directory: Location of Stations CSV file.
    :ivar volumeDir: Location of the Volume CSV file.
    :ivar routeDir: Location of the Route CSV file.
    :ivar type: "Bus" or "MRT".
    :ivar term: "Stop" or "Station".
    :ivar name: Transport Facility Name.
    :ivar number: Bus Stop Number or MRT Number.
    :ivar lat: Latitude of Facility.
    :ivar long: Longitude of Facility.
    """
    def __init__(self, X, Y, directory, volumeDir, routeDir, type, term):
        self.X = X
        self.Y = Y
        self.directory = directory
        self.volumeDir = volumeDir
        self.routeDir = routeDir
        self.type = type
        self.term = term
        self.csv = pd.DataFrame(pd.read_csv(self.directory))
        X_diff = np.subtract(np.array(self.csv['X']), self.X)
        Y_diff = np.subtract(np.array(self.csv['Y']), self.Y)
        self.csv['DISTANCE'] = np.sqrt(np.square(X_diff) + np.square(Y_diff))
        self.name = self.csv.sort_values(by='DISTANCE').iloc[0]['NAME']
        self.number = self.csv.sort_values(by='DISTANCE').iloc[0]['NUMBER']
        self.lat = self.csv.sort_values(by='DISTANCE').iloc[0]['LATITUDE']
        self.long = self.csv.sort_values(by='DISTANCE').iloc[0]['LONGITUDE']

    def plot(self):
        """
        This function seeks to plot the transport ameneties graph.

        :return: A plot of the traffic volume of the selected transport facility.
        """
        volume = pd.DataFrame(pd.read_csv(self.volumeDir))
        plotData = volume[volume['PT_CODE'] == self.number].sort_values('TIME_PER_HOUR')
        time = [24 if x == 0 else x for x in plotData['TIME_PER_HOUR'].tolist()]
        fig = go.Figure()
        fig.layout = go.Layout(
            title=go.layout.Title(
                text="{} ({})".format(self.name.upper(), self.number),
            ),

            xaxis=go.layout.XAxis(
                tickmode='array',
                tickvals=time,
                ticktext=[str(i) for i in time],
                title=go.layout.xaxis.Title(text='Time', )
            ),

            yaxis=go.layout.YAxis(
                title=go.layout.yaxis.Title(
                    text='Passenger Volume',
                )
            )
        )
        fig.add_trace(go.Bar(
            x=time,
            y=plotData['TOTAL_TAP_IN_VOLUME'].tolist(),
            name='Total Tap In Volume',
            marker_color='rgb(255, 211, 120)'))
        fig.add_trace(go.Bar(
            x=time,
            y=plotData['TOTAL_TAP_OUT_VOLUME'].tolist(),
            name='Total Tap Out Volume',
            marker_color='rgb(206, 123, 91)'))
        fig.update_layout(barmode='group', xaxis_tickangle=-45, plot_bgcolor='rgb(252, 250, 241)', font={"family": "Karla", "size": 16})
        return plot(fig, output_type="div", include_plotlyjs=False)

    @abstractmethod
    def table(self):
        pass


class MRTLRTData(TransportData):
    """
    This class aims to facilitate storing and retrieving MRT and LRT station data, while being an extention of Transport Data.
    """
    def __init__(self, X, Y):
        directory = "propertea/static/MRT_LRT_Station_Data.csv"
        volumeDir = "propertea/static/MRT_LRT_Transport_Volume.csv"
        routeDir = "propertea/static/MRT_LRT_Route_Data.csv"
        type = "MRT/LRT"
        term = "Station"
        super().__init__(X, Y, directory, volumeDir, routeDir, type, term)

    def table(self):
        """
        This function aims to create the tables for the first and last train services from the selected MRT and LRT station.

        :return: A plot of a table containing the first and last train timings from the selected MRT and LRT station.
        """
        routeData = pd.read_csv(self.routeDir)
        tableData = routeData[routeData['NUMBER'] == self.number]
        fig = make_subplots(
            rows=len(list(set(tableData['LINE'].values))), cols=1,
            shared_xaxes=True,
            vertical_spacing=0,
            specs=list([{"type": "table"}] for i in range(len(list(set(tableData['LINE'].values)))))
        )

        num = 1

        for trainline in list(set(tableData['LINE'].values)):
            subset = tableData[tableData['LINE'] == trainline]
            header_values = ["<b>{}</b>".format(trainline)]
            table_values = [['', '<b>Weekday</b>', '<b>Saturday</b>', '<b>Sunday</b>']]
            for index in range(len(subset)):
                header_values.append('<b>{}</b>'.format(subset['TOWARDS'].iloc[index]))
                header_values.append('<b>{}</b>'.format(subset['TOWARDS'].iloc[index]))
                table_values.append(
                    ['First Train', str(subset['WD_FIRSTTRAIN'].iloc[index]), str(subset['SAT_FIRSTTRAIN'].iloc[index]),
                     str(subset['SUN_FIRSTTRAIN'].iloc[index])])
                table_values.append(
                    ['Last Train', str(subset['WD_LASTTRAIN'].iloc[index]), str(subset['SAT_LASTTRAIN'].iloc[index]),
                     str(subset['SUN_LASTTRAIN'].iloc[index])])

            for row_index in range(1, len(table_values)):
                for col_index in range(len(table_values[row_index])):
                    if len(table_values[row_index][col_index]) == 1 and table_values[row_index][col_index]!='-':
                        table_values[row_index][col_index] = '000' + table_values[row_index][col_index]
                    elif len(table_values[row_index][col_index]) == 2:
                        table_values[row_index][col_index] = '00' + table_values[row_index][col_index]
                    elif len(table_values[row_index][col_index]) == 3:
                        table_values[row_index][col_index] = '0' + table_values[row_index][col_index]

            fig.add_trace(go.Table(
                header=dict(values=header_values,
                            height=30,
                            align=['right', 'center'],
                            fill = dict(color = 'rgb(201, 190, 120)'),
                            font=dict(family='Karla, monospace', size=18)
                            ),
                cells=dict(values=table_values,
                           align=['right', 'center'],
                           height=30,
                           fill = dict(color = 'rgb(252, 250, 241)'),
                           font=dict(family='Karla, monospace', size=18)
                           )
            ),
                row=num, col=1
            )
            num += 1

        fig.update_layout(
            height=400 * len(list(set(tableData['LINE'].values))),
            showlegend=True,
            title_text="MRT/LRT SERVICES AT THIS STOP",
        )
        return plot(fig, output_type="div", include_plotlyjs=False)


class BusData(TransportData):
    """
    This class aims to facilitate storing and retrieving Bus Stop data, while being an extension of Transport Data.
    """
    def __init__(self, X, Y):
        directory = "propertea/static/Bus_Stop_Data.csv"
        volumeDir = "propertea/static/Bus_Transport_Volume.csv"
        routeDir = "propertea/static/Bus_Route_Data.csv"
        type = "Bus"
        term = "Stop"
        super().__init__(X, Y, directory, volumeDir, routeDir, type, term)

    def table(self):
        """
        This function aims to create the tables for the first and last bus services arriving at the selected bus stop.

        :return: A plot of the table of the first and last bus services arriving at the selected bus stop.
        """
        routeData = pd.DataFrame(pd.read_csv(self.routeDir))
        tableData = routeData[routeData['BUSSTOPCODE'] == str(self.number)]

        fig = make_subplots(
            rows=len(tableData), cols=1,
            shared_xaxes=True,
            vertical_spacing=0,
            specs=list([{"type": "table"}] for i in range(len(tableData)))
        )

        for index in range(len(tableData)):
            FirstBus = [tableData['WD_FIRSTBUS'].iloc[index], tableData['SAT_FIRSTBUS'].iloc[index],
                        tableData['SUN_FIRSTBUS'].iloc[index]]
            for j in range(len(FirstBus)):
                if len(FirstBus[j]) == 2:
                    FirstBus[j] = '00' + FirstBus[j]
                elif len(FirstBus[j]) == 3:
                    FirstBus[j] = '0' + FirstBus[j]

            LastBus = [tableData['WD_LASTBUS'].iloc[index], tableData['SAT_LASTBUS'].iloc[index],
                       tableData['SUN_LASTBUS'].iloc[index]]
            for j in range(len(LastBus)):
                if len(LastBus[j]) == 1 and LastBus[j]!='-':
                    LastBus[j] = '000' + LastBus[j]
                elif len(LastBus[j]) == 2:  
                    LastBus[j] = '00' + LastBus[j]
                elif len(LastBus[j]) == 3:
                    LastBus[j] = '0' + LastBus[j]

            fig.add_trace(go.Table(
                header=dict(values=['<b>{}</b>'.format(tableData['ROUTENAME'].iloc[index]), '<b>First Bus</b>',
                                    '<b>Last Bus</b>'],
                            align=['right', 'center'],
                            fill=dict(color = 'rgb(201,190,120)'),
                            height=30,
                            font=dict(family='Karla, monospace', size=18)
                            ),
                cells=dict(values=[['Weekdays', 'Saturdays', 'Sundays & Public Holidays'],
                                   FirstBus,
                                   LastBus
                                   ],
                           align=['right', 'center'],
                           fill=dict(color = 'rgb(252,250,241)'),
                           height=30,
                           font=dict(family='Karla, monospace', size=18)
                           )
            ),
                row=index + 1, col=1
            )

        fig.update_layout(
            height=max([len(tableData) * 220, 400]),
            showlegend=True,
            title_text="BUS SERVICES AT THIS STOP",
        )
        return plot(fig, output_type="div", include_plotlyjs=False)


class PropertyImages:
    """
    This class aims to facilitate storing and retrieving property images.

    :ivar name: Google Image Search Keyword
    """
    def __init__(self, name):
        self.name = name

    def getLinks(self):
        """
        This function generates a link to view more Google Images on the selected property.

        :return: The link that can be used to link to a Google Images search.
        """
        url = 'https://www.google.no/search?client=opera&hs=cTQ&source=lnms&tbm=isch&sa=X&ved=0ahUKEwig3LOx4PzKAhWGFywKHZyZAAgQ_AUIBygB&biw=1920&bih=982'
        page = requests.get(url, params={'q': self.name + " singapore property"}).text
        soup = BeautifulSoup(page, 'html.parser')

        links = []

        for raw_img in soup.find_all('img'):
            link = raw_img.get('src')
            if link and 'http://' in link:
                links.append(link)
            if len(links) >= 3:
                break

        return links

    def getURL(self):
        """
        Returns the URL.

        :return: URL.
        """
        return 'https://www.google.no/search?client=opera&hs=cTQ&source=lnms&tbm=isch&sa=X&ved=0ahUKEwig3LOx4PzKAhWGFywKHZyZAAgQ_AUIBygB&biw=1920&bih=982&q=' + self.name + " singapore property"
