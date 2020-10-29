from django.contrib import admin
from .models import Account, Customer, VPS, SMSCustomer, CorrlinksToSMS, SMSToCorrlinks, APIKey, Image, \
    SystemToCorrlinks

import admin_thumbnails

@admin_thumbnails.thumbnail('image')
class ImageAdmin(admin.TabularInline):
    model = Image


# Register your models here.
class AccountAdmin(admin.TabularInline):
    # list_display = ('email', 'status', 'VPS')
    model = Account


class AccountAdmin2(admin.ModelAdmin):
    list_display = ('email', 'status', 'message_24h', 'active', 'blocked', 'VPS')
    list_filter = ('email', 'status', 'VPS')

    def message_24h(self, obj):
        return obj.sms_to_corrlinks_count()

    def active(self, obj):
        return obj.get_active_customers()

    def blocked(self, obj):
        return obj.get_blocked_customers()


class VPSAdmin(admin.ModelAdmin):
    list_display = ('VPS_Name', 'notes', 'active', 'disabled')
    inlines = [AccountAdmin]

    def active(self, obj):
        return obj.get_active_count()

    def disabled(self, obj):
        return obj.get_disabled_count()


class CorrlinksToSMSAdmin(admin.ModelAdmin):
    list_display = ('status', 'createdAt', '_from','to')
    list_filter = ('status','createdAt')
    search_fields = ('_from__corrlinks_ID', '_from__name','to__name')


class SMSToCorrlinksAdmin(admin.ModelAdmin):
    list_display = ('status', 'createdAt', '_from', 'Images_Count')
    list_filter = ('status','createdAt')
    search_fields = ('_from__corrlinks_Customer__corrlinks_ID', '_from__corrlinks_Customer__name', '_from__name')

    inlines = [ImageAdmin]

    def Images_Count(self, obj):
        return obj.get_image_count()


class SMSCustomerAdmin(admin.TabularInline):
    # list_display = ('co rrlinks_Customer', 'name', 'phone_Number')
    model = SMSCustomer


class CustomerAndSmsCustomer(Customer):
    class Meta:
        proxy = True
        verbose_name = "Customer"


class CustomerAndSmsCustomerAdmin(admin.ModelAdmin):
    list_display = (
        'corrlinks_ID', 'name', 'due_Date', 'status', 'balance','image_count', 'phone_Number', 'corrlinks_Account')
    search_fields = ('corrlinks_ID', 'name','phone_Number')
    inlines = [SMSCustomerAdmin, ]
    list_filter = ('due_Date', 'status', 'corrlinks_Account')


class CustomerAndImagesAdmin(admin.ModelAdmin):
    list_display = (
        'corrlinks_ID', 'name', 'due_Date', 'status', 'Images_Count', 'balance', 'phone_Number', 'corrlinks_Account')
    search_fields = ('corrlinks_ID', 'name')
    inlines = [ImageAdmin, ]
    list_filter = ('due_Date', 'status', 'corrlinks_Account')

    def Images_Count(self, obj):
        return obj.get_image_count_customer()


class CustomerAndImage(Customer):
    class Meta:
        proxy = True
        verbose_name = "Customer's Picture"

class DummyCustomerAdmin(admin.ModelAdmin):
    search_fields = ('corrlinks_ID', 'name', 'phone_Number')
    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}



class SystemToCorrlinksAdmin(admin.ModelAdmin):
    list_display = (
        'customer', 'subject', 'body', 'status', 'createdAt'
    )
    search_fields = ('customer', 'subject')
    autocomplete_fields = ['customer', ]


admin.site.register(SystemToCorrlinks, SystemToCorrlinksAdmin)

admin.site.register(Account, AccountAdmin2)
admin.site.register(VPS, VPSAdmin)
admin.site.site_header = 'SMS-ADMIN'
admin.site.register(CustomerAndSmsCustomer, CustomerAndSmsCustomerAdmin)
admin.site.register(Customer, DummyCustomerAdmin)

# admin.site.register(CustomerAndImage, CustomerAndImagesAdmin)

admin.site.register(SMSToCorrlinks, SMSToCorrlinksAdmin)
admin.site.register(CorrlinksToSMS, CorrlinksToSMSAdmin)
admin.site.register(APIKey)
