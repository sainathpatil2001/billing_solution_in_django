from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from inventory.models import Product, Category
from .models import Customer, Bill, BillItem, BusinessInformation, PaymentHistory
import decimal
from decimal import Decimal, ROUND_HALF_UP
import json
import zipfile
import io
from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from django.db.models import Q
from datetime import datetime, date, time, timedelta
from django.utils import timezone
from django.shortcuts import redirect
import os
from django.core.management import call_command
from django.conf import settings
from django.http import HttpResponse
from django.core import serializers
import csv
from django.db.models import Sum, Count, F
from collections import defaultdict


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
                    first_name=data['customer'].get('first_name', ''),
                    middle_name=data['customer'].get('middle_name', ''),
                    last_name=data['customer'].get('last_name', ''),
                    phone=data['customer'].get('phone', ''),
                    address=data['customer'].get('address', ''),
                    city=data['customer'].get('city', ''),
                    district=data['customer'].get('district', ''),
                    state=data['customer'].get('state', ''),
                    pincode=data['customer'].get('pincode', ''),
                    sub_district=data['customer'].get('sub_district', ''),
                    gst_number=data['customer'].get('gst_number', ''),
                    drug_license_number=data['customer'].get('drug_license_number', ''),
                    pan_number=data['customer'].get('pan_number', ''),
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
        mobile_number = request.GET.get('mobile_number', '')
        date_str = request.GET.get('date', '')
        payment_status = request.GET.get('payment_status', '')

        # Start with all bills, ordered by newest first
        bills = Bill.objects.all().order_by('-date')

        # Apply filters
        if bill_number:
            bills = bills.filter(bill_number__icontains=bill_number)
            
        if customer_name:
            bills = bills.filter(
                Q(customer__first_name__icontains=customer_name) |
                Q(customer__middle_name__icontains=customer_name) |
                Q(customer__last_name__icontains=customer_name)
            )
            
        if mobile_number:
            bills = bills.filter(customer__phone__icontains=mobile_number)
            
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

        # Calculate total remaining collection before limiting results
        total_remaining = bills.aggregate(total=Sum('remaining_amount'))['total'] or Decimal('0')

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
            'total_remaining': str(total_remaining),
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
            'customer_city': bill.customer.city if bill.customer else '',
            'customer_pincode': bill.customer.pincode if bill.customer else '',
            'customer_sub_district': bill.customer.sub_district if bill.customer else '',
            'customer_gst_number': bill.customer.gst_number if bill.customer else '',
            'customer_drug_license_number': bill.customer.drug_license_number if bill.customer else '',
            'customer_pan_number': bill.customer.pan_number if bill.customer else '',
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
                'pan_number': business_info.pan_number,
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
            business_info.pan_number = request.POST.get('pan_number', '')
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
    
    
    return render(request, 'genrate_bill/business_settings.html', {
        'business_info': business_info,
    })

