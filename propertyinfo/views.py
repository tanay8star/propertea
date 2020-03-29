from . import controller
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render


# Create your views here.
def index(request):
    c = controller.PropertyInfoController(request)

    context = {
        'name': c.name,
        'postal': c.postal,
        'mrt_lrt_plot': c.MRT_LRT_Data.plot(),
        'mrt_lrt_table_plot': c.MRT_LRT_Data.table(),
        'bus_plot': c.Bus_Data.plot(),
        'bus_table_plot': c.Bus_Data.table(),
        'links': c.PropertyImages(),
        'url': 'https://www.google.no/search?client=opera&hs=cTQ&source=lnms&tbm=isch&sa=X&ved=0ahUKEwig3LOx4PzKAhWGFywKHZyZAAgQ_AUIBygB&biw=1920&bih=982&q=' + c.name + " singapore property",
        'LAT': c.LAT,
        'LONG': c.LONG,
        'nearest_train_lat': c.MRT_LRT_Data.lat,
        'nearest_train_long': c.MRT_LRT_Data.long,
        'nearest_bus_lat': c.Bus_Data.lat,
        'nearest_bus_long': c.Bus_Data.long
    }

    return render(request, "propertyinfo/index.html", context)
