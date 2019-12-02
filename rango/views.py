from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import sessions

from rango.bing_search import run_query
from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from datetime import datetime


def index(request):
    category_list = Category.objects.order_by('-likes')[:3]
    page_list = Page.objects.order_by('-views')[:5]

    context_dict = {}
    context_dict['boldmessage'] = 'Crunchy, creamy, cookie, candy, cupcake!'
    context_dict['categories'] = category_list
    context_dict['pages'] = page_list

    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']

    response = render(request, 'rango/index.html', context_dict)
    return response


def about(request):
    if request.session.test_cookie_worked():
        print("TEST COOKIED WORKED!")
        request.session.delete_test_cookie()

    context_dict = {}
    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']

    return render(request, 'rango/about.html', context_dict)


def show_category(request, category_name_slug):
    context_dict = {}

    try:
        category = Category.objects.get(slug=category_name_slug)
        pages = Page.objects.filter(category=category).order_by('-views')

        context_dict['pages'] = pages
        context_dict['category'] = category
    except Category.DoesNotExist:
        context_dict['pages'] = None
        context_dict['category'] = None

    # start new search functionality code
    if request.method == "POST":
        query = request.POST['query'].strip()

        if query:
            context_dict['result_list'] = run_query(query)
            context_dict['query'] = query

    return render(request, 'rango/category.html', context_dict)


def add_category(request):
    form = CategoryForm()

    # A HTTP POST?
    if request.method == "POST":
        form = CategoryForm(request.POST)

        if form.is_valid():
            # Save the new category in database
            form.save(commit=True)
            return index(request)
        else:
            print(form.errors)

    return render(request, 'rango/add_category.html', {'form': form})


def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category = None

    form = PageForm()
    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()

                return redirect(reverse('rango:show_category',
                                        kwargs={'category_name_slug':
                                                category_name_slug}))
        else:
            print(form.errors)

    context_dict = {'form': form, 'category': category}
    return render(request, 'rango/add_page.html', context_dict)


def register(request):
    # true when registration succeeds.
    registered = False

    if request.method == "POST":
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # if the two form are valid
        if user_form.is_valid() and profile_form.is_valid():
            # save the user's form data to the database
            user = user_form.save()

            # Now hash password with the set_password method
            # once hashed, we can update the user object
            user.set_password(user.password)
            user.save()

            # we set commit=False. This delays saving the model
            # until we're ready to avoid integrity problems
            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()

            # Update our variable to indicate that the template
            # registration was successful
            registered = True
        else:
            # Print problems to the terminal
            print(user_form.errors, profile_form.errors)
    else:
        # Not a HTTP POST
        # These form will be blank, ready for user input
        user_form = UserForm()
        profile_form = UserProfileForm()

    content_dict = {'user_form': user_form,
                    'profile_form': profile_form,
                    'registered': registered}
    return render(request, 'rango/register.html', content_dict)


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return redirect(reverse('rango:index'))
            else:
                return HttpResponse("Your Rango account is disabled.")
        else:
            print("Invalid login details: {0} {1}".format(username, password))
            return HttpResponse("Invalid login details supplied.")
    else:
        return render(request, 'rango/login.html')


@login_required
def restricted(request):
    return HttpResponse("Since you're logged in, you can see this text!")


@login_required
def user_logout(request):
    logout(request)
    return redirect(reverse('rango:index'))


# a helper method
def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)

    if not val:
        val = default_val

    return val


# update the function definition
def visitor_cookie_handler(request):
    visits = int(get_server_side_cookie(request, 'visits', '1'))

    last_visit_cookie = get_server_side_cookie(request, 'last_visit', str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')

    if (datetime.now() - last_visit_time).days > 0:
        visits = visits + 1
        request.session['last_visit'] = str(datetime.now())
    else:
        request.session['last_visit'] = last_visit_cookie

    request.session['visits'] = visits


def search(request):
    result_list = []
    if request.method == 'POST':
        query = request.POST['query'].strip()
        if query:
            result_list = run_query(query)

    return render(request, 'rango/search.html', {'result_list': result_list})


def goto_url(request):
    if request.method == "GET":
        page_id = request.GET.get('page_id')
        try:
            selected_page = Page.objects.get(id=page_id)
        except Page.DoesNotExist:
            return redirect(reverse('rango:index'))

        selected_page.views = selected_page.views + 1
        selected_page.save()

        return redirect(selected_page.url)

    return redirect(reverse('rango:index'))
