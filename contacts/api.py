from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from contacts.models import Organisation, Contact


# Serializers define the API representation.
class ContactSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Contact
        fields = ['first_name', 'last_name']


class OrganisationSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Organisation
        fields = ['name', 'website']


# ViewSets define the view behavior.
class OrganisationViewSet(ReadOnlyModelViewSet):
    queryset = Organisation.objects.filter(listed=True)
    serializer_class = OrganisationSerializer
    filterset_fields = ['name']
    search_fields = ['name']


class ContactViewSet(ReadOnlyModelViewSet):
    queryset = Contact.objects.filter(listed=True)
    serializer_class = ContactSerializer
    filterset_fields = ['first_name', 'last_name']
    search_fields = ['fist_name', 'last_name']