@require_http_methods(["GET"])
def create_backup(request):
    """Generate and download a full system backup"""
    try:
        # Create a zip file in memory
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            # 1. Dump Database Data
            # Order matters for dependencies: Parents first
            models_to_backup = [
                BusinessInformation, Category, Unit, Product, 
                Customer, Bill, BillItem
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
            # 1. Restore Data (Clean Restore)
            if 'data.json' in zip_ref.namelist():
                data_content = zip_ref.read('data.json').decode('utf-8')
                objects = serializers.deserialize('json', data_content)
                
                with transaction.atomic():
                    # A. Delete existing data in Reverse Dependency Order (Children First)
                    # This ensures a clean slate and avoids foreign key conflicts during deletion
                    models_to_clear = [
                        BillItem, Bill, Customer, Product, 
                        Category, Unit, BusinessInformation
                    ]
                    for model in models_to_clear:
                        model.objects.all().delete()
                    
                    # B. Save new data
                    # The backup is already ordered Parent -> Child, so saving in order is safe
                    for obj in objects:
                        obj.save()
                        
            # 2. Restore Media (After data is safe)
            for file in zip_ref.namelist():
                if file.startswith('media/'):
                    # Extract to media root
                    target_path = os.path.join(settings.MEDIA_ROOT, os.path.relpath(file, 'media'))
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, 'wb') as f:
                        f.write(zip_ref.read(file))
                        
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
        
        if payment_date:
            parsed_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
        else:
            parsed_date = timezone.now().date()
            
        with transaction.atomic():
            if new_status in ['Paid', 'Partially Paid']:
                # Amount being paid right now - handle empty or null safely
                raw_amount = data.get('paid_amount')
                if raw_amount is None or str(raw_amount).strip() == '':
                    current_payment_amount = Decimal('0')
                else:
                    try:
                        current_payment_amount = Decimal(str(raw_amount))
                    except (TypeError, ValueError, decimal.DecimalException):
                        current_payment_amount = Decimal('0')
                
                if current_payment_amount > 0 or new_status == 'Paid':
                    # If status is just updated to Paid without specific partial, it pays the remainder
                    if new_status == 'Paid' and current_payment_amount == 0:
                        current_payment_amount = bill.remaining_amount
                        
                    # Cap payment so we don't overpay
                    if current_payment_amount > bill.remaining_amount:
                        current_payment_amount = bill.remaining_amount
                    
                    # Create History Record
                    if current_payment_amount > 0:
                        PaymentHistory.objects.create(
                            bill=bill,
                            payment_date=parsed_date,
                            amount_paid=current_payment_amount,
                            payment_mode=payment_mode,
                            remarks=f"Payment updated to {new_status}"
                        )
                        
                    # Update Bill Totals
                    bill.paid_amount += current_payment_amount
                    bill.remaining_amount = bill.final_amount - bill.paid_amount
                    bill.payment_mode = payment_mode
                    bill.payment_date = parsed_date
                    
                    # Auto adjust status based on remaining amount
                    if bill.remaining_amount <= 0:
                        bill.payment_status = 'Paid'
                        bill.paid_amount = bill.final_amount
                        bill.remaining_amount = Decimal('0')
                    elif bill.paid_amount > 0:
                        bill.payment_status = 'Partially Paid'
                    else:
                        bill.payment_status = 'Pending'
                        
            else:
                # Pending Reset
                bill.payment_status = 'Pending'
                bill.payment_mode = None
                bill.payment_date = None
                bill.paid_amount = Decimal('0')
                bill.remaining_amount = bill.final_amount
                # Optionally delete history on reset? We shouldn't delete audit trail, but bill is pending now.
                # PaymentHistory.objects.filter(bill=bill).delete()  # Decided to keep history
                
            bill.save()
            
        return JsonResponse({'success': True, 'message': 'Payment status updated successfully'})
        
    except Bill.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bill not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["GET"])
def get_payment_history(request, bill_id):
    try:
        bill = Bill.objects.get(bill_number=bill_id)
        # Fetch chronologically to calculate running totals
        history = PaymentHistory.objects.filter(bill_id=bill_id).order_by('created_at')
        
        history_data = []
        current_remaining = bill.final_amount
        
        for h in history:
            paid = h.amount_paid
            current_remaining -= paid
            
            history_data.append({
                'id': h.id,
                'payment_date': h.payment_date.strftime('%Y-%m-%d'),
                'amount_paid': str(paid),
                'payment_mode': h.payment_mode,
                'remarks': h.remarks,
                'created_at': h.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'total_amount': str(bill.final_amount),
                'remaining_amount': str(current_remaining)
            })
            
        # Reverse the list so the newest payments appear first
        history_data.reverse()
        
        return JsonResponse({'success': True, 'history': history_data})
    except Bill.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bill not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def customers_page(request):
    """Render the customers management page"""
    business_info = BusinessInformation.get_business_info()
    customers = Customer.objects.all().order_by('-id')
    return render(request, 'genrate_bill/customers.html', {
        'business_info': business_info,
        'customers': customers
    })

