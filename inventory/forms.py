from django import forms
from .models import Product, Category, Unit

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'unit', 'dealer_price', 'selling_price', 
                 'quantity', 'minimum_stock', 'show_product']
        
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

class UpdateProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'unit', 'dealer_price', 'selling_price', 
                 'quantity', 'minimum_stock', 'show_product']
        
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

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'is_food_item']

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'symbol']
