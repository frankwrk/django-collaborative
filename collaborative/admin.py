from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin.models import LogEntry
from django.apps import apps
from import_export.resources import modelresource_factory

from django_models_from_csv.admin import AdminAutoRegistration
from django_models_from_csv.models import DynamicModel


UserAdmin.list_display = ("username","email","first_name","last_name")
# UserAdmin.list_editable = ("first_name", "last_name")

UserAdmin.add_fieldsets = ((None, {
    'fields': ('username', 'email', 'password1', 'password2'),
    'classes': ('wide',)
}),)


def make_getter(rel_name, attr_name, getter_name):
    """
    Build a reverse lookup getter, to be attached to the custom
    dynamic lookup admin class.
    """
    def getter(self):
        if hasattr(self, rel_name):
            rel = getattr(self, rel_name).first()
            # try to lookup choices for field
            choices = getattr(
                rel, "%s_CHOICES" % attr_name.upper(), []
            )
            value = getattr(rel, attr_name)
            for pk, txt in choices:
                if pk == value:
                    return txt
            # no choice found, return field value
            return value
    # the header in django admin is named after the function name. if
    # this line is removed, the header will be "GETTER" for all derived
    # reverse lookup columns
    getter.__name__ = getter_name
    return getter


class ReverseFKAdmin(admin.ModelAdmin):
    def __init__(self, *args, **kwargs):
        """
        Build relations lookup methods, like metadata__status, but
        for the reverse foreignkey direction.
        """
        super().__init__(*args, **kwargs)
        Model, site = args
        if "DynamicModel" == Model._meta.object_name:
            return

        # setup reverse related attr getters so we can do things like
        # metadata__status in the reverse direction
        for rel in Model._meta.related_objects:
            rel_name = rel.get_accessor_name() # "metadata", etc, related_name

            rel_model = rel.related_model
            if not rel_model:
                continue

            for rel_field in rel_model._meta.get_fields():
                # remove auto fields and other fields of that nature. we
                # only want the directly acessible fields of this method
                if rel_field.is_relation: continue
                if not hasattr(rel_field, "auto_created"): continue
                if rel_field.auto_created: continue

                # build a getter for this relation attribute
                attr_name = rel_field.name
                getter_name = "%s_%s" % (rel_name, attr_name)
                getter = make_getter(rel_name, attr_name, getter_name)
                setattr(Model, getter_name, getter)


class AdminMetaAutoRegistration(AdminAutoRegistration):
    def should_register_admin(self, Model):
        name = Model._meta.object_name
        if name.endswith("Metadata"):
            return False
        return super(
            AdminMetaAutoRegistration, self
        ).should_register_admin(Model)

    def create_admin(self, Model):
        name = Model._meta.object_name
        if "Metadata" in name or name == "DynamicModel":
            return super().create_admin(Model)

        meta = []
        # find the Metadata model corresponding to the
        # csv-backed model we're creating admin for.
        # this will end up as an inline admin
        for MetaModel in self.all_models:
            meta_name = MetaModel._meta.object_name
            # all our additonal related models are in this pattern:
            # [ModelName][Contact|*]Metadata
            if not meta_name.startswith(name) or \
               not meta_name.endswith("Metadata"):
                continue
            MetaModelInline = type(
                "%sInlineAdmin" % meta_name,
                (admin.StackedInline,), {
                    "model": MetaModel,
                    "extra": 0,
                })
            meta.append(MetaModelInline)

        # get searchable and filterable (from column attributes)
        model_desc = DynamicModel.objects.get(name=name)
        searchable = [c["name"] for c in model_desc.columns if c.get("searchable")]
        filterable = [c["name"] for c in model_desc.columns if c.get("filterable")]

        # Build our CSV-backed admin, attaching inline meta model
        ro_fields = self.get_readonly_fields(Model)
        fields = self.get_fields(Model)
        associated_fields = []
        if name != "DynamicModel":
            associated_fields.append("metadata_status")
            associated_fields.append("metadata_partner")
        list_display = associated_fields + fields[:5]
        return type("%sAdmin" % name, (ReverseFKAdmin,), {
            "inlines": meta,
            "readonly_fields": fields,
            "list_display": list_display,
            "search_fields": searchable,
            "list_filter": filterable,
        })


AdminMetaAutoRegistration(include="django_models_from_csv.models").register()
admin.site.register(LogEntry)

admin.site.site_header = "Collaborate"
admin.site.index_title = "Welcome"
admin.site.site_title = "Collaborate"

