from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from inventory.models import Product, Category
from .models import Customer, Bill, BillItem, BusinessInformation
from decimal import Decimal, ROUND_HALF_UP
import json
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.db.models import Q
from datetime import datetime, timezone, time
from django.utils import timezone
from datetime import timedelta
from .models import Customer, Bill, BillItem, BusinessInformation, ActivationKey
from django.shortcuts import redirect
import io
import zipfile
import os
from django.core.management import call_command
from django.conf import settings
from django.http import HttpResponse
from inventory.models import Category, Unit
from django.core import serializers


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
                    address=data['customer'].get('address', ''),
                    city=data['customer'].get('city', ''),
                    district=data['customer'].get('district', ''),
                    state=data['customer'].get('state', ''),
                    pincode=data['customer'].get('pincode', ''),
                    sub_district=data['customer'].get('sub_district', ''),
                    gst_number=data['customer'].get('gst_number', ''),
                    extra_note=data['customer'].get('extra_note', '')
                )
                
                # Calculate totals
                total_amount = Decimal('0')
                items_to_process = []
                
                for item in data.get('items', []):
                    product = Product.objects.get(id=item['product_id'])
                    quantity = Decimal(str(item['quantity']))
                    base_amount = product.selling_price * quantity
                    
                    hsn = item.get('hsn_number', product.hsn_number)
                    mfg_date = item.get('mfg_date')
                    unit = item.get('unit', product.unit.symbol if product.unit else '')
                    
                    is_igst = item.get('is_igst', False)
                    gst_rate = Decimal(str(item.get('gst_rate', product.gst_rate)))
                    
                    igst_rate = Decimal('0')
                    cgst_rate = Decimal('0')
                    sgst_rate = Decimal('0')
                    igst_amount = Decimal('0')
                    cgst_amount = Decimal('0')
                    sgst_amount = Decimal('0')
                    
                    if is_igst:
                         igst_rate = gst_rate
                         igst_amount = ((base_amount * igst_rate) / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    else:
                         cgst_rate = gst_rate / 2
                         sgst_rate = gst_rate / 2
                         cgst_amount = ((base_amount * cgst_rate) / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                         sgst_amount = ((base_amount * sgst_rate) / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    
                    item_total = (base_amount + cgst_amount + sgst_amount + igst_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    total_amount += item_total
                    
                    # Parse dates
                    mfg_date_obj = None
                    if mfg_date:
                        try:
                            mfg_date_obj = datetime.strptime(mfg_date, '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                mfg_date_obj = datetime.strptime(mfg_date, '%Y-%m').date()
                            except ValueError:
                                pass
                            
                    expiry_date = item.get('expiry_date')
                    expiry_date_obj = product.expiry_date
                    if expiry_date:
                        try:
                            expiry_date_obj = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                        except ValueError:
                            try:
                                expiry_date_obj = datetime.strptime(expiry_date, '%Y-%m').date()
                            except ValueError:
                                pass

                    items_to_process.append({
                        'product': product,
                        'quantity': quantity,
                        'price': product.selling_price,
                        'cgst_rate': cgst_rate,
                        'cgst_amount': cgst_amount,
                        'sgst_rate': sgst_rate,
                        'sgst_amount': sgst_amount,
                        'igst_rate': igst_rate,
                        'igst_amount': igst_amount,
                        'total': item_total,
                        'mrp': product.mrp,
                        'batch_number': item.get('batch_number', product.batch_number),
                        'expiry_date': expiry_date_obj,
                        'mfg_date': mfg_date_obj,
                        'hsn_number': hsn,
                        'unit': unit
                    })
                
                discount = Decimal(str(data.get('discount', '0')))
                final_amount = total_amount - discount
                
                payment_status = data.get('payment_status', 'Pending')
                
                # Calculate amounts based on status
                if payment_status == 'Paid':
                    paid_amount = final_amount
                    remaining_amount = Decimal('0')
                    payment_mode = data.get('payment_mode')
                elif payment_status == 'Partially Paid':
                    paid_amount = Decimal(str(data.get('paid_amount', '0')))
                    if paid_amount > final_amount:
                        paid_amount = final_amount
                    remaining_amount = final_amount - paid_amount
                    payment_mode = data.get('payment_mode')
                else: # Pending
                    paid_amount = Decimal('0')
                    remaining_amount = final_amount
                    payment_mode = None

                payment_date = data.get('payment_date')
                
                # Transport Details
                transport_mode = data.get('transport_mode', '')
                vehicle_number = data.get('vehicle_number', '')
                place_of_supply = data.get('place_of_supply', '')
                supply_date_str = data.get('supply_date', '')
                supply_date = None
                if supply_date_str:
                    try:
                        supply_date = datetime.strptime(supply_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        pass
                
                # Create bill with date
                bill = Bill.objects.create(
                    customer=customer,
                    total_amount=total_amount,
                    discount=discount,
                    final_amount=final_amount,
                    date=timezone.now(),
                    payment_status=payment_status,
                    payment_mode=payment_mode,
                    payment_date=payment_date if payment_date else None,
                    paid_amount=paid_amount,
                    remaining_amount=remaining_amount,
                    transport_mode=transport_mode,
                    vehicle_number=vehicle_number,
                    place_of_supply=place_of_supply,
                    supply_date=supply_date
                )
                
                # Create bill items
                for item in items_to_process:
                    BillItem.objects.create(
                        bill=bill,
                        product=item['product'],
                        quantity=item['quantity'],
                        price=item['price'],
                        cgst_rate=item['cgst_rate'],
                        cgst_amount=item['cgst_amount'],
                        sgst_rate=item['sgst_rate'],
                        sgst_amount=item['sgst_amount'],
                        igst_rate=item['igst_rate'],
                        igst_amount=item['igst_amount'],
                        total_price=item['total'],
                        mrp=item['mrp'],
                        batch_number=item['batch_number'],
                        expiry_date=item['expiry_date'],
                        mfg_date=item['mfg_date'],
                        hsn_number=item['hsn_number'],
                        unit=item['unit']
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
            
    business_info = BusinessInformation.get_business_info()
    return render(request, 'genrate_bill/billing.html', {
        'business_info': business_info
    })

def search_billing_products(request):
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'products': []})

    try:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(id__icontains=query) |
            Q(hsn_number__icontains=query) |
            Q(batch_number__icontains=query),
            show_product=True,
            quantity__gt=0
        ).select_related('category', 'unit').order_by('name')[:10]  # Limit to 10 results

        products_data = [{
            'id': product.id,
            'name': product.name,
            'price': float(product.selling_price),  # Frontend expects 'price' not 'selling_price'
            'stock': float(product.quantity),  # Frontend expects 'stock' not 'quantity'
            'unit': product.unit.symbol if product.unit else '',  # Add unit information
            'category': product.category.name if product.category else '',  # Add category information
            'selling_price': str(product.selling_price),  # Keep for backward compatibility
            'quantity': str(product.quantity),  # Keep for backward compatibility
            'gst_rate': str(product.gst_rate),  # Add GST rate
            'igst': str(product.igst),
            'cgst': str(product.cgst),
            'sgst': str(product.sgst),
            'mrp': str(product.mrp),
            'batch_number': product.batch_number,
            'hsn_number': product.hsn_number,
            'expiry_date': product.expiry_date.strftime('%Y-%m-%d') if product.expiry_date else '',
            'mfg_date': product.mfg_date.strftime('%Y-%m-%d') if product.mfg_date else ''
        } for product in products]

        return JsonResponse({'products': products_data})
    except Exception as e:
        print(f"Product search error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)

def bills_page(request):
    """Render the bills listing page"""
    business_info = BusinessInformation.get_business_info()
    return render(request, 'genrate_bill/bills.html', {'business_info': business_info})

def backup_page(request):
    """Render the backup and restore page"""
    business_info = BusinessInformation.get_business_info()
    return render(request, 'genrate_bill/backup.html', {'business_info': business_info})

def search_bills(request):
    """Search for bills in real-time"""
    try:
        bill_number = request.GET.get('bill_number', '')
        customer_name = request.GET.get('customer_name', '')
        date_str = request.GET.get('date', '')
        payment_status = request.GET.get('payment_status', '')

        # Start with all bills, ordered by newest first
        bills = Bill.objects.all().order_by('-date')

        # Apply filters
        if bill_number:
            bills = bills.filter(bill_number__icontains=bill_number)
            
        if customer_name:
            bills = bills.filter(customer__name__icontains=customer_name)
            
        if payment_status:
            bills = bills.filter(payment_status=payment_status)
            
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
                    'customer_address': bill.customer.address if bill.customer else '',
                    'total_amount': str(bill.total_amount),
                    'discount': str(bill.discount),
                    'final_amount': str(bill.final_amount),
                    'payment_status': bill.payment_status,
                    'payment_mode': bill.payment_mode,
                    'paid_amount': str(bill.paid_amount),
                    'remaining_amount': str(bill.remaining_amount),
                    'payment_date': bill.payment_date.strftime('%Y-%m-%d') if bill.payment_date else ''
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
        business_info = BusinessInformation.get_business_info()
        
        bill_data = {
            'bill_number': bill.bill_number,
            'date': bill.date.strftime('%Y-%m-%d %H:%M') if bill.date else '',
            'customer_name': bill.customer.name if bill.customer else 'N/A',
            'customer_phone': bill.customer.phone if bill.customer else '',
            'customer_address': bill.customer.address if bill.customer else '',
            'customer_pincode': bill.customer.pincode if bill.customer else '',
            'customer_sub_district': bill.customer.sub_district if bill.customer else '',
            'customer_gst_number': bill.customer.gst_number if bill.customer else '',
            'total_amount': str(bill.total_amount),
            'discount': str(bill.discount),
            'final_amount': str(bill.final_amount),
            'transport_mode': bill.transport_mode or '',
            'vehicle_number': bill.vehicle_number or '',
            'place_of_supply': bill.place_of_supply or '',
            'supply_date': bill.supply_date.strftime('%Y-%m-%d') if bill.supply_date else '',
            'business_info': {
                'company_name': business_info.company_name,
                'address_line1': business_info.address_line1,
                'address_line2': business_info.address_line2,
                'phone': business_info.phone,
                'email': business_info.email,
                'gst_number': business_info.gst_number,
                'city': business_info.city,
                'pincode': business_info.pincode,
                'state': business_info.state,
                'district': business_info.district,
                'sub_district': business_info.sub_district,
                'website': business_info.website,
                'signature_url': business_info.signature.url if business_info.signature else '',
                'website': business_info.website,
                'signature_url': business_info.signature.url if business_info.signature else '',
                'logo_url': business_info.logo.url if business_info.logo else '',
                'logo_url': business_info.logo.url if business_info.logo else '',
                'upi_id': business_info.upi_id,
                'terms_and_conditions': business_info.terms_and_conditions.split('\n')
            },
            'payment_status': bill.payment_status,
            'payment_mode': bill.payment_mode,
            'payment_date': bill.payment_date.strftime('%Y-%m-%d') if bill.payment_date else '',
            'paid_amount': str(bill.paid_amount),
            'remaining_amount': str(bill.remaining_amount),
            'items': []
        }

        for item in items:
            try:
                bill_data['items'].append({
                    'product_name': item.product.name if item.product else 'N/A',
                    'quantity': str(item.quantity),
                    'unit': item.product.unit.symbol if item.product and item.product.unit else '',
                    'price': str(item.price),
                    'cgst_rate': str(item.cgst_rate),
                    'cgst_amount': str(item.cgst_amount),
                    'sgst_rate': str(item.sgst_rate),
                    'sgst_amount': str(item.sgst_amount),
                    'igst_rate': str(item.igst_rate or 0),
                    'igst_amount': str(item.igst_amount or 0),
                    'hsn_number': item.hsn_number,
                    'mfg_date': item.mfg_date.strftime('%Y-%m-%d') if item.mfg_date else '',
                    'total_price': str(item.total_price),
                    'mrp': str(item.mrp),
                    'batch_number': item.batch_number,
                    'expiry_date': item.expiry_date.strftime('%Y-%m-%d') if item.expiry_date else ''
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

def business_settings(request):
    """Business settings page"""
    business_info = BusinessInformation.get_business_info()
    
    if request.method == 'POST':
        try:
            business_info.company_name = request.POST.get('company_name', '')
            business_info.address_line1 = request.POST.get('address_line1', '')
            business_info.address_line2 = request.POST.get('address_line2', '')
            business_info.phone = request.POST.get('phone', '')
            business_info.email = request.POST.get('email', '')
            business_info.gst_number = request.POST.get('gst_number', '')
            business_info.website = request.POST.get('website', '')
            if request.FILES.get('signature'):
                business_info.signature = request.FILES['signature']
            if request.FILES.get('logo'):
                business_info.logo = request.FILES['logo']
            
            # Update password if provided
            password = request.POST.get('security_password')
            if password:
                business_info.security_password = password
            
            business_info.city = request.POST.get('city', '')
            business_info.pincode = request.POST.get('pincode', '')
            business_info.state = request.POST.get('state', '')
            business_info.district = request.POST.get('district', '')
            business_info.sub_district = request.POST.get('sub_district', '')

            business_info.upi_id = request.POST.get('upi_id', '')
            business_info.terms_and_conditions = request.POST.get('terms_and_conditions', '')
                
            business_info.save()
            
            return JsonResponse({'success': True, 'message': 'Business information updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    
    # Calculate days remaining
    days_remaining = 0
    if business_info.activation_expiry_date:
        days_remaining = (business_info.activation_expiry_date - timezone.now().date()).days
    
    return render(request, 'genrate_bill/business_settings.html', {
        'business_info': business_info,
        'days_remaining': days_remaining,
        'is_expired': days_remaining <= 0
    })

def activation_page(request):
    """Render the activation page"""
    business_info = BusinessInformation.get_business_info()
    
    # Check if already activated and valid
    if business_info.activation_expiry_date and business_info.activation_expiry_date > timezone.now().date():
        return redirect('billing') # Redirect to home/billing if already active
        
    return render(request, 'genrate_bill/activation.html', {'business_info': business_info})

@require_http_methods(["POST"])
def activate_license(request):
    """Handle license key submission"""
    try:
        data = json.loads(request.body)
        key_input = data.get('key', '').strip()
        
        if not key_input:
            return JsonResponse({'success': False, 'error': 'Please enter a key'})
            
        # Find the key
        # Try exact match first
        activation_key = ActivationKey.objects.filter(key=key_input, is_used=False).first()
        
        # If not found, try appending a dash (in case DB has it but user omitted)
        if not activation_key:
             activation_key = ActivationKey.objects.filter(key=key_input + '-', is_used=False).first()
             
        # If still not found, try removing a dash (in case user added it but DB doesn't have it)
        if not activation_key and key_input.endswith('-'):
             activation_key = ActivationKey.objects.filter(key=key_input.rstrip('-'), is_used=False).first()

        if not activation_key:
            return JsonResponse({'success': False, 'error': f'Invalid or already used activation key.'})
            
        # Activate
        business_info = BusinessInformation.get_business_info()
        current_expiry = business_info.activation_expiry_date
        
        # If expired or never activated, start from today. If valid, extend from current expiry.
        start_date = timezone.now().date()
        if current_expiry and current_expiry > start_date:
            start_date = current_expiry
            
        new_expiry = start_date + timedelta(days=activation_key.duration_months * 30) # Approx 6 months
        
        business_info.activation_expiry_date = new_expiry
        business_info.save()
        
        # Mark key as used
        activation_key.is_used = True
        activation_key.used_at = timezone.now()
        activation_key.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Activation successful! Valid until {new_expiry.strftime("%Y-%m-%d")}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["GET"])
def create_backup(request):
    """Generate and download a full system backup"""
    try:
        # Create a zip file in memory
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            # 1. Dump Database Data
            # flexible way: serialize all relevant models
            models_to_backup = [
                BusinessInformation, Category, Unit, Product, 
                Customer, Bill, BillItem, ActivationKey
            ]
            
            all_objects = []
            for model in models_to_backup:
                all_objects.extend(list(model.objects.all()))
                
            json_data = serializers.serialize('json', all_objects)
            zip_file.writestr('data.json', json_data)
            
            # 2. Backup Media Files (Logos, Signatures)
            if os.path.exists(settings.MEDIA_ROOT):
                for root, dirs, files in os.walk(settings.MEDIA_ROOT):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Archive name relative to media root
                        arcname = os.path.join('media', os.path.relpath(file_path, settings.MEDIA_ROOT))
                        zip_file.write(file_path, arcname)
                        
        # Finalize zip
        buffer.seek(0)
        
        # Update last backup date
        access_info = BusinessInformation.get_business_info()
        access_info.last_backup_date = timezone.now()
        access_info.save()
        
        filename = f"backup_billing_{timezone.now().strftime('%Y%m%d_%H%M%S')}.zip"
        response = HttpResponse(buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
def restore_backup(request):
    """Restore system from a backup zip"""
    try:
        if 'backup_file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'No file uploaded'}, status=400)
            
        backup_file = request.FILES['backup_file']
        
        if not backup_file.name.endswith('.zip'):
            return JsonResponse({'success': False, 'error': 'Invalid file format. Please upload a .zip file'}, status=400)
            
        with zipfile.ZipFile(backup_file, 'r') as zip_ref:
            # 1. Restore Media
            for file in zip_ref.namelist():
                if file.startswith('media/'):
                    # Extract to media root
                    target_path = os.path.join(settings.MEDIA_ROOT, os.path.relpath(file, 'media'))
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, 'wb') as f:
                        f.write(zip_ref.read(file))
            
            # 2. Restore Data
            if 'data.json' in zip_ref.namelist():
                data_content = zip_ref.read('data.json').decode('utf-8')
                
                # We need to be careful about not duplicating active business info if it exists
                # But deserializer handles PKs, so it should update existing records if PKs match
                objects = serializers.deserialize('json', data_content)
                
                with transaction.atomic():
                    for obj in objects:
                        obj.save()
                        
        return JsonResponse({'success': True, 'message': 'System restored successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
def update_backup_settings(request):
    """Update backup reminder preference"""
    try:
        data = json.loads(request.body)
        days = int(data.get('days', 7))
        
        info = BusinessInformation.get_business_info()
        info.backup_reminder_days = days
        info.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["POST"])
@ensure_csrf_cookie
def update_payment_status(request, bill_id):
    try:
        data = json.loads(request.body)
        password = data.get('password')
        new_status = data.get('status')
        payment_mode = data.get('payment_mode')
        payment_date = data.get('payment_date')
        
        # Verify password
        business_info = BusinessInformation.get_business_info()
        if business_info.security_password != password:
            return JsonResponse({'success': False, 'error': 'Invalid security password'}, status=403)
            
        bill = Bill.objects.get(bill_number=bill_id)
        bill.payment_status = new_status
        
        if new_status == 'Paid':
            bill.payment_mode = payment_mode
            bill.paid_amount = bill.final_amount
            bill.remaining_amount = Decimal('0')
            if payment_date:
                bill.payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
            else:
                bill.payment_date = timezone.now().date()
        elif new_status == 'Partially Paid':
            bill.payment_mode = payment_mode
            # Handle user provided amount
            paid_val = Decimal(str(data.get('paid_amount', '0')))
            if paid_val > bill.final_amount:
                paid_val = bill.final_amount
                
            bill.paid_amount = paid_val
            bill.remaining_amount = bill.final_amount - bill.paid_amount
            
            if payment_date:
                bill.payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
            else:
                bill.payment_date = timezone.now().date()
        else:
            bill.payment_mode = None
            bill.payment_date = None
            bill.paid_amount = Decimal('0')
            bill.remaining_amount = bill.final_amount
            
        bill.save()
        
        return JsonResponse({'success': True, 'message': 'Payment status updated successfully'})
        
    except Bill.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bill not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
