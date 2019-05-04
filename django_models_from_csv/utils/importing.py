from import_export.resources import (
    # modelresource_factory,
    ModelResource, ModelDeclarativeMetaclass,
)
from tablib import Dataset

from django_models_from_csv import models
from django_models_from_csv.utils.csv import fetch_csv


def modelresource_factory(model, resource_class=ModelResource, extra_attrs=None):
    """
    Factory for creating ``ModelResource`` class for given Django model.
    """
    attrs = {'model': model}
    if extra_attrs:
        attrs.update(extra_attrs)

    Meta = type(str('Meta'), (object,), attrs)

    class_name = model.__name__ + str('Resource')

    class_attrs = {
        'Meta': Meta,
    }

    metaclass = ModelDeclarativeMetaclass
    return metaclass(class_name, (resource_class,), class_attrs)


def import_records_list(csv, dynmodel):
    """
    Take a fetched CSV and turn it into a tablib Dataset, with
    a row ID column and all headers translated to model field names.
    """
    data = Dataset().load(csv)
    data.insert_col(0, col=[i+1 for i in range(len(data))], header='id')
    # Turn our CSV columns into model columns
    for i in range(len(data.headers)):
        header = data.headers[i]
        model_header = dynmodel.csv_header_to_model_header(header)
        if model_header and header != model_header:
            data.headers[i] = model_header
    return data


def import_records(csv, Model, dynmodel):
    """
    Take a fetched CSV, parse it into user rows for
    insertion and attempt to import the data into the
    specified model.

    This performs a pre-import routine which will return
    failure information we can display and let the user fix
    the dynmodel before trying again. On success this function
    returns None.

    TODO: Only show N number of errors. If there are more,
    tell the user more errors have been supressed and to
    fix the ones listed before continuing. We don't want
    to overwhelm the user with error messages.
    """
    attrs = {
        "fields": ("id", "timestamp",)
    }
    resource = modelresource_factory(model=Model, extra_attrs=attrs)()
    # import IPython; IPython.embed(); import time; time.sleep(2)
    dataset = import_records_list(csv, dynmodel)
    result = resource.import_data(dataset, dry_run=True)
    # TODO: transform errors to something readable
    if result.has_errors():
        errors = result.row_errors()
        return errors
    result = resource.import_data(dataset, dry_run=False)
    if result.has_errors():
        errors = result.row_errors()
        return errors
