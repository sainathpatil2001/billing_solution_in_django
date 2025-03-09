from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from inventory.models import Product, Category
from .models import Customer, Bill, BillItem
from decimal import Decimal
import json
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.db.models import Q
from datetime import datetime, timezone, time
from django.utils import timezone


# Create your views here.

@require_http_methods(["GET", "POST"])
@ensure_csrf_cookie
def generate_bill(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            with transaction.atomic():
                # Create customer
                customer = Customer.objects.create(
                    name=data['customer']['name'],
                    phone=data['customer'].get('phone', ''),
                    address=data['customer'].get('address', '')
                )
                
                # Calculate totals
                total_amount = Decimal('0')
                items_to_process = []
                
                for item in data.get('items', []):
                    product = Product.objects.get(id=item['product_id'])
                    quantity = Decimal(str(item['quantity']))
                    item_total = product.selling_price * quantity
                    total_amount += item_total
                    items_to_process.append({
                        'product': product,
                        'quantity': quantity,
                        'price': product.selling_price,
                        'total': item_total
                    })
                
                discount = Decimal(str(data.get('discount', '0')))
                final_amount = total_amount - discount
                
                # Create bill with date
                bill = Bill.objects.create(
                    customer=customer,
                    total_amount=total_amount,
                    discount=discount,
                    final_amount=final_amount,
                    date=timezone.now()  # Set the current date and time
                )
                
                # Create bill items
                for item in items_to_process:
                    BillItem.objects.create(
                        bill=bill,
                        product=item['product'],
                        quantity=item['quantity'],
                        price=item['price'],
                        total_price=item['total']
                    )
                    
                    # Update inventory
                    product = item['product']
                    product.quantity -= item['quantity']
                    product.save()
                
                return JsonResponse({
                    'success': True,
                    'bill_number': bill.bill_number,
                    'message': 'Bill generated successfully'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
            
    return render(request, 'genrate_bill/billing.html')

def search_billing_products(request):
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'products': []})

    try:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(id__icontains=query),
            show_product=True,
            quantity__gt=0
        ).order_by('name')[:10]  # Limit to 10 results

        products_data = [{
            'id': product.id,
            'name': product.name,
            'selling_price': str(product.selling_price),
            'quantity': str(product.quantity)
        } for product in products]

        return JsonResponse({'products': products_data})
    except Exception as e:
        print(f"Product search error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

def bills_page(request):
    """Render the bills listing page"""
    return render(request, 'genrate_bill/bills.html')

def search_bills(request):
    """Search for bills in real-time"""
    try:
        bill_number = request.GET.get('bill_number', '')
        customer_name = request.GET.get('customer_name', '')
        date_str = request.GET.get('date', '')

        # Start with all bills, ordered by newest first
        bills = Bill.objects.all().order_by('-date')

        # Apply filters
        if bill_number:
            bills = bills.filter(bill_number__icontains=bill_number)
            
        if customer_name:
            bills = bills.filter(customer__name__icontains=customer_name)
            
        if date_str:
            try:
                # Convert string to datetime
                search_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Create datetime objects for start and end of the day
                start_datetime = datetime.combine(search_date, time.min)
                end_datetime = datetime.combine(search_date, time.max)
                
                # Filter bills between start and end of the day
                bills = bills.filter(date__range=(start_datetime, end_datetime))
                
            except Exception as e:
                print(f"Date filtering error: {str(e)}")
                # Continue without date filter if there's an error

        # Limit results for better performance
        bills = bills[:50]

        bills_data = []
        for bill in bills:
            try:
                bills_data.append({
                    'id': bill.bill_number,
                    'bill_number': bill.bill_number,
                    'date': bill.date.strftime('%Y-%m-%d') if bill.date else '',
                    'customer_name': bill.customer.name if bill.customer else 'N/A',
                    'customer_phone': bill.customer.phone if bill.customer else '',
                    'total_amount': str(bill.total_amount),
                    'discount': str(bill.discount),
                    'final_amount': str(bill.final_amount)
                })
            except Exception as e:
                print(f"Error processing bill {bill.bill_number}: {str(e)}")
                continue

        return JsonResponse({
            'success': True, 
            'bills': bills_data,
            'filters': {
                'date': date_str,
                'bill_number': bill_number,
                'customer_name': customer_name
            }
        })
    except Exception as e:
        print(f"Search error: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=400)

def get_bill_details(request, bill_id):
    """Get details of a specific bill"""
    try:
        bill = Bill.objects.get(bill_number=bill_id)
        items = BillItem.objects.filter(bill=bill)
        
        bill_data = {
            'bill_number': bill.bill_number,
            'date': bill.date.strftime('%Y-%m-%d %H:%M') if bill.date else '',
            'customer_name': bill.customer.name if bill.customer else 'N/A',
            'customer_phone': bill.customer.phone if bill.customer else '',
            'customer_address': bill.customer.address if bill.customer else '',
            'total_amount': str(bill.total_amount),
            'discount': str(bill.discount),
            'final_amount': str(bill.final_amount),
            'items': []
        }

        for item in items:
            try:
                bill_data['items'].append({
                    'product_name': item.product.name if item.product else 'N/A',
                    'quantity': str(item.quantity),
                    'price': str(item.price),
                    'total_price': str(item.total_price)
                })
            except Exception as e:
                print(f"Error processing item in bill {bill_id}: {str(e)}")
                continue

        return JsonResponse({'success': True, 'bill': bill_data})
    except Bill.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'error': 'Bill not found'
        }, status=404)
    except Exception as e:
        print(f"Error fetching bill details: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=400)
