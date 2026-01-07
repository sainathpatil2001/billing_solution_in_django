from django import forms
from .models import Product, Category, Unit

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'unit', 'dealer_price', 'selling_price', 'mrp',
                 'quantity', 'gst_rate', 'igst', 'cgst', 'sgst', 'hsn_number', 
                 'minimum_stock', 'batch_number', 'mfg_date', 'expiry_date', 'show_product']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].widget.attrs.update({'class': 'form-select'})
        self.fields['unit'].widget.attrs.update({'class': 'form-select'})
        self.fields['minimum_stock'].widget.attrs.update({
            'step': '0.001',
            'min': '0'
        })
        self.fields['quantity'].widget.attrs.update({
            'step': '0.001',
            'min': '0'
        })
        self.fields['gst_rate'].widget.attrs.update({
            'step': '0.01',
            'min': '0'
        })
        self.fields['mrp'].widget.attrs.update({
            'step': '0.01',
            'min': '0'
        })
        self.fields['gst_rate'].widget.attrs.update({
            'step': '0.01',
            'min': '0'
        })
        for field in ['igst', 'cgst', 'sgst']:
            self.fields[field].widget.attrs.update({
                'step': '0.01',
                'min': '0'
            })
        self.fields['show_product'].required = False
        self.fields['category'].required = False
        self.fields['unit'].required = False
    
    mfg_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'month'}),
        input_formats=['%Y-%m', '%Y-%m-%d'],
        required=False
    )
    expiry_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'month'}),
        input_formats=['%Y-%m', '%Y-%m-%d'],
        required=False
    )


class UpdateProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'unit', 'dealer_price', 'selling_price', 'mrp',
                 'quantity', 'gst_rate', 'igst', 'cgst', 'sgst', 'hsn_number',
                 'minimum_stock', 'batch_number', 'mfg_date', 'expiry_date', 'show_product']
        
    mfg_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'month'}),
        input_formats=['%Y-%m', '%Y-%m-%d'],
        required=False
    )
    expiry_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'month'}),
        input_formats=['%Y-%m', '%Y-%m-%d'],
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].widget.attrs.update({'class': 'form-select'})
        self.fields['unit'].widget.attrs.update({'class': 'form-select'})
        self.fields['minimum_stock'].widget.attrs.update({
            'step': '0.001',
            'min': '0'
        })
        self.fields['quantity'].widget.attrs.update({
            'step': '0.001',
            'min': '0'
        })
        self.fields['gst_rate'].widget.attrs.update({
            'step': '0.01',
            'min': '0'
        })
        self.fields['mrp'].widget.attrs.update({
            'step': '0.01',
            'min': '0'
        })
        self.fields['gst_rate'].widget.attrs.update({
            'step': '0.01',
            'min': '0'
        })
        for field in ['igst', 'cgst', 'sgst']:
            self.fields[field].widget.attrs.update({
                'step': '0.01',
                'min': '0'
            })
        self.fields['mfg_date'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['expiry_date'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['show_product'].required = False
        self.fields['category'].required = False
        self.fields['unit'].required = False

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'is_food_item']

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'symbol']
