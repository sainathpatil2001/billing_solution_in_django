from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Unit
from genrate_bill.models import BusinessInformation
from .forms import ProductForm, UpdateProductForm, CategoryForm, UnitForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from decimal import Decimal
import json

def landing_home_page(request):    
    return render(request, 'inventory/landing_page.html')

def billing_page(request):
    # Get only active products (show_product=True) and with stock > 0
    active_products = Product.objects.filter(show_product=True, quantity__gt=0).order_by('name')
    categories = Category.objects.all()
    
    context = {
        'products': active_products,
        'categories': categories
    }
    return render(request, 'inventory/billing_page.html', context)

def Manage_inventory(request):
    form = ProductForm()
    products = Product.objects.select_related('category', 'unit').all().order_by('-id')
    categories = Category.objects.all()
    units = Unit.objects.all()
    
    context = {
        "form": form,
        "products": products,
        "categories": categories,
        "units": units,
        "active_tab": request.GET.get('tab', 'add-product'),
        "business_info": BusinessInformation.get_business_info()
    }
    
    if request.method == 'POST':
        if 'product_id' in request.POST:  # Update product
            product = get_object_or_404(Product, id=request.POST.get('product_id'))
            form = UpdateProductForm(request.POST, instance=product)
            if form.is_valid():
                try:
                    form.save()
                    context['success'] = f"Product '{product.name}' was successfully updated!"
                    context['active_tab'] = 'update-product'
                except Exception as e:
                    context['error'] = f"Error saving product: {str(e)}"
                    context['active_tab'] = 'update-product'
            else:
                error_messages = [f"{field}: {error[0]}" for field, error in form.errors.items()]
                context['error'] = f"Invalid form data: {', '.join(error_messages)}"
                context['active_tab'] = 'update-product'
        else:  # Add new product
            form = ProductForm(request.POST)
            if form.is_valid():
                try:
                    product = form.save()
                    context['success'] = f"Product '{product.name}' was successfully added!"
                    context['active_tab'] = 'add-product'
                except Exception as e:
                    context['error'] = f"Error saving product: {str(e)}"
            else:
                error_messages = [f"{field}: {error[0]}" for field, error in form.errors.items()]
                context['error'] = f"Invalid form data: {', '.join(error_messages)}"

    return render(request, 'inventory/inventory_dashboard.html', context)

def product_details(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        data = {
            "id": product.id,
            "name": product.name,
            "category": {
                "id": product.category.id,
                "name": product.category.name,
                "is_food_item": product.category.is_food_item
            } if product.category else None,
            "unit": {
                "id": product.unit.id,
                "name": product.unit.name,
                "symbol": product.unit.symbol
            } if product.unit else None,
            "dealer_price": float(product.dealer_price),
            "selling_price": float(product.selling_price),
            "mrp": float(product.mrp),
            "quantity": float(product.quantity),
            "gst_rate": float(product.gst_rate),
            "igst": float(product.igst),
            "cgst": float(product.cgst),
            "sgst": float(product.sgst),
            "batch_number": product.batch_number,
            "hsn_number": product.hsn_number,
            "mfg_date": product.mfg_date.strftime("%Y-%m-%d") if product.mfg_date else None,
            "expiry_date": product.expiry_date.strftime("%Y-%m-%d") if product.expiry_date else None,
            "minimum_stock": float(product.minimum_stock),
            "show_product": product.show_product,
            "stock_status": product.stock_status,
            "total_value": float(product.total_value),
            "last_updated": product.last_updated.strftime("%Y-%m-%d %H:%M:%S")
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

def search_product(request):
    query = request.GET.get('query', '').strip()
    category_id = request.GET.get('category')
    
    try:
        products = Product.objects.all()
        
        if category_id:
            products = products.filter(category_id=category_id)
        
        if query:
            if query.isdigit():
                products = products.filter(id=query)
                if not products:
                    products = products.filter(name__icontains=query)
            else:
                products = products.filter(name__icontains=query)
        
        products = products[:5]
        
        data = {
            "products": [{
                "id": p.id,
                "name": p.name,
                "category": p.category.name if p.category else None,
                "unit": p.unit.symbol if p.unit else None,
                "dealer_price": float(p.dealer_price),
                "selling_price": float(p.selling_price),
                "mrp": float(p.mrp),
                "gst_rate": float(p.gst_rate),
                "igst": float(p.igst),
                "cgst": float(p.cgst),
                "sgst": float(p.sgst),
                "batch_number": p.batch_number,
                "hsn_number": p.hsn_number,
                "mfg_date": p.mfg_date.strftime("%Y-%m-%d") if p.mfg_date else None,
                "expiry_date": p.expiry_date.strftime("%Y-%m-%d") if p.expiry_date else None,
                "quantity": float(p.quantity),
                "minimum_stock": float(p.minimum_stock),
                "show_product": p.show_product,
                "stock_status": p.stock_status
            } for p in products]
        }
    except Exception as e:
        data = {"error": str(e), "products": []}
    
    return JsonResponse(data)

@require_POST
def delete_product(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        product_name = product.name
        product.delete()
        return JsonResponse({
            'success': True,
            'message': f'Product "{product_name}" deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@require_http_methods(["GET", "POST", "DELETE"])
def manage_units(request, unit_id=None):
    if request.method == "DELETE" and unit_id:
        try:
            unit = get_object_or_404(Unit, id=unit_id)
            if Product.objects.filter(unit=unit).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot delete unit as it is being used by some products'
                })
            unit.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            unit = Unit.objects.create(
                name=data['name'],
                symbol=data['symbol']
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'errors': str(e)})
    
    units = Unit.objects.all()
    return JsonResponse({'units': list(units.values())})

@require_http_methods(["GET", "POST", "DELETE"])
def manage_categories(request, category_id=None):
    if request.method == "DELETE" and category_id:
        try:
            category = get_object_or_404(Category, id=category_id)
            if Product.objects.filter(category=category).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot delete category as it contains products'
                })
            category.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            category = Category.objects.create(
                name=data['name'],
                description=data.get('description', ''),
                is_food_item=data.get('is_food_item', False)
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'errors': str(e)})
    
    categories = Category.objects.all()
    return JsonResponse({'categories': list(categories.values())})



