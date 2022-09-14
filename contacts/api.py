from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from contacts.models import Contact, Organisation


# Serializers define the API representation.
class ContactSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Contact
        fields = ["first_name", "last_name"]


class OrganisationSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Organisation
        fields = ["name", "logo", "website"]


# ViewSets define the view behavior.
class DonorOrganisationViewSet(ReadOnlyModelViewSet):
    queryset = Organisation.objects.filter(listed=True, contacts__groups__name__icontains="donor").distinct()
    serializer_class = OrganisationSerializer
    filterset_fields = ["name"]
    search_fields = ["name"]


class PersonalDonorViewSet(ReadOnlyModelViewSet):
    queryset = Contact.objects.filter(listed=True, groups__name__icontains="donor")
    serializer_class = ContactSerializer
    filterset_fields = ["first_name", "last_name"]
    search_fields = ["fist_name", "last_name"]