@require_http_methods(["POST"])
def save_customer(request):
    """Create or Update a customer"""
    try:
        data = json.loads(request.body)
        customer_id = data.get('id')
        
        defaults = {
            'first_name': data.get('first_name', ''),
            'middle_name': data.get('middle_name', ''),
            'last_name': data.get('last_name', ''),
            'phone': data.get('phone', ''),
            'address': data.get('address', ''),
            'city': data.get('city', ''),
            'district': data.get('district', ''),
            'state': data.get('state', ''),
            'pincode': data.get('pincode', ''),
            'sub_district': data.get('sub_district', ''),
            'gst_number': data.get('gst_number', ''),
            'drug_license_number': data.get('drug_license_number', ''),
            'pan_number': data.get('pan_number', ''),
            'extra_note': data.get('extra_note', '')
        }

        if customer_id:
            customer = Customer.objects.get(id=customer_id)
            for key, value in defaults.items():
                setattr(customer, key, value)
            customer.save()
            message = "Customer updated successfully"
        else:
            # Check for duplicates by phone if phone is provided
            if defaults['phone'] and Customer.objects.filter(phone=defaults['phone']).exists():
                return JsonResponse({'success': False, 'error': 'Customer with this phone number already exists'}, status=400)
                
            customer = Customer.objects.create(**defaults)
            message = "Customer added successfully"
            
        return JsonResponse({
            'success': True, 
            'message': message,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'first_name': customer.first_name,
                'middle_name': customer.middle_name,
                'last_name': customer.last_name,
                'phone': customer.phone,
                'address': customer.address,
                'city': customer.city,
                'state': customer.state,
                'pincode': customer.pincode,
                'gst_number': customer.gst_number
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["POST"])
def delete_customer(request, customer_id):
    try:
        Customer.objects.get(id=customer_id).delete()
        return JsonResponse({'success': True, 'message': 'Customer deleted successfully'})
    except Customer.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Customer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def get_customer_by_phone(request, phone):
    """Fetch customer details by phone number"""
    try:
        customer = Customer.objects.filter(phone=phone).first()
        if customer:
            data = {
                'id': customer.id,
                'name': customer.name,
                'first_name': customer.first_name,
                'middle_name': customer.middle_name,
                'last_name': customer.last_name,
                'phone': customer.phone,
                'address': customer.address,
                'city': customer.city,
                'district': customer.district,
                'sub_district': customer.sub_district,
                'state': customer.state,
                'pincode': customer.pincode,
                'gst_number': customer.gst_number,
                'drug_license_number': customer.drug_license_number,
                'pan_number': customer.pan_number
            }
            return JsonResponse({'success': True, 'customer': data})
        else:
            return JsonResponse({'success': False, 'error': 'Customer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def tax_center_page(request):
    """Render Tax Center Page"""
    business_info = BusinessInformation.get_business_info()
    return render(request, 'genrate_bill/tax_center.html', {
        'business_info': business_info
    })

def tax_center_search_bills(request):
    """Search bills for Tax Center without changing the History & Search endpoint."""
    try:
        bill_number = request.GET.get('bill_number', '')
        customer_name = request.GET.get('customer_name', '')
        mobile_number = request.GET.get('mobile_number', '')
        start_date_str = request.GET.get('start_date', '')
        end_date_str = request.GET.get('end_date', '')

        bills = Bill.objects.all().order_by('date', 'bill_number')

        if bill_number:
            bills = bills.filter(bill_number__icontains=bill_number)

        if customer_name:
            bills = bills.filter(
                Q(customer__first_name__icontains=customer_name) |
                Q(customer__middle_name__icontains=customer_name) |
                Q(customer__last_name__icontains=customer_name)
            )

        if mobile_number:
            bills = bills.filter(customer__phone__icontains=mobile_number)

        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            start_datetime = timezone.make_aware(datetime.combine(start_date, time.min))
            bills = bills.filter(date__gte=start_datetime)

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            end_datetime = timezone.make_aware(datetime.combine(end_date, time.max))
            bills = bills.filter(date__lte=end_datetime)

        total_remaining = bills.aggregate(total=Sum('remaining_amount'))['total'] or Decimal('0')

        bills_data = []
        for bill in bills:
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

        return JsonResponse({
            'success': True,
            'bills': bills_data,
            'total_remaining': str(total_remaining),
            'filters': {
                'start_date': start_date_str,
                'end_date': end_date_str,
                'bill_number': bill_number,
                'customer_name': customer_name
            }
        })
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid date format'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def get_tax_stats(request):
    """API to return tax stats for a specific month"""
    try:
        month_str = request.GET.get('month', timezone.now().strftime('%Y-%m')) # YYYY-MM
        year, month = map(int, month_str.split('-'))
        
        # Filter bills
        bills = Bill.objects.filter(date__year=year, date__month=month)
        
        # Initialize stats
        stats = {
            'total_count': 0, 'total_taxable': 0.0, 'total_igst': 0.0, 'total_cgst': 0.0, 'total_sgst': 0.0,
            'b2b_count': 0, 'b2b_taxable': 0.0, 'b2b_igst': 0.0, 'b2b_cgst': 0.0, 'b2b_sgst': 0.0,
            'b2c_count': 0, 'b2c_taxable': 0.0, 'b2c_igst': 0.0, 'b2c_cgst': 0.0, 'b2c_sgst': 0.0,
        }
        
        for bill in bills:
            is_b2b = bool(bill.customer.gst_number)
            
            # Get items totals
            items = BillItem.objects.filter(bill=bill)
            
            bill_taxable = 0
            bill_igst = 0
            bill_cgst = 0
            bill_sgst = 0
            
            for item in items:
                # Assuming tax amounts are stored correctly in item.total_price vs item.price*qty
                # Based on models: total_price = (qty*price) + taxes
                # Taxable = qty * price
                taxable = float(item.quantity) * float(item.price)
                bill_taxable += taxable
                bill_igst += float(item.igst_amount)
                bill_cgst += float(item.cgst_amount)
                bill_sgst += float(item.sgst_amount)

            # Apply Bill Discount Ratio to Taxable? 
            # The discount is on the bill total usually. 
            # For accurate GST, discount implies reduced taxable value.
            # If bill.discount > 0, we should reduce taxable proportionaly or just subtract.
            # Simplified: Subtract bill discount from total taxable.
            if bill.discount:
                bill_taxable -= float(bill.discount)

            stats['total_count'] += 1
            stats['total_taxable'] += bill_taxable
            stats['total_igst'] += bill_igst
            stats['total_cgst'] += bill_cgst
            stats['total_sgst'] += bill_sgst
            
            if is_b2b:
                stats['b2b_count'] += 1
                stats['b2b_taxable'] += bill_taxable
                stats['b2b_igst'] += bill_igst
                stats['b2b_cgst'] += bill_cgst
                stats['b2b_sgst'] += bill_sgst
            else:
                stats['b2c_count'] += 1
                stats['b2c_taxable'] += bill_taxable
                stats['b2c_igst'] += bill_igst
                stats['b2c_cgst'] += bill_cgst
                stats['b2c_sgst'] += bill_sgst
                
        return JsonResponse({'success': True, 'stats': stats})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET"])
def download_tax_report(request):
    """Generate and download GST zip report"""
    try:
        month_str = request.GET.get('month', timezone.now().strftime('%Y-%m'))
        year, month = map(int, month_str.split('-'))
        notes = request.GET.get('notes', '')
        
        bills = Bill.objects.filter(date__year=year, date__month=month)
        
        # Buffers for CSVs
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            # Helper to write CSV
            def add_csv(filename, headers, rows):
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)
                writer.writerow(headers)
                writer.writerows(rows)
                zip_file.writestr(filename, csv_buffer.getvalue())

            # 1. B2B CSV
            b2b_headers = ['Date', 'Invoice No', 'Customer Name', 'GSTIN', 'State', 'Taxable Value', 'IGST', 'CGST', 'SGST', 'Total', 'Notes']
            b2b_rows = []
            
            # 2. B2C CSV
            b2c_headers = ['Date', 'Invoice No', 'Customer Name', 'State', 'Taxable Value', 'IGST', 'CGST', 'SGST', 'Total']
            b2c_rows = []
            
            # 3. HSN Summary Data
            hsn_map = {} # {hsn: {qty, taxable, tax_amount}}
            
            for bill in bills:
                is_b2b = bool(bill.customer.gst_number)
                bill_date = bill.date.strftime('%Y-%m-%d')
                
                # Fetch items
                items = BillItem.objects.filter(bill=bill)
                
                bill_taxable = 0
                bill_igst = 0
                bill_cgst = 0
                bill_sgst = 0
                
                for item in items:
                    qty = float(item.quantity)
                    taxable = qty * float(item.price)
                    igst = float(item.igst_amount)
                    cgst = float(item.cgst_amount)
                    sgst = float(item.sgst_amount)
                    
                    bill_taxable += taxable
                    bill_igst += igst
                    bill_cgst += cgst
                    bill_sgst += sgst
                    
                    # HSN Aggr
                    hsn = item.hsn_number or 'General'
                    if hsn not in hsn_map: hsn_map[hsn] = {'qty': 0, 'val': 0, 'tax': 0}
                    hsn_map[hsn]['qty'] += qty
                    hsn_map[hsn]['val'] += taxable
                    hsn_map[hsn]['tax'] += (igst + cgst + sgst)
                
                # Discount Adj
                if bill.discount:
                    bill_taxable -= float(bill.discount)
                
                row = [
                    bill_date,
                    bill.bill_number,
                    bill.customer.name,
                    bill.customer.gst_number if is_b2b else '',
                    bill.place_of_supply or bill.customer.state or '',
                    round(bill_taxable, 2),
                    round(bill_igst, 2),
                    round(bill_cgst, 2),
                    round(bill_sgst, 2),
                    float(bill.final_amount),
                    ''
                ]
                
                if is_b2b:
                    row.insert(3, bill.customer.gst_number) 
                    b2b_rows.append([
                        bill_date, bill.bill_number, bill.customer.name, bill.customer.gst_number,
                        bill.place_of_supply or bill.customer.state or '',
                        round(bill_taxable, 2), round(bill_igst, 2), round(bill_cgst, 2), round(bill_sgst, 2),
                        float(bill.final_amount), ''
                    ])
                else:
                     b2c_rows.append([
                        bill_date, bill.bill_number, bill.customer.name,
                        bill.place_of_supply or bill.customer.state or '',
                        round(bill_taxable, 2), round(bill_igst, 2), round(bill_cgst, 2), round(bill_sgst, 2),
                        float(bill.final_amount)
                    ])

            add_csv('B2B_Sales.csv', b2b_headers, b2b_rows)
            add_csv('B2C_Sales.csv', b2c_headers, b2c_rows)
            
            # 4. HSN CSV
            hsn_rows = [[h, round(d['qty'], 2), round(d['val'], 2), round(d['tax'], 2)] for h, d in hsn_map.items()]
            add_csv('HSN_Summary.csv', ['HSN Code', 'Total Quantity', 'Taxable Value', 'Total Tax Amount'], hsn_rows)
            
            # 5. Notes
            if notes:
                zip_file.writestr('Notes_To_CA.txt', f"Notes for period {month_str}:\n\n{notes}")
                
        buffer.seek(0)
        filename = f"GST_Return_Data_{month_str}.zip"
        response = HttpResponse(buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def ca_pdf_report(request):
    """View to render a printable CA report for a date range"""
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if not start_date_str or not end_date_str:
        # Default to current month if not provided
        today = timezone.now().date()
        start_date = today.replace(day=1)
        end_date = today
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
    
    # Adjust end date to include full day
    start_datetime = datetime.combine(start_date, time.min)
    end_datetime = datetime.combine(end_date, time.max)
    
    bills = Bill.objects.filter(date__range=(start_datetime, end_datetime)).order_by('date')
    business_info = BusinessInformation.get_business_info()
    
    # Calculate totals
    totals = {
        'taxable': 0,
        'cgst': 0,
        'sgst': 0,
        'igst': 0,
        'total': 0
    }
    
    bill_data = []
    for bill in bills:
        items = BillItem.objects.filter(bill=bill)
        bill_taxable = 0
        bill_cgst = 0
        bill_sgst = 0
        bill_igst = 0
        
        for item in items:
            taxable = float(item.quantity) * float(item.price)
            bill_taxable += taxable
            bill_cgst += float(item.cgst_amount)
            bill_sgst += float(item.sgst_amount)
            bill_igst += float(item.igst_amount)
        
        if bill.discount:
            bill_taxable -= float(bill.discount)
            
        totals['taxable'] += bill_taxable
        totals['cgst'] += bill_cgst
        totals['sgst'] += bill_sgst
        totals['igst'] += bill_igst
        totals['total'] += float(bill.final_amount)
        
        bill_data.append({
            'bill_number': bill.bill_number,
            'date': bill.date,
            'customer_name': bill.customer.name,
            'gst_number': bill.customer.gst_number,
            'taxable': bill_taxable,
            'cgst': bill_cgst,
            'sgst': bill_sgst,
            'igst': bill_igst,
            'total': float(bill.final_amount)
        })
    
    return render(request, 'genrate_bill/ca_pdf_report.html', {
        'business_info': business_info,
        'bills': bill_data,
        'totals': totals,
        'start_date': start_date,
        'end_date': end_date
    })

def render_to_pdf(template_src, context_dict={}):
    """Utility to render HTML to PDF bytes"""
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None

@require_http_methods(["GET"])
def download_bills_zip(request):
    """View to download all bills in a date range as individual PDFs in a ZIP"""
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if not start_date_str or not end_date_str:
        return JsonResponse({'success': False, 'error': 'Dates are required'}, status=400)
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid date format'}, status=400)

    start_datetime = datetime.combine(start_date, time.min)
    end_datetime = datetime.combine(end_date, time.max)
    
    bills = Bill.objects.filter(date__range=(start_datetime, end_datetime)).order_by('bill_number')
    business_info = BusinessInformation.get_business_info()
    
    if not bills.exists():
        return JsonResponse({'success': False, 'error': 'No bills found in this range'}, status=404)
    
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for bill in bills:
            items = BillItem.objects.filter(bill=bill)
            
            # Calculate tax groups and totals for the template
            tax_groups = {}
            total_cgst = 0
            total_sgst = 0
            total_igst = 0
            total_basic = 0
            total_quantity = 0
            
            for item in items:
                label = "GST 0%"
                if item.igst_rate > 0:
                    label = f"IGST {float(item.igst_rate)}%"
                elif item.cgst_rate > 0 or item.sgst_rate > 0:
                    label = f"GST {float(item.cgst_rate + item.sgst_rate)}%"
                
                if label not in tax_groups:
                    tax_groups[label] = {'basic': 0, 'cgst': 0, 'sgst': 0, 'igst': 0, 'total_tax': 0}
                
                taxable = float(item.quantity * item.price)
                gst_amount = float(item.cgst_amount + item.sgst_amount + item.igst_amount)
                item.taxable_amount = taxable
                item.gst_amount = gst_amount
                tax_groups[label]['basic'] += taxable
                tax_groups[label]['cgst'] += float(item.cgst_amount)
                tax_groups[label]['sgst'] += float(item.sgst_amount)
                tax_groups[label]['igst'] += float(item.igst_amount)
                tax_groups[label]['total_tax'] += gst_amount
                
                total_cgst += float(item.cgst_amount)
                total_sgst += float(item.sgst_amount)
                total_igst += float(item.igst_amount)
                total_basic += taxable
                total_quantity += float(item.quantity)
            
            # Implementation for Amount in Words (Indian Numbering System)
            def num_to_words(num):
                try:
                    num = int(round(float(num)))
                    if num == 0: return "Zero Rupees Only"
                    
                    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
                    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
                    
                    def convert(n):
                        if n == 0:
                            return ""
                        if n < 20:
                            return units[n]
                        if n < 100:
                            return tens[n // 10] + ((" " + units[n % 10]) if n % 10 else "")
                        if n < 1000:
                            return units[n // 100] + " Hundred" + ((" and " + convert(n % 100)) if n % 100 else "")
                        if n < 100000:
                            return convert(n // 1000) + " Thousand" + ((" " + convert(n % 1000)) if n % 1000 else "")
                        if n < 10000000:
                            return convert(n // 100000) + " Lakh" + ((" " + convert(n % 100000)) if n % 100000 else "")
                        return convert(n // 10000000) + " Crore" + ((" " + convert(n % 10000000)) if n % 10000000 else "")

                    return convert(num) + " Rupees Only"
                except:
                    return "Zero Rupees Only"
                
            terms = []
            for term in (business_info.terms_and_conditions or '').replace('\r', '').split('\n'):
                clean_term = term.strip()
                if clean_term:
                    clean_term = clean_term.lstrip('0123456789. )')
                    terms.append(clean_term)
            if not terms:
                terms = [
                    'Goods once sold will not be taken back or exchanged.',
                    'All disputes are subject to jurisdiction only.'
                ]

            context = {
                'bill': bill,
                'items': items,
                'business_info': business_info,
                'tax_groups': tax_groups,
                'terms': terms,
                'totals': {
                    'cgst': total_cgst,
                    'sgst': total_sgst,
                    'igst': total_igst,
                    'basic': total_basic,
                    'taxable': total_basic - float(bill.discount or 0),
                    'tax_total': total_cgst + total_sgst + total_igst,
                    'grand_total': float(bill.final_amount),
                    'quantity': total_quantity,
                    'has_igst': total_igst > 0,
                    'words': num_to_words(float(bill.final_amount))
                }
            }
            pdf_content = render_to_pdf('genrate_bill/bill_pdf_template.html', context)
            if pdf_content:
                zip_file.writestr(f"Bill_{bill.bill_number}.pdf", pdf_content)
    
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="Bills_{start_date_str}_to_{end_date_str}.zip"'
    return response

def sales_analytics_page(request):
    """Render Analytics Page"""
    business_info = BusinessInformation.get_business_info()
    return render(request, 'genrate_bill/analytics.html', {
        'business_info': business_info
    })

def get_analytics_data(request):
    """JSON API for analytics"""
    try:
        start_date_str = request.GET.get('start')
        end_date_str = request.GET.get('end')
        group_by = request.GET.get('group', 'day') # day/month
        
        if not start_date_str or not end_date_str:
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
        # Adjust end date to include full day
        end_datetime = datetime.combine(end_date, time.max)
        start_datetime = datetime.combine(start_date, time.min)
        
        # 1. KPIs
        bills = Bill.objects.filter(date__range=(start_datetime, end_datetime))
        kpi_revenue = bills.aggregate(Sum('final_amount'))['final_amount__sum'] or 0
        kpi_orders = bills.count()
        # Avg Order Value
        kpi_aov = kpi_revenue / kpi_orders if kpi_orders else 0
        
        # Products sold count (sum quantity from BillItem)
        bill_ids = bills.values_list('bill_number', flat=True)
        items = BillItem.objects.filter(bill__in=bill_ids)
        kpi_products_sold = items.aggregate(Sum('quantity'))['quantity__sum'] or 0
        
        # 2. Charts Data
        
        # A. Trend (Revenue over time)
        trend_map = defaultdict(float)
        for bill in bills:
            if group_by == 'month':
                key = bill.date.strftime('%Y-%m')
            else:
                key = bill.date.strftime('%Y-%m-%d')
            trend_map[key] += float(bill.final_amount)
            
        # Fill gaps if 'day' (optional, skipping for simplicity or just sort keys)
        trend_labels = sorted(trend_map.keys())
        trend_values = [trend_map[k] for k in trend_labels]
        
        # B. Payment Modes - Only for Paid/Partially Paid bills?
        # Let's count all instances, filtering for those with payment mode
        modes = bills.exclude(payment_mode__isnull=True).exclude(payment_mode='').values('payment_mode').annotate(total=Count('payment_mode'))
        payment_labels = [m['payment_mode'] for m in modes]
        payment_values = [m['total'] for m in modes]
        
        # C. Top Products (by Revenue) & D. Categories
        # We need items for this
        # Group items by product name
        product_stats = items.values('product__name', 'product__category__name').annotate(revenue=Sum('total_price')).order_by('-revenue')[:5]
        
        prod_labels = [p['product__name'] for p in product_stats]
        prod_values = [float(p['revenue']) for p in product_stats]
        
        # Categories aggregation from the same items query? 
        # Easier to do separate aggregation
        cat_stats = items.values('product__category__name').annotate(revenue=Sum('total_price')).order_by('-revenue')
        
        cat_labels = [c['product__category__name'] or 'Uncategorized' for c in cat_stats]
        cat_values = [float(c['revenue']) for c in cat_stats]
        
        return JsonResponse({
            'success': True,
            'kpis': {
                'revenue': kpi_revenue,
                'orders': kpi_orders,
                'aov': kpi_aov,
                'products_sold': kpi_products_sold
            },
            'charts': {
                'trend': { 'labels': trend_labels, 'values': trend_values },
                'payment': { 'labels': payment_labels, 'values': payment_values },
                'products': { 'labels': prod_labels, 'values': prod_values },
                'categories': { 'labels': cat_labels, 'values': cat_values }
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
