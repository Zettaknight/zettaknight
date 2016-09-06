from django.contrib.auth.models import User, Group
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

class DatasetSerializer(serializers.Serializer):

    #fields = ('user','dataset','function')
    args = serializers.CharField()
    user = serializers.CharField()
    function = serializers.CharField(allow_none=True)

    def restore_object(self, attrs, instance=None):
        if instance is None:
            instance.user = attrs.get('user', instance.user)
            instance.function = attrs.get('function', instance.function)
            instance.args = attrs.get('args', instance.args)
        return Dataset(**attrs)
