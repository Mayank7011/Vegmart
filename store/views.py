from django.shortcuts import render,reverse,redirect
from django.http import HttpResponseRedirect,HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from store.decorators import check_access
from django.db.models import Q
from .models import Shop,Order,OrderItem,Product,Customer,Rating,Customer_Address,DelivaryBoy,OrderShipping
from .forms import CustomerAddressForm
veg_type_list=['','all','Daily Use','Green Leaves','Root','spices and flavour']
veg_description_list=[
    '',
    'All types of vegetables',
    'Vegetables which are most commonly used everyday',
    'All types of green leave vegetables',
    'All types of Root vegetables',
    'All types of Spices and Flavour Vegetables',
]
@check_access(allowed_users=['anonymous','Customer'])
def home(request):
    shops=Shop.objects.all()
    shop_order=request.GET.get('order')
    if shop_order == None:
        shop_order=1
    shop_order=int(shop_order)
    try:
        shops=order_shops(shops,shop_order)
    except:
        return render(request,'store/error.html');
    page_number=request.GET.get('page')
    if page_number == None:
        page_number=1
    paginator=Paginator(shops,6)
    page_obj=paginator.get_page(page_number)
    sponsered_shops=Shop.objects.filter(sponsored=True)
    context={
        'shops':page_obj,
        'order':shop_order,
        'page_number':page_number,
        'sponsered_shops':sponsered_shops,
        'home_flag':True,
    }
    return render(request,'store/home.html',context)

def about(request):
    return render(request,'store/about.html')

def contact_us(request):
    return render(request,'store/contact_us.html')

def order_by_shop_rating(shop):
    return shop.shop_rating

def order_shops(shops,shop_order):
    if shop_order == 1:
        pass
    elif shop_order == 2:
        shop=shops.first()
        shops=sorted(shops,key=order_by_shop_rating, reverse=True)
    elif shop_order == 3:
        shops=sorted(shops,key= lambda shop: shop.discount,reverse=True)
    else:
        raise Exception('Not valid')
    return shops
    
def get_products_list(shop,veg_type):
    if veg_type <1 and veg_type > 5:
        raise Exception('Not Valid!')
    if veg_type ==1:
        return shop.product.all()
    else:
        veg_type_name=veg_type_list[veg_type]
        products=shop.product.filter(category__name=veg_type_name)
        return products
@check_access(allowed_users=['anonymous','Customer',])
def ShopDetail(request,slug_store):
    veg_type=request.GET.get('type')
    if veg_type == None:
        veg_type='1'
    veg_type=int(veg_type)
    try:
        shop=Shop.objects.get(slug_store=slug_store)
        veg_title='Fresh Vegetables'
        veg_description=veg_description_list[veg_type]
        products=get_products_list(shop,veg_type)
        rating=0,
        rated=False
        if request.user.is_authenticated:
            #rate_qs=Rating.objects.filter(shop=shop,customer=request.user.customer)
            rate_qs = None
            if False and rate_qs.exists() and rate_qs.count() == 1:
                rate_obj=rate_qs.first()
                rating=rate_obj.rate
                rated=True
        context={'shop':shop,
            'veg_type':veg_type,
            'products':products,
            'rated':rated,
            'rating':rating,
            'veg_title':veg_title,
            'veg_description':veg_description,
        }
        return render(request,'store/shop_detail.html',context)
    except:
        return render(request,'store/error.html')

def get_product(request,slug_store,slug_product):
    try:
        shop=Shop.objects.get(slug_store=slug_store)
        product=shop.product.get(slug_product=slug_product)
        return product
    except:
        return render(request,'store/error.html')

def create_or_update_order_item(order,product):
    try:
        order_item=order.order_item.get(product=product)
        order_item.quantity=order_item.quantity+1
        order_item.save()
    except:
        order.order_item.create(product=product)
    order.save()

