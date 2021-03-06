import requests
from .models import MRTLRTData, BusData, PropertyImages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from users.models import FavouriteProperty


class PropertyInfoController:
    """
    This controller class executes the logic for the 'PropertyInfo' sub-application.

    :ivar name: Name of property considered.
    :ivar keyword: Search keyword used to find the building.
    :ivar URL: URL for API.
    :ivar info: Information Retrieved from API.
    :ivar address: Address of Property.
    :ivar X: X-Coordinate of Property.
    :ivar Y: Y-Coordinate of Property.
    :ivar LAT: Latitude of Property.
    :ivar LONG: Longitude of Property.
    :ivar MRT_LRT_Data: Data of the nearest MRT/LRT.
    :ivar Bus_Data: Data of the nearest Bus Stop.
    :ivar images: Data from Google Images.
    :ivar request: The HTTP request at that instance.
    """
    def __init__(self, request):
        self.name = request.GET['name']
        self.keyword = request.GET['keyword']
        # may break when user clicks on property from favourites list
        self.URL = "https://developers.onemap.sg/commonapi/search?searchVal={}&returnGeom=Y&getAddrDetails=Y&pageNum=1".format(
            self.name)
        self.info = [i for i in requests.get(self.URL).json().get('results') if not (i['POSTAL'] == 'NIL')]
        self.address = self.info[0]['ADDRESS']
        self.X = float(self.info[0]['X'])
        self.Y = float(self.info[0]['Y'])
        self.LAT = float(self.info[0]['LATITUDE'])
        self.LONG = float(self.info[0]['LONGITUDE'])
        self.MRT_LRT_Data = MRTLRTData(self.X, self.Y)
        self.Bus_Data = BusData(self.X, self.Y)
        self.images = PropertyImages(self.name)
        self.request = request

    def getResponse(self):
        """
        Returns the 'index' page for the propertyinfo sub-application.

        :return: Render of 'index' page.
        """
        context = {
            'name': self.name,
            'address': self.address,
            'mrt_lrt_plot': self.MRT_LRT_Data.plot(),
            'mrt_lrt_table_plot': self.MRT_LRT_Data.table(),
            'bus_plot': self.Bus_Data.plot(),
            'bus_table_plot': self.Bus_Data.table(),
            'links': self.images.getLinks(),
            'url': self.images.getURL(),
            'LAT': self.LAT,
            'LONG': self.LONG,
            'nearest_train_lat': self.MRT_LRT_Data.lat,
            'nearest_train_long': self.MRT_LRT_Data.long,
            'nearest_bus_lat': self.Bus_Data.lat,
            'nearest_bus_long': self.Bus_Data.long,
            'keyword': self.keyword,
            'favourite': self.favourite(),
        }
        return render(self.request, "propertyinfo/index.html", context)

    def favouriteResponse(self):       
        """
        This function implements logic for toggling the favourites button.

        :return: Redirect back to the search page.
        """
        if self.request.POST:
            user = self.request.user
            if user is not None:
                propertyname = self.request.POST['propertyname']
                favourite = []
                if self.request.user.is_authenticated:
                    favourite = [i[0] for i in list(self.request.user.favouriteproperty_set.values_list('name'))]
                if propertyname in favourite:
                    FavouriteProperty.objects.get(name=propertyname, user=user).delete()
                else:
                    new_favourite = FavouriteProperty.objects.create(name=propertyname, user=user)
                    new_favourite.save()
                next_url = self.request.POST.get('next', '/')
                if next_url != "/users/login":
                    return HttpResponseRedirect(next_url)
            else:
                HttpResponseRedirect(self.request)
        else:
            return HttpResponseRedirect(self.request)

    def favourite(self):
        """
        This function implements logic for toggling the view favourites button.

        :return: The list of Favourite Properties in the database for a particular user.
        """
        favourite = []
        if self.request.user.is_authenticated:
            favourite = [i[0] for i in list(self.request.user.favouriteproperty_set.values_list('name'))]
        return favourite
