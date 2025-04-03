from . import views


from django.urls import path
urlpatterns = [

    path('billing',views.billing,name='billing'),

]