@check_access(allowed_users=['Customer',])
def add_to_cart(request,slug_store,slug_product):
    try:
        qs=Order.objects.filter(customer=request.user.customer,is_completed=False)
    except:
        return render(request,'store/error.html',{'error_message':'You are not authorized to order products!',})
    product=get_product(request,slug_store,slug_product)
    shop=product.shop
    if qs.exists() and qs.count()==1:
        order=qs.first()
        if order.shop == None:
            order.shop=shop
            order.save()
        elif order.shop != shop:
            return render(request,'store/cart_error.html',{'product':product,'order':order,})
        create_or_update_order_item(order,product)
    else:
        order=Order(customer=request.user.customer,shop=shop)
        order.save()
        create_or_update_order_item(order,product)
    return redirect(product.shop.get_absolute_url)

@check_access(allowed_users=['Customer',])
def CartView(request):
    try:
        order=Order.objects.get(customer=request.user.customer,is_completed=False)
        if order.order_item.count() == 0:
            raise Exception('Cart is Empty!')
        order_items=order.order_item.all()
        context={
            'order':order,
            'order_items':order_items
        }
        return render(request,'store/cart.html',context)
    except:
        return render(request,'store/error.html',{'error_message':'Cart is Empty!',})
@check_access(allowed_users=['anonymous','Customer',])
def search(request):
    query=request.GET.get('query')
    shop_qs=Shop.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query)
         ).distinct()
    product_qs=Product.objects.filter(name__icontains=query).distinct()
    shop=shop_qs.exists()
    product=product_qs.exists()
    context={
        'shop': shop,
        'product': product,
        'shop_qs':shop_qs,
        'product_qs' : product_qs,
    }
    return render(request,'store/search.html',context) 

@check_access(allowed_users=['Customer',])
def remove_from_cart(request,slug_store,slug_product):
    try:
        qs=Order.objects.filter(customer=request.user.customer,is_completed=False)
    except:
        return render(request,'store/error.html',{'error_message':'You are not authorized to order products!',})
    product=get_product(request,slug_store,slug_product)
    shop=product.shop
    if qs.exists() and qs.count() == 1:
        order=qs.first()
        req_order_item_qs=order.order_item.filter(product=product).delete()
        if order.order_item.count() == 0:
            order.shop=None
        order.save()
        return redirect('store:cart')
    return render(request,'store/error.html')
@check_access(allowed_users=['Customer',])
def decrease_order_item_quantity(request,slug_store,slug_product):
    try:
        qs=Order.objects.filter(customer=request.user.customer,is_completed=False)
    except:
        return render(request,'store/error.html',{'error_message':'You are not authorized to order products!',})
    product=get_product(request,slug_store,slug_product)
    shop=product.shop
    if qs.exists() and qs.count() == 1:
        order=qs.first()
        req_order_item_qs=order.order_item.filter(product=product)
        if req_order_item_qs.exists() and req_order_item_qs.count() == 1:
            req_order_item=req_order_item_qs.first()
            if req_order_item.quantity == 1:
                req_order_item_qs.all().delete()
                if order.order_item.count() == 0:
                    order.shop=None
            else:
                req_order_item.quantity=req_order_item.quantity-1
                req_order_item.save()
            order.save()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return render(request,'store/error.html')

@check_access(allowed_users=['Customer',])
def increase_order_item_quantity(request,slug_store,slug_product):
    try:
        qs=Order.objects.filter(customer=request.user.customer,is_completed=False)
    except:
        return render(request,'store/error.html',{'error_message':'You are not authorized to order products!',})
    product=get_product(request,slug_store,slug_product)
    shop=product.shop
    if qs.exists() and qs.count() == 1:
        order=qs.first()
        req_order_item_qs=order.order_item.filter(product=product)
        if req_order_item_qs.exists() and req_order_item_qs.count() == 1:
            req_order_item=req_order_item_qs.first()
            req_order_item.quantity=req_order_item.quantity+1
            req_order_item.save()
            order.save()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    return render(request,'store/error.html')

@check_access(allowed_users=['Customer',])
def fresh_cart(request,slug_store,slug_product):
    try:
        qs=Order.objects.filter(customer=request.user.customer,is_completed=False)
    except:
        return render(request,'store/error.html',{'error_message':'You are not authorized to order products!',})
    product=get_product(request,slug_store,slug_product)
    shop=product.shop
    if qs.exists() and qs.count() == 1:
        order=qs.first()
        order.order_item.all().delete()
        order.shop=shop
        order.save()
        create_or_update_order_item(order,product)
        return redirect(shop.get_absolute_url)
    return render(request,'store/error.html')

