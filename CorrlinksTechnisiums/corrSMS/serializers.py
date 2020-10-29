from rest_framework import serializers

from .models import Account, CorrlinksToSMS, SMSToCorrlinks


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'


class CorrlinksToSMSSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorrlinksToSMS
        fields = ('_from', 'to', 'body')


class SMSToCorrlinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSToCorrlinks
        fields = ('id', '_from', 'body')
