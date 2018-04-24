from django.shortcuts import render, redirect
from .models import Restaurant, Item, FavoriteRestaurant
from .forms import RestaurantForm, ItemForm, SignupForm, SigninForm
from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse
from django.db.models import Q

def restaurant_favorite(request, restaurant_id):
    restaurant_obj = Restaurant.objects.get(id=restaurant_id)
    if request.user.is_anonymous:
        return redirect('signin')
    
    favorite, created = FavoriteRestaurant.objects.get_or_create(user=request.user, restaurant=restaurant_obj)
    if created:
        action="favorite"
    else:
        favorite.delete()
        action="unfavorite"

    response = {
        "action": action,
    }
    return JsonResponse(response, safe=False)

def no_access(request):
    return render(request, 'no_access.html')

def signup(request):
    form = SignupForm()
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            user.set_password(user.password)
            user.save()

            login(request, user)
            return redirect("restaurant-list")
    context = {
        "form":form,
    }
    return render(request, 'signup.html', context)

def signin(request):
    form = SigninForm()
    if request.method == 'POST':
        form = SigninForm(request.POST)
        if form.is_valid():

            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            auth_user = authenticate(username=username, password=password)
            if auth_user is not None:
                login(request, auth_user)
                return redirect('restaurant-list')
    context = {
        "form":form
    }
    return render(request, 'signin.html', context)

def signout(request):
    logout(request)
    return redirect("signin")

def restaurant_list(request):
    restaurants = Restaurant.objects.all()
    query = request.GET.get('q')
    if query:
        restaurants = restaurants.filter(
            Q(name__icontains=query)|
            Q(description__icontains=query)|
            Q(owner__username__icontains=query)
        ).distinct()

    favorite_list = []
    if request.user.is_authenticated:
        favorite_list = request.user.favoriterestaurant_set.all().values_list('restaurant', flat=True)

    context = {
       "restaurants": restaurants,
       "favorite_list": favorite_list
    }
    return render(request, 'list.html', context)

def favorite_restaurants(request):
    if request.user.is_anonymous:
        return redirect('signin')
    favorite_list = request.user.favoriterestaurant_set.all().values_list('restaurant', flat=True)
    restaurants = Restaurant.objects.filter(id__in=favorite_list)
    context = {
        "restaurants": restaurants,
    }
    return render(request, 'favorite_restaurants.html', context)

def restaurant_detail(request, restaurant_id):
    restaurant = Restaurant.objects.get(id=restaurant_id)
    items = Item.objects.filter(restaurant=restaurant)
    context = {
        "restaurant": restaurant,
        "items": items,
    }
    return render(request, 'detail.html', context)

def restaurant_create(request):
    if request.user.is_anonymous:
        return redirect('signin')
    form = RestaurantForm()
    if request.method == "POST":
        form = RestaurantForm(request.POST, request.FILES)
        if form.is_valid():
            restaurant = form.save(commit=False)
            restaurant.owner = request.user
            restaurant.save()
            return redirect('restaurant-list')
    context = {
        "form":form,
    }
    return render(request, 'create.html', context)

def item_create(request, restaurant_id):
    form = ItemForm()
    restaurant = Restaurant.objects.get(id=restaurant_id)
    if not (request.user.is_staff or request.user == restaurant.owner):
        return redirect('no-access')
    if request.method == "POST":
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.restaurant = restaurant
            item.save()
            return redirect('restaurant-detail', restaurant_id)
    context = {
        "form":form,
        "restaurant": restaurant,
    }
    return render(request, 'item_create.html', context)

def restaurant_update(request, restaurant_id):
    restaurant_obj = Restaurant.objects.get(id=restaurant_id)
    if not (request.user.is_staff or request.user == restaurant_obj.owner):
        return redirect('no-access')
    form = RestaurantForm(instance=restaurant_obj)
    if request.method == "POST":
        form = RestaurantForm(request.POST, request.FILES, instance=restaurant_obj)
        if form.is_valid():
            form.save()
            return redirect('restaurant-list')
    context = {
        "restaurant_obj": restaurant_obj,
        "form":form,
    }
    return render(request, 'update.html', context)

def restaurant_delete(request, restaurant_id):
    restaurant_obj = Restaurant.objects.get(id=restaurant_id)
    if not (request.user.is_staff):
        return redirect('no-access')
    restaurant_obj.delete()
    return redirect('restaurant-list')