def create_or_update_rating(shop,customer,rating):
    try:
        rate_obj=Rating.objects.get(shop=shop,customer=customer)
    except:
        rate_obj=Rating(shop=shop,customer=customer)
    rate_obj.rate=rating
    rate_obj.save()

@check_access(allowed_users=['Customer',])
def RatingView(request,slug_store):
    path=request.GET.get('next')
    if request.method == 'POST':
        rating=int(request.POST.get('rating'))
        try:
            shop=Shop.objects.get(slug_store=slug_store)
            create_or_update_rating(shop,request.user.customer,rating)
            if path == None:
                return redirect('store:home')
            messages.success(request,'Thanks for giving your valuable feedback!')
            return redirect(path)
        except:
            return render(request,'store/error.html')
    return render(request,'store/error.html')

def get_delivery_boy():
    qs=DelivaryBoy.objects.filter(is_available=True)
    if qs.exists():
        minimum=100001
        for boy in qs:
            temp=boy.get_active_orders
            if minimum > temp:
                minimum=temp
        for boy in qs:
            if boy.get_active_orders == minimum:
                return boy
    return None

@check_access(allowed_users=['Customer',])
def checkout(request):
    if request.method == 'POST':
        form=CustomerAddressForm(request.POST)
        print('codervp')
        if form.is_valid():
            try:
                r_name=request.POST.get('r_name')
                r_ph_no=request.POST.get('r_ph_no')
                address_flag=int(request.POST.get('address_flag'))
                print(address_flag)
                print('coderbobby')
                address=None
                if address_flag == 0:
                    temp_address=form.instance
                    temp_address.customer=request.user.customer
                    address=form.save()
                else:
                    address=request.user.customer.address.get(id=address_flag)
                qs=Order.objects.filter(customer=request.user.customer,is_completed=False)
                order=None
                if qs.exists() and qs.count() == 1:
                    order=qs.first()
                else:
                    raise Exception('Invalid!')
                delivery_boy=get_delivery_boy()
                if delivery_boy is None:
                    return HttpResponse('Sorry For Inconvenience! There is no Delivery boy available.')
                order_shipping=OrderShipping(customer=request.user.customer,order=order,name=r_name,phone_number=r_ph_no,delivery_boy=delivery_boy,address=address)
                order_shipping.save()
                order.is_completed=True
                order.save()
                messages.success(request,'Your order has placed successfully!')
                return redirect(order_shipping.get_absolute_url)
            except:
                return render(request,'store/error.html')
        return render(request,'store/checkout.html',{'form':form,})
    form=CustomerAddressForm()
    return render(request,'store/checkout.html',{'form':form,})

@check_access(allowed_users=['Customer','DeliveryBoy','ShopOwner'])
def order_detail_view(request,customer,order_id,id):
    try:
        customer_obj=Customer.objects.get(user__username=customer)
        order_obj=Order.objects.get(id=order_id)
        order_shipping_obj=OrderShipping.objects.get(customer=customer_obj,order=order_obj,id=id)
        context={
            'obj':order_shipping_obj,
        }
        return render(request,'store/order_detail.html',context)
    except:
        return render(request,'store/error.html')

@check_access(allowed_users=['Customer',])
def customer_orders_view(request,customer):
    try:
        customer_obj=Customer.objects.get(user__username=customer)
        f_qs=OrderShipping.objects.filter(customer=customer_obj)
        active_orders=f_qs.filter(is_delivered=False).order_by('-date_shipped')
        completed_orders=f_qs.filter(is_delivered=True).order_by('-date_shipped')
        active=active_orders.exists()
        completed=completed_orders.exists()
        context={
            'active_orders':active_orders,
            'completed_orders':completed_orders,
            'active':active,
            'completed':completed
        }
        return render(request,'store/customer_orders.html',context)
    except:
        return render(request,'store/error.html')

@check_access(allowed_users=['DeliveryBoy',])    
def order_delivered_view(request,id):
    if request.method == 'POST':
        try:
            order_shipping=OrderShipping.objects.get(id=id)
            order_shipping.is_delivered=True
            order_shipping.save()
            return redirect(order_shipping.get_absolute_url)
        except:
            return render(request,'store/error.html')
    else:
        return render(request,'store/error.html')